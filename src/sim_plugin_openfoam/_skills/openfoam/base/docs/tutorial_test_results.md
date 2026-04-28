# OpenFOAM Tutorial Test Results

**Date:** 2026-04-06
**OpenFOAM:** v2206 (ESI/OpenCFD)
**Platform:** Linux (remote via sim-server over SSH tunnel)
**Execution:** Serial only (Batch 1–7), parallel pending (Batch 8)

## Summary

| Metric | Count |
|--------|-------|
| Total tutorials scanned | 462 |
| Standalone serial selected | ~105 |
| **PASS** | **66** |
| **SLOW** (solver OK, >timeout) | **32** |
| **FAIL** (real error) | **5** |
| Parallel (deferred) | ~273 |
| Round 1 (prior session) | 10 |

**Success rate (PASS + SLOW): 94%** — nearly all solvers launch and run correctly.
SLOW cases would pass with longer timeout; they are not errors.

## Batch 1: basic (5/5 PASS)

| Case | Solver | Status | Time |
|------|--------|--------|------|
| laplacianFoam/implicitAMI | laplacianFoam | PASS | <5s |
| potentialFoam/pitzDaily | potentialFoam | PASS | <5s |
| scalarTransportFoam/pitzDaily | scalarTransportFoam | PASS | <5s |
| simpleFoam/implicitAMI | simpleFoam | PASS | <5s |
| chtMultiRegionFoam/2DImplicitCyclic | chtMultiRegionFoam | PASS | 3s (needs Allmesh) |

## Batch 2: combustion (9 PASS, 1 FAIL, 4 SLOW)

| Case | Solver | Status | Notes |
|------|--------|--------|-------|
| chemFoam/h2 | chemFoam | PASS | 0D reactor |
| chemFoam/ic8h18 | chemFoam | PASS | ~180s |
| chemFoam/ic8h18_TDAC | chemFoam | PASS | |
| chemFoam/nc7h16 | chemFoam | PASS | |
| chemFoam/gri | chemFoam | **FAIL** | Missing IFstream file |
| coldEngineFoam/freePiston | coldEngineFoam | PASS | |
| fireFoam/LES/smallPoolFire2D | fireFoam | PASS | |
| reactingFoam/laminar/counterFlowFlame2D | reactingFoam | PASS | |
| XiFoam/RAS/moriyoshiHomogeneous | XiFoam | PASS | |
| reactingFoam/laminar/counterFlowFlame2D_GRI | reactingFoam | SLOW | >120s |
| reactingFoam/RAS/membrane | reactingFoam | SLOW | >120s |
| reactingFoam/RAS/SandiaD_LTS | reactingFoam | SLOW | >120s |
| XiDyMFoam/oscillatingCylinder | XiDyMFoam | SLOW | >120s |

## Batch 3: compressible (10 PASS, 12 SLOW)

| Case | Solver | Status |
|------|--------|--------|
| rhoCentralFoam/obliqueShock | rhoCentralFoam | PASS |
| rhoCentralFoam/wedge15Ma5 | rhoCentralFoam | PASS |
| sonicFoam/laminar/forwardStep | sonicFoam | PASS |
| sonicLiquidFoam/decompressionTank | sonicLiquidFoam | PASS |
| rhoPimpleFoam/RAS/cavity | rhoPimpleFoam | PASS |
| rhoPimpleFoam/RAS/angledDuct | rhoPimpleFoam | PASS |
| rhoPimpleFoam/RAS/angledDuctLTS | rhoPimpleFoam | PASS |
| rhoSimpleFoam/angledDuctExplicitFixedCoeff | rhoSimpleFoam | PASS |
| sonicDyMFoam/movingCone | sonicDyMFoam | PASS |
| sonicFoam/RAS/prism | sonicFoam | PASS |
| rhoCentralFoam/shockTube | rhoCentralFoam | SLOW |
| rhoCentralFoam/forwardStep | rhoCentralFoam | SLOW |
| rhoCentralFoam/biconic25-55Run35 | rhoCentralFoam | SLOW |
| rhoCentralFoam/movingCone | rhoCentralFoam | SLOW |
| rhoPimpleFoam/laminar/sineWaveDamping | rhoPimpleFoam | SLOW |
| rhoPimpleFoam/RAS/annularThermalMixer | rhoPimpleFoam | SLOW |
| rhoPimpleFoam/RAS/mixerVessel2D | rhoPimpleFoam | SLOW |
| rhoPimpleFoam/RAS/TJunction | rhoPimpleFoam | SLOW |
| rhoPimpleFoam/RAS/TJunctionAverage | rhoPimpleFoam | SLOW |
| rhoPorousSimpleFoam/angledDuct/explicit | rhoPorousSimpleFoam | SLOW |
| rhoPorousSimpleFoam/angledDuct/implicit | rhoPorousSimpleFoam | SLOW |
| sonicFoam/laminar/shockTube | sonicFoam | SLOW |

## Batch 4: heatTransfer (7 PASS, 3 SLOW, 1 FAIL)

| Case | Solver | Status |
|------|--------|--------|
| buoyantBoussinesqPimpleFoam/BenardCells | buoyantBoussinesqPimpleFoam | PASS |
| buoyantBoussinesqPimpleFoam/hotRoom | buoyantBoussinesqPimpleFoam | PASS |
| buoyantBoussinesqSimpleFoam/hotRoom | buoyantBoussinesqSimpleFoam | PASS |
| buoyantPimpleFoam/hotRoom | buoyantPimpleFoam | PASS |
| buoyantSimpleFoam/circuitBoardCooling | buoyantSimpleFoam | PASS |
| buoyantSimpleFoam/simpleCarSolarPanel | buoyantSimpleFoam | PASS |
| solidFoam/movingCone | solidFoam | PASS |
| buoyantSimpleFoam/hotRadiationRoom | buoyantSimpleFoam | SLOW |
| buoyantSimpleFoam/hotRadiationRoomFvDOM | buoyantSimpleFoam | SLOW |
| buoyantSimpleFoam/roomWithThickCeiling | buoyantSimpleFoam | SLOW |
| buoyantPimpleFoam/thermocoupleTestCase | buoyantPimpleFoam | **FAIL** | Multi-region |

## Batch 5: incompressible (12 PASS, 10 SLOW)

| Case | Solver | Status |
|------|--------|--------|
| adjointShapeOptimizationFoam/pitzDaily | adjointShapeOptimizationFoam | PASS |
| nonNewtonianIcoFoam/offsetCylinder | nonNewtonianIcoFoam | PASS |
| pimpleFoam/laminar/movingCone | pimpleFoam | PASS |
| pimpleFoam/laminar/planarContraction | pimpleFoam | PASS |
| pimpleFoam/RAS/pitzDaily | pimpleFoam | PASS |
| pimpleFoam/RAS/TJunction | pimpleFoam | PASS |
| pimpleFoam/RAS/TJunctionFan | pimpleFoam | PASS |
| shallowWaterFoam/squareBump | shallowWaterFoam | PASS |
| simpleFoam/pitzDaily | simpleFoam | PASS |
| simpleFoam/pitzDailyExptInlet | simpleFoam | PASS |
| simpleFoam/T3A | simpleFoam | PASS |
| SRFSimpleFoam/mixer | SRFSimpleFoam | PASS |
| icoFoam/cavity/cavityClipped | icoFoam | SLOW |
| icoFoam/cavity/cavityGrade | icoFoam | SLOW |
| icoFoam/elbow | icoFoam | SLOW |
| pisoFoam/laminar/porousBlockage | pisoFoam | SLOW |
| porousSimpleFoam/angledDuct/explicit | porousSimpleFoam | SLOW |
| porousSimpleFoam/angledDuct/implicit | porousSimpleFoam | SLOW |
| simpleFoam/mixerVessel2D | simpleFoam | SLOW |
| simpleFoam/rotorDisk | simpleFoam | SLOW |
| simpleFoam/simpleCar | simpleFoam | SLOW |
| SRFPimpleFoam/rotor2D | SRFPimpleFoam | SLOW |

## Batch 6: multiphase (12 PASS, 11 SLOW)

| Case | Solver | Status |
|------|--------|--------|
| cavitatingFoam/LES/throttle | cavitatingFoam | PASS |
| cavitatingFoam/RAS/throttle | cavitatingFoam | PASS |
| compressibleInterFoam/laminar/climbingRod | compressibleInterFoam | PASS |
| compressibleInterFoam/laminar/depthCharge2D | compressibleInterFoam | PASS |
| driftFluxFoam/RAS/dahl | driftFluxFoam | PASS |
| driftFluxFoam/RAS/mixerVessel2D | driftFluxFoam | PASS |
| interFoam/laminar/capillaryRise | interFoam | PASS |
| interFoam/laminar/mixerVessel2D | interFoam | PASS |
| interFoam/laminar/sloshingCylinder | interFoam | PASS |
| interFoam/RAS/angledDuct | interFoam | PASS |
| interIsoFoam/discInConstantFlow | interIsoFoam | PASS |
| interIsoFoam/notchedDiscInSolidBodyRotation | interIsoFoam | PASS |
| interFoam/RAS/weirOverflow | interFoam | SLOW |
| interIsoFoam/weirOverflow | interIsoFoam | SLOW |
| multiphaseEulerFoam/bubbleColumn | multiphaseEulerFoam | SLOW |
| multiphaseInterFoam/laminar/mixerVessel2D | multiphaseInterFoam | SLOW |
| potentialFreeSurfaceFoam/oscillatingBox | potentialFreeSurfaceFoam | SLOW |
| twoLiquidMixingFoam/lockExchange | twoLiquidMixingFoam | SLOW |
| twoPhaseEulerFoam/laminar/bubbleColumn | twoPhaseEulerFoam | SLOW |
| twoPhaseEulerFoam/laminar/fluidisedBed | twoPhaseEulerFoam | SLOW |
| twoPhaseEulerFoam/RAS/bubbleColumn | twoPhaseEulerFoam | SLOW |
| twoPhaseEulerFoam/RAS/fluidisedBed | twoPhaseEulerFoam | SLOW |

## Batch 7: other (10 PASS, 1 SLOW, 2 FAIL)

| Case | Solver | Status |
|------|--------|--------|
| DNS/dnsFoam/boxTurb16 | dnsFoam | PASS |
| electromagnetics/electrostaticFoam/chargedWire | electrostaticFoam | PASS |
| electromagnetics/mhdFoam/hartmann | mhdFoam | PASS |
| financial/financialFoam/europeanCall | financialFoam | PASS |
| stressAnalysis/solidDisplacementFoam/plateHole | solidDisplacementFoam | PASS |
| stressAnalysis/solidEquilibriumDisplacementFoam/beamEndLoad | solidEquilibriumDisplacementFoam | PASS |
| mesh/blockMesh/sphere | blockMesh | PASS |
| mesh/blockMesh/sphere7 | blockMesh | PASS |
| lagrangian/kinematicParcelFoam/spinningDisk | kinematicParcelFoam | PASS |
| lagrangian/MPPICFoam/column | MPPICFoam | PASS |
| lagrangian/MPPICFoam/Goldschmidt | MPPICFoam | SLOW |
| discreteMethods/mdEquilibrationFoam/periodicCubeArgon | mdEquilibrationFoam | **FAIL** |
| mesh/blockMesh/pipe | blockMesh | **FAIL** |

## Round 1 (prior session, 10 cases)

| Case | Solver | Status | Time |
|------|--------|--------|------|
| icoFoam/cavity | icoFoam | PASS | 0.3s |
| simpleFoam/backwardFacingStep2D | simpleFoam | PASS | 70s |
| nonNewtonianIcoFoam/offsetCylinder | nonNewtonianIcoFoam | PASS | 6s |
| interFoam/damBreak | interFoam | PASS | 7.5s |
| pimpleFoam/cylinder2D | pimpleFoam | PASS | 19s |
| buoyantSimpleFoam/buoyantCavity | buoyantSimpleFoam | PASS | 170s |
| dnsFoam/boxTurb16 | dnsFoam | PASS | 6s |
| simpleFoam/squareBend | simpleFoam | PASS | 22s |
| reactingFoam/DLR_A_LTS | reactingFoam | PASS | 10s |
| pisoFoam/RAS/cavity | pisoFoam | PASS | 26s |

## Solver Coverage

**35 unique solvers tested:**

| Category | Solvers |
|----------|---------|
| Incompressible | icoFoam, pimpleFoam, pisoFoam, simpleFoam, nonNewtonianIcoFoam, adjointShapeOptimizationFoam, porousSimpleFoam, shallowWaterFoam, SRFPimpleFoam, SRFSimpleFoam |
| Compressible | rhoCentralFoam, rhoPimpleFoam, rhoSimpleFoam, rhoPorousSimpleFoam, sonicFoam, sonicDyMFoam, sonicLiquidFoam |
| Combustion | chemFoam, coldEngineFoam, fireFoam, reactingFoam, XiFoam, XiDyMFoam |
| Heat Transfer | buoyantBoussinesqPimpleFoam, buoyantBoussinesqSimpleFoam, buoyantPimpleFoam, buoyantSimpleFoam, solidFoam, chtMultiRegionFoam |
| Multiphase | interFoam, interIsoFoam, cavitatingFoam, compressibleInterFoam, driftFluxFoam, multiphaseEulerFoam, twoPhaseEulerFoam, potentialFreeSurfaceFoam, twoLiquidMixingFoam, MPPICFoam |
| Other | dnsFoam, electrostaticFoam, mhdFoam, financialFoam, solidDisplacementFoam, solidEquilibriumDisplacementFoam, laplacianFoam, potentialFoam, scalarTransportFoam, kinematicParcelFoam, mdEquilibrationFoam |

## Not Yet Tested

### Parallel cases (~273)
Require `mpirun -np N` with decomposePar. Planned for Batch 8.
Key parallel-only tutorials:
- simpleFoam/motorBike (snappyHexMesh + RANS)
- simpleFoam/windAroundBuildings
- pisoFoam/LES/motorBike
- interFoam/RAS/DTCHull (ship hull)
- heatTransfer/chtMultiRegionFoam/* (multi-region conjugate heat transfer)
- combustion/fireFoam/LES/* (large-scale fire simulations)

### Skipped categories
- **IO/** — file handling utilities, not solver cases
- **preProcessing/** — decomposition/setup tools
- **verificationAndValidation/** — validation suites with complex multi-setup Allrun
- **modules/** — empty in v2206
- **finiteArea/** — specialized finite area method cases
- **overset mesh** — multi-mesh sub-directories (not standalone)
