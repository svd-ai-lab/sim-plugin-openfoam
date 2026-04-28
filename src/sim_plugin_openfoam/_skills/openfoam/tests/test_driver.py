"""Tests for OpenFOAM driver — unit tests (no server needed) + integration."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sim.drivers.openfoam.driver import OpenFOAMDriver

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

class TestDetect:
    def setup_method(self):
        self.drv = OpenFOAMDriver()

    def test_detect_foam_file(self):
        assert self.drv.detect(FIXTURES / "empty.foam") is True

    def test_detect_python_with_openfoam_comment(self):
        assert self.drv.detect(FIXTURES / "hello_foam.py") is True

    def test_detect_shell_with_shebang(self):
        assert self.drv.detect(FIXTURES / "cavity_setup.sh") is True

    def test_detect_unrelated_file(self, tmp_path):
        f = tmp_path / "plain.py"
        f.write_text("x = 1\n")
        assert self.drv.detect(f) is False

    def test_detect_missing_file(self, tmp_path):
        assert self.drv.detect(tmp_path / "nonexistent.py") is False


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------

class TestLint:
    def setup_method(self):
        self.drv = OpenFOAMDriver()

    def test_lint_foam_marker(self):
        result = self.drv.lint(FIXTURES / "empty.foam")
        assert result.ok is True

    def test_lint_valid_python(self):
        result = self.drv.lint(FIXTURES / "hello_foam.py")
        assert result.ok is True

    def test_lint_valid_shell(self):
        result = self.drv.lint(FIXTURES / "cavity_setup.sh")
        assert result.ok is True

    def test_lint_bad_python(self, tmp_path):
        f = tmp_path / "bad.py"
        f.write_text("def foo(\n")
        result = self.drv.lint(f)
        assert result.ok is False
        assert any("Syntax error" in d.message for d in result.diagnostics)

    def test_lint_empty_shell(self, tmp_path):
        f = tmp_path / "empty.sh"
        f.write_text("")
        result = self.drv.lint(f)
        assert result.ok is False

    def test_lint_unsupported_ext(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        result = self.drv.lint(f)
        assert result.ok is False


# ---------------------------------------------------------------------------
# Connect (no remote host configured)
# ---------------------------------------------------------------------------

class TestConnect:
    def test_connect_not_configured(self):
        drv = OpenFOAMDriver()
        info = drv.connect()
        assert info.status == "not_configured"
        assert info.solver == "openfoam"


# ---------------------------------------------------------------------------
# Parse output
# ---------------------------------------------------------------------------

class TestParseOutput:
    def setup_method(self):
        self.drv = OpenFOAMDriver()

    def test_parse_json_last_line(self):
        stdout = 'some log\n{"cells": 1000, "ok": true}\n'
        result = self.drv.parse_output(stdout)
        assert result == {"cells": 1000, "ok": True}

    def test_parse_no_json(self):
        assert self.drv.parse_output("no json here\n") == {}

    def test_parse_multiple_json_takes_last(self):
        stdout = '{"a": 1}\nlog line\n{"b": 2}\n'
        result = self.drv.parse_output(stdout)
        assert result == {"b": 2}


# ---------------------------------------------------------------------------
# Remote session (mocked httpx)
# ---------------------------------------------------------------------------

class TestRemoteSession:
    """Test launch/run/query/disconnect with mocked HTTP."""

    def setup_method(self):
        self.drv = OpenFOAMDriver()

    def _mock_response(self, status_code=200, json_data=None):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data or {}
        resp.text = json.dumps(json_data or {})
        return resp

    def test_launch_success(self):
        drv = self.drv
        mock_client = MagicMock()
        mock_client.post.return_value = self._mock_response(200, {
            "ok": True,
            "data": {"session_id": "abc-123", "solver": "openfoam"},
        })

        with patch("httpx.Client", return_value=mock_client):
            result = drv.launch("testhost", 7600)

        assert result["ok"] is True
        assert drv._session_id == "abc-123"
        assert drv.is_connected is True

    def test_launch_already_active(self):
        drv = self.drv
        drv._session_id = "existing"
        with pytest.raises(RuntimeError, match="already active"):
            drv.launch("testhost", 7600)

    def test_launch_unreachable(self):
        import httpx as _httpx
        mock_client = MagicMock()
        mock_client.post.side_effect = _httpx.ConnectError("refused")

        with patch("httpx.Client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Cannot reach"):
                self.drv.launch("badhost", 9999)

    def test_run_not_connected(self):
        with pytest.raises(RuntimeError, match="Not connected"):
            self.drv.run("#!openfoam\nblockMesh")

    def test_run_success(self):
        drv = self.drv
        drv._host = "h"
        drv._port = 7600
        drv._client = MagicMock()
        drv._client.post.return_value = self._mock_response(200, {
            "data": {"ok": True, "label": "mesh", "stdout": "Mesh OK\n"},
        })

        result = drv.run("#!openfoam\nblockMesh", label="mesh")
        assert result["ok"] is True
        assert "Mesh OK" in result["stdout"]

    def test_run_failure(self):
        drv = self.drv
        drv._host = "h"
        drv._port = 7600
        drv._client = MagicMock()
        drv._client.post.return_value = self._mock_response(500, {
            "detail": "solver crashed",
        })

        result = drv.run("#!openfoam\nbadcmd", label="fail")
        assert result["ok"] is False

    def test_query(self):
        drv = self.drv
        drv._host = "h"
        drv._port = 7600
        drv._client = MagicMock()
        drv._client.get.return_value = self._mock_response(200, {
            "data": {"session_id": "abc", "solver": "openfoam"},
        })

        result = drv.query("session.summary")
        assert result["solver"] == "openfoam"

    def test_disconnect(self):
        drv = self.drv
        drv._host = "h"
        drv._port = 7600
        drv._session_id = "abc"
        drv._client = MagicMock()
        drv._client.post.return_value = self._mock_response(200, {
            "ok": True, "data": {"session_id": "abc"},
        })

        result = drv.disconnect()
        assert drv.is_connected is False
        assert drv._client is None

    def test_ps_not_connected(self):
        result = self.drv.ps()
        assert result["connected"] is False


# ---------------------------------------------------------------------------
# Integration tests (require real sim-server)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestRemoteIntegration:
    """Real integration tests — require sim-server at SIM_SERVER_HOST:7600."""

    HOST = "localhost"
    PORT = 7600

    def setup_method(self):
        self.drv = OpenFOAMDriver()

    def test_launch_and_ps(self):
        self.drv.launch(self.HOST, self.PORT)
        assert self.drv.is_connected
        ps = self.drv.ps()
        assert ps.get("connected") or "session_id" in ps.get("data", ps)
        self.drv.disconnect()

    def test_run_shell_command(self):
        self.drv.launch(self.HOST, self.PORT)
        result = self.drv.run("#!openfoam\necho 'hello from openfoam'", label="echo-test")
        assert result.get("ok") is True
        self.drv.disconnect()

    def test_cavity_tutorial(self):
        """Run the lid-driven cavity tutorial end-to-end."""
        self.drv.launch(self.HOST, self.PORT, timeout=600.0)
        code = """#!openfoam
cd /tmp && rm -rf cavity_test
cp -r $FOAM_TUTORIALS/incompressible/icoFoam/cavity/cavity cavity_test
cd cavity_test
blockMesh 2>&1
icoFoam 2>&1
echo '{"ok": true, "tutorial": "cavity"}'
"""
        result = self.drv.run(code, label="cavity-tutorial")
        assert result.get("ok") is True
        self.drv.disconnect()
