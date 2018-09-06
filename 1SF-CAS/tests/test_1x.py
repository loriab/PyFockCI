import sys, os
import psi4
sys.path.insert(1, '../')
import spinflip
from spinflip import sf_cas as sf_cas_ref
import cis
from cis import do_sf_cas

# threshold for value equality
threshold = 1e-7
# setting up molecule
n2 = psi4.core.Molecule.create_molecule_from_string("""
0 7
N 0 0 0
N 0 0 2.5
symmetry c1
""")
o2 = psi4.core.Molecule.create_molecule_from_string("""
0 3
O
O 1 1.2
symmetry c1
""")

# Test: 1SF-CAS
def test_1():
    options = {"basis": "cc-pvdz", 'num_roots': 4, 'diis_start': 20, 'e_convergence': 1e-10, 'd_convergence': 1e-10}
    expected = sf_cas_ref( 0, 5, n2, conf_space="", add_opts=options )
    e = do_sf_cas( 0, 5, n2, conf_space="", add_opts=options )
    assert abs(e - expected) < threshold

def test_2():
    options = {"basis": "cc-pvdz", 'e_convergence': 1e-10, 'd_convergence': 1e-10, 'diag_method': 'rsp'}
    expected = sf_cas_ref( 0, 1, o2, conf_space="", add_opts=options )
    e = do_sf_cas( 0, 1, o2, conf_space="", add_opts=options, num_roots=2 )
    assert abs(e - expected) < threshold
