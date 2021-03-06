"""
Fock-space CI using Psi4's interface.

Runs a RAS-nSF-IP/EA calculation using Psi4 to construct the integrals.
"""

# importing general python functionality
from __future__ import print_function
import time
import math

# importing necessary packages
import numpy as np
import psi4

# importing our packages
from .f import get_F
from .tei import *
from .np_sf import do_sf_np

def do_sf_psi4(delta_a, delta_b, mol, conf_space="", ref_opts={}, sf_opts={}):
    """
    Runs RAS-nSF-IP/EA using Psi4.

    This runs a RAS-nSF-IP/EA calculation using Psi4 to solve for the 
    reference state ROHF orbitals, if needed, and construct the one- and 
    two-electron integral objects to pass along to the NumPy-based solver.

    Parameters
    ----------
    delta_a : int
        Number of alpha electrons to eliminate
    delta_b : int
        Number of beta electrons to create
    mol : Psi4.core.Molecule
        Psi4 Molecule object on which to run the calculation
    conf_space : str
        Inclusion of holes/particles (Options: "", "h", "p", "h,p")
    ref_opts : dict
        Additional options for Psi4 (see Psi4 docs)
    sf_opts : dict
        Additional options for Fock CI

    Returns
    -------
    A FockWfn object containing calculation results
    """
    start_time = time.time()
    # cleanup in case of multiple calculations
    psi4.core.clean()
    psi4.core.clean_options()
    psi4.core.clean_variables()

    # setting default options, reading in additional options from user
    psi4_opts = {'BASIS': 'cc-pvdz',
                 'scf_type': 'direct',
                 'guess': 'gwh',
                 'e_convergence': 1e-10,
                 'd_convergence': 1e-10,
                 'reference': 'rohf'}
    psi4_opts.update(ref_opts)
    psi4.set_options(psi4_opts)
    # run ROHF
    if(sf_opts['READ_PSI4_WFN']):
        wfn = sf_opts['PSI4_WFN']
        e = wfn.energy()
    else:
        e, wfn = psi4.energy('scf', molecule=mol, return_wfn=True)
    print("Reference Energy: ", e)
    # obtain RAS spaces
    ras1 = wfn.doccpi()[0]
    ras2 = wfn.soccpi()[0]
    ras3 = wfn.basisset().nbf() - (ras1 + ras2)
    # get Fock and MO coefficients
    Ca = psi4.core.Matrix.to_array(wfn.Ca())
    Cb = psi4.core.Matrix.to_array(wfn.Cb())
    # freeze core/virt if needed
    frozen_core = sf_opts['FROZEN_CORE']
    frozen_virt = sf_opts['FROZEN_VIRT']
    print("FROZEN CORE", frozen_core)
    print("FROZEN VIRT", frozen_virt)
    if(frozen_core != 0):
        Ca = Ca[:, frozen_core:]
        Cb = Cb[:, frozen_core:]
        ras1 = ras1 - frozen_core
        print(Ca.shape)
    if(frozen_virt != 0):
        Ca = Ca[:, :-frozen_virt]
        Cb = Cb[:, :-frozen_virt]
        ras3 = ras3 - frozen_virt
        print(Ca.shape)
    wfn.Ca().copy(psi4.core.Matrix.from_array(Ca))
    wfn.Cb().copy(psi4.core.Matrix.from_array(Cb))
    Fa, Fb = get_F(wfn)
    print(Fa.shape)
    # get two-electron integrals
    if(sf_opts['INTEGRAL_TYPE']=="FULL"):
        tei_int = TEIFullPsi4(wfn.Ca(), wfn.basisset(), ras1, ras2, ras3,
                              conf_space)
    if(sf_opts['INTEGRAL_TYPE']=="DF"):
        # if user hasn't defined which aux basis to use, default behavior
        # is to use the one from Psi4 wfn
        if(sf_opts['AUX_BASIS_NAME'] == ""):
            aux_basis_name = psi4.qcdb.basislist.corresponding_basis(
                                 wfn.basisset().name(), role=sf_opts['DF_ROLE'])[0]
        else:
            aux_basis_name = sf_opts['AUX_BASIS_NAME']
        aux_basis = psi4.core.BasisSet.build(mol, "DF_BASIS_SCF", "", 
                                             sf_opts['DF_ROLE'], aux_basis_name)
        tei_int = TEIDFPsi4(wfn.Ca(), wfn.basisset(), aux_basis, ras1, ras2,
                            ras3, conf_space)
    out = do_sf_np(delta_a, delta_b, ras1, ras2, ras3, Fa, Fb, tei_int, e,
                   conf_space=conf_space, sf_opts=sf_opts)
    # write Psi4 wavefunction to output object
    out.wfn = wfn
    print("Total Psi4 walltime: %3.5f seconds." %(time.time() - start_time) )
    return out

