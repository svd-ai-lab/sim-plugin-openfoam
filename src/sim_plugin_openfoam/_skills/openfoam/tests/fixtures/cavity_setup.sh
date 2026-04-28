#!openfoam
# Lid-driven cavity tutorial setup
cp -r $FOAM_TUTORIALS/incompressible/icoFoam/cavity/cavity ./cavity
cd cavity
blockMesh
icoFoam
