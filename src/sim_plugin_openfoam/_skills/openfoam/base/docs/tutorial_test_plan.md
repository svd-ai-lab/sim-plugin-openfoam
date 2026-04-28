# OpenFOAM Tutorial Reproduction Plan

## Overview

- **Total tutorials with controlDict:** 462
- **Standalone serial cases (no parallel):** ~190 (after filtering sub-components)
- **Parallel cases (has decomposeParDict):** ~273
- **Already completed (Round 1):** 10

## Execution Strategy

1. **Serial first** — run all standalone serial cases (no mpirun needed)
2. **Parallel second** — run parallel cases with `mpirun -np N` (max 100 cores)
3. **Skip** — multiWorld, overset sub-meshes, multi-region sub-dirs (not standalone)

## Batches

### Batch 1: basic (serial) — 5 cases
| # | Case | Solver | Status |
|---|------|--------|--------|
| 1 | basic/laplacianFoam/implicitAMI | laplacianFoam | pending |
| 2 | basic/potentialFoam/pitzDaily | potentialFoam | pending |
| 3 | basic/scalarTransportFoam/pitzDaily | scalarTransportFoam | pending |
| 4 | basic/simpleFoam/implicitAMI | simpleFoam | pending |
| 5 | basic/chtMultiRegionFoam/2DImplicitCyclic | chtMultiRegionFoam | pending |

### Batch 2: combustion (serial) — 14 cases
| # | Case | Solver | Status |
|---|------|--------|--------|
| 6 | combustion/chemFoam/gri | chemFoam | pending |
| 7 | combustion/chemFoam/h2 | chemFoam | pending |
| 8 | combustion/chemFoam/ic8h18 | chemFoam | pending |
| 9 | combustion/chemFoam/ic8h18_TDAC | chemFoam | pending |
| 10 | combustion/chemFoam/nc7h16 | chemFoam | pending |
| 11 | combustion/coldEngineFoam/freePiston | coldEngineFoam | pending |
| 12 | combustion/fireFoam/LES/flameSpreadWaterSuppressionPanel | fireFoam | pending |
| 13 | combustion/fireFoam/LES/simplePMMApanel | fireFoam | pending |
| 14 | combustion/fireFoam/LES/smallPoolFire2D | fireFoam | pending |
| 15 | combustion/PDRFoam/pipeLattice | PDRFoam | pending |
| 16 | combustion/reactingFoam/laminar/counterFlowFlame2D | reactingFoam | pending |
| 17 | combustion/reactingFoam/laminar/counterFlowFlame2D_GRI | reactingFoam | pending |
| 18 | combustion/reactingFoam/RAS/membrane | reactingFoam | pending |
| 19 | combustion/reactingFoam/RAS/SandiaD_LTS | reactingFoam | pending |

### Batch 3: compressible (serial) — 21 cases
| # | Case | Solver | Status |
|---|------|--------|--------|
| 20 | compressible/rhoCentralFoam/biconic25-55Run35 | rhoCentralFoam | pending |
| 21 | compressible/rhoCentralFoam/forwardStep | rhoCentralFoam | pending |
| 22 | compressible/rhoCentralFoam/movingCone | rhoCentralFoam | pending |
| 23 | compressible/rhoCentralFoam/obliqueShock | rhoCentralFoam | pending |
| 24 | compressible/rhoCentralFoam/shockTube | rhoCentralFoam | pending |
| 25 | compressible/rhoCentralFoam/wedge15Ma5 | rhoCentralFoam | pending |
| 26 | compressible/rhoPimpleFoam/laminar/sineWaveDamping | rhoPimpleFoam | pending |
| 27 | compressible/rhoPimpleFoam/RAS/angledDuct | rhoPimpleFoam | pending |
| 28 | compressible/rhoPimpleFoam/RAS/angledDuctLTS | rhoPimpleFoam | pending |
| 29 | compressible/rhoPimpleFoam/RAS/annularThermalMixer | rhoPimpleFoam | pending |
| 30 | compressible/rhoPimpleFoam/RAS/cavity | rhoPimpleFoam | pending |
| 31 | compressible/rhoPimpleFoam/RAS/mixerVessel2D | rhoPimpleFoam | pending |
| 32 | compressible/rhoPimpleFoam/RAS/TJunction | rhoPimpleFoam | pending |
| 33 | compressible/rhoPimpleFoam/RAS/TJunctionAverage | rhoPimpleFoam | pending |
| 34 | compressible/rhoPorousSimpleFoam/angledDuct/explicit | rhoPorousSimpleFoam | pending |
| 35 | compressible/rhoPorousSimpleFoam/angledDuct/implicit | rhoPorousSimpleFoam | pending |
| 36 | compressible/rhoSimpleFoam/angledDuctExplicitFixedCoeff | rhoSimpleFoam | pending |
| 37 | compressible/sonicDyMFoam/movingCone | sonicDyMFoam | pending |
| 38 | compressible/sonicFoam/laminar/forwardStep | sonicFoam | pending |
| 39 | compressible/sonicFoam/laminar/shockTube | sonicFoam | pending |
| 40 | compressible/sonicFoam/RAS/prism | sonicFoam | pending |
| 41 | compressible/sonicLiquidFoam/decompressionTank | sonicLiquidFoam | pending |

### Batch 4: heatTransfer (serial) — 12 cases
| # | Case | Solver | Status |
|---|------|--------|--------|
| 42 | heatTransfer/buoyantBoussinesqPimpleFoam/BenardCells | buoyantBoussinesqPimpleFoam | pending |
| 43 | heatTransfer/buoyantBoussinesqPimpleFoam/hotRoom | buoyantBoussinesqPimpleFoam | pending |
| 44 | heatTransfer/buoyantBoossinesqSimpleFoam/hotRoom | buoyantBoussinesqSimpleFoam | pending |
| 45 | heatTransfer/buoyantPimpleFoam/hotRoom | buoyantPimpleFoam | pending |
| 46 | heatTransfer/buoyantPimpleFoam/thermocoupleTestCase | buoyantPimpleFoam | pending |
| 47 | heatTransfer/buoyantSimpleFoam/circuitBoardCooling | buoyantSimpleFoam | pending |
| 48 | heatTransfer/buoyantSimpleFoam/hotRadiationRoom | buoyantSimpleFoam | pending |
| 49 | heatTransfer/buoyantSimpleFoam/hotRadiationRoomFvDOM | buoyantSimpleFoam | pending |
| 50 | heatTransfer/buoyantSimpleFoam/roomWithThickCeiling | buoyantSimpleFoam | pending |
| 51 | heatTransfer/buoyantSimpleFoam/simpleCarSolarPanel | buoyantSimpleFoam | pending |
| 52 | heatTransfer/solidFoam/movingCone | solidFoam | pending |

### Batch 5: incompressible (serial) — 30 cases
| # | Case | Solver | Status |
|---|------|--------|--------|
| 53 | incompressible/icoFoam/cavity/cavityClipped | icoFoam | pending |
| 54 | incompressible/icoFoam/cavity/cavityGrade | icoFoam | pending |
| 55 | incompressible/icoFoam/elbow | icoFoam | pending |
| 56 | incompressible/adjointShapeOptimizationFoam/pitzDaily | adjointShapeOptimizationFoam | pending |
| 57 | incompressible/pimpleFoam/laminar/filmPanel0 | pimpleFoam | pending |
| 58 | incompressible/pimpleFoam/laminar/movingCone | pimpleFoam | pending |
| 59 | incompressible/pimpleFoam/laminar/planarContraction | pimpleFoam | pending |
| 60 | incompressible/pimpleFoam/RAS/pitzDaily | pimpleFoam | pending |
| 61 | incompressible/pimpleFoam/RAS/TJunction | pimpleFoam | pending |
| 62 | incompressible/pimpleFoam/RAS/TJunctionFan | pimpleFoam | pending |
| 63 | incompressible/pisoFoam/laminar/porousBlockage | pisoFoam | pending |
| 64 | incompressible/porousSimpleFoam/angledDuct/explicit | porousSimpleFoam | pending |
| 65 | incompressible/porousSimpleFoam/angledDuct/implicit | porousSimpleFoam | pending |
| 66 | incompressible/shallowWaterFoam/squareBump | shallowWaterFoam | pending |
| 67 | incompressible/simpleFoam/mixerVessel2D | simpleFoam | pending |
| 68 | incompressible/simpleFoam/pitzDaily | simpleFoam | pending |
| 69 | incompressible/simpleFoam/pitzDailyExptInlet | simpleFoam | pending |
| 70 | incompressible/simpleFoam/rotorDisk | simpleFoam | pending |
| 71 | incompressible/simpleFoam/simpleCar | simpleFoam | pending |
| 72 | incompressible/simpleFoam/T3A | simpleFoam | pending |
| 73 | incompressible/SRFPimpleFoam/rotor2D | SRFPimpleFoam | pending |
| 74 | incompressible/SRFSimpleFoam/mixer | SRFSimpleFoam | pending |

### Batch 6: multiphase (serial) — 40 cases
(See full list in execution log)

### Batch 7: other categories (serial) — ~20 cases
DNS, electromagnetics, financial, discreteMethods, lagrangian, mesh, stressAnalysis, etc.

### Batch 8+: parallel cases — ~100 selected
(To be planned after serial batches complete)

## Status Legend

- **PASS** — ran to completion, solver converged or completed normally
- **FAIL** — solver crashed, mesh failed, or missing dependencies
- **SKIP** — not standalone, too expensive (>30min), or requires special setup
- **SLOW** — passed but took >5 minutes (may need endTime reduction)
- **pending** — not yet attempted

## Notes

- All cases run via: `sim-server /exec` with `#!openfoam` shebang
- SSH tunnel: Windows localhost:7600 → Linux localhost:8080
- Max parallel: `mpirun -np 100` (Linux machine limit)
- Long cases: reduce endTime via `sed` for quick validation
- Common fix: `cp -r 0.orig 0` before solver run
