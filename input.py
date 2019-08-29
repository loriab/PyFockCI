import os
import psi4
import numpy as np
import sf_ip_ea
from sf_ip_ea import fock_ci
import heisenberg
import numpy as np
import numpy.linalg as LIN

n2_7 = psi4.core.Molecule.create_molecule_from_string("""
0 5
H 0 0 0
H 2 0 0
H 0 2 0
H 2 2 0
symmetry c1
""")
"""
# 1.278
0 7
O 0.0 0.0 0.0
O 2.0 0.0 0.0
O 4.0 0.0 0.0
H 0 0 0
H 2 0 0
H 0 2 0
H 2 2 0
"""

options = {"BASIS": "6-31G*", 'e_convergence': 1e-12, 'd_convergence': 1e-4, 'scf_type': 'pk', 'guess': 'gwh', 'reference': 'rohf'}
sf_options = {'SF_DIAG_METHOD': 'LANCZOS', 'NUM_ROOTS': 4}

print("***** TEST: NO READ PSI WFN")
wfn = fock_ci( 1, 1, n2_7, conf_space="", ref_opts=options, sf_opts=sf_options)

"""
print("***** TEST: READ PSI WFN")
psi4.core.clean()

psi4.set_options(options)
e, rohf_wfn = psi4.energy('scf', molecule=n2_7, return_wfn=True)

sf_options.update({'READ_PSI4_WFN': True,
                   'PSI4_WFN': rohf_wfn})

wfn = fock_ci( 1, 1, n2_7, conf_space="", ref_opts=options, sf_opts=sf_options)
"""

np.set_printoptions(threshold=np.inf, linewidth=100000)
#J = bloch.do_bloch(wfn, 4)
J = bloch.do_bloch(wfn, 4)

print("J")
print(J*27.2114*1000)

heis = heisenberg.heis_ham()
heis.do_heisenberg([1,1,1,1], J)
heis.print_roots()


