import psi4
import sf_ip_ea
import pytest

# threshold for value equality
threshold = 1e-7
# setting up molecule
n2_7 = psi4.core.Molecule.from_string("""
0 7
N 0 0 0
N 0 0 2.5
symmetry c1
""")
n2_3 = psi4.core.Molecule.from_string("""
0 5
N 0 0 0
N 0 0 1.5
symmetry c1
""")
o2 = psi4.core.Molecule.from_string("""
0 3
O
O 1 1.2
symmetry c1
""")

# Test: 1SF-RAS(p)
@pytest.mark.methodtest
def test_1():
    psi4.core.clean()
    psi4.core.clean_options()
    psi4.core.clean_variables()
    expected = [-108.773240258070189, -108.766379708729545, -108.677933383504808, -108.671261012421127]
    options = {"basis": "cc-pvdz", 'num_roots': 4, 'diis_start': 20, 'e_convergence': 1e-10, 'd_convergence': 1e-10}
    wfn = sf_ip_ea.fock_ci( 1, 1, n2_7, conf_space="p", ref_opts=options, sf_opts={'NUM_ROOTS': 4} )
    for i, true in enumerate(wfn.e):
        assert abs(true - expected[i]) < threshold

@pytest.mark.methodtest
def test_2():
    psi4.core.clean()
    psi4.core.clean_options()
    psi4.core.clean_variables()
    expected = [-108.787240209836739, -108.729125830987144, -108.729125830987130, -108.711324264599156]
    options = {"basis": "cc-pvdz", 'num_roots': 4, 'diis_start': 20, 'e_convergence': 1e-10, 'd_convergence': 1e-10}
    wfn = sf_ip_ea.fock_ci( 1, 1, n2_3, conf_space="p", ref_opts=options, sf_opts={'NUM_ROOTS': 4} )
    for i, true in enumerate(wfn.e):
        assert abs(true - expected[i]) < threshold

@pytest.mark.methodtest
def test_3():
    psi4.core.clean()
    psi4.core.clean_options()
    psi4.core.clean_variables()
    expected = [-149.609461120738501, -149.562132340061027]
    options = {"basis": "cc-pvdz", 'e_convergence': 1e-10, 'd_convergence': 1e-10, 'diag_method': 'rsp'}
    wfn = sf_ip_ea.fock_ci( 1, 1, o2, conf_space="p", ref_opts=options, sf_opts={'NUM_ROOTS': 2, 'SF_DIAG_METHOD': 'LANCZOS'} )
    for i, true in enumerate(wfn.e):
        assert abs(true - expected[i]) < threshold
