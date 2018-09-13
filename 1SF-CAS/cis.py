from __future__ import print_function
import math
import numpy as np
from numpy import linalg as LIN
from scipy.sparse import linalg as SPLIN
from linop import LinOpH
import psi4

'''
Refs:
Crawford Tutorials (http://sirius.chem.vt.edu/wiki/doku.php?id=crawdad:programming:project12)
DePrince Tutorials (https://www.chem.fsu.edu/~deprince/programming_projects/cis/)
Sherrill Notes (http://vergil.chemistry.gatech.edu/notes/cis/cis.html)
'''

# Kronaker delta function.
def kdel(i, j):
    if(i==j):
        return 1
    else:
        return 0

# Generates the set of singles determinants (spin adapted).
# First row is i, second is a.
def generate_dets_sa(n_occ, n_virt):
    n_dets = n_occ * n_virt
    det_list = np.zeros((n_dets, 2)).astype(int)
    for i in range(n_occ):
        for a in range(n_virt):
            det_list[i*n_virt+a] = [i,n_occ+a]
    return det_list

# Generates the set of singly-excited determinants (spin unadapted).
# First row is orbital excited from, second row is the orbital excited into.
# Indexing treats alphas as the first "block" and betas as the second,
# regardless of which orbitals are virtual/occupied.
# Ground state not included.
def generate_dets(na_occ, na_virt, nb_occ, nb_virt):
    nbf = na_occ + na_virt
    n_dets = (na_occ + nb_occ) * (na_virt + nb_virt)
    det_list = np.zeros((n_dets, 2, 2)).astype(int)
    # fill out alpha -> ??
    for i in range(na_occ):
        # a -> a
        for a in range(na_virt):
            det_list[i*na_virt+a] = [[i,0], [na_occ+a,0]]
        # a -> b
        for a in range(nb_virt):
            det_list[i*nb_virt+a+(na_virt*na_occ)] = [[i,0], [nb_occ+a+nbf, 0]]
    # fill out beta -> ??
    for i in range(nb_occ):
        # b -> a
        for a in range(na_virt):
            det_list[i*na_virt+a+(na_occ*(na_virt+nb_virt))] = [[nbf+i, 0], [na_occ+a, 0]]
        # b -> b
        for a in range(nb_virt):
            det_list[i*nb_virt+a+(na_occ*(na_virt+nb_virt))+(nb_occ*na_virt)] = [[i+nbf, 0], [nb_occ+a+nbf, 0]]
    return det_list

# Generates the set of singly-excited SF determinants (spin unadapted, obviously).
def generate_sf_dets(na_occ, na_virt, nb_occ, nb_virt):
    nbf = na_occ + na_virt
    n_dets = (na_occ - nb_occ) * (na_occ - nb_occ)
    det_list = np.zeros((n_dets, 2, 2)).astype(int)
    for i in range(na_occ - nb_occ):
        for a in range(na_occ - nb_occ):
            det_list[i*(na_occ - nb_occ)+a] = [[nb_occ+i, 0], [nb_occ+a+nbf, 0]]
    return det_list

def generate_sf_p_dets(na_occ, na_virt, nb_occ, nb_virt):
    nbf = na_occ + na_virt
    socc = na_occ - nb_occ
    #det_list = np.zeros((n_dets, 2, 2)).astype(int)
    n_dets_singles = socc * nb_virt
    #print(n_dets_singles)
    n_dets_doubles = socc * na_virt * (math.factorial(socc)/(2*math.factorial(socc-2)))
    #print(n_dets_doubles)
    det_list = np.zeros((n_dets_singles + n_dets_doubles, 2, 2)).astype(int)
    index = 0
    # fill out singles
    for i in range(socc):
        # a -> b_virt (singles)
        for a in range(nb_virt):
            det_list[index] = [[nb_occ+i, 0], [nbf+nb_occ+a, 0]]
            index = index + 1
    # fill out doubles
    for a in range(na_virt):
        for b in range(socc):
            for i in range(socc):
                for j in range(i):
                    # i->a, j->b
                    if(not i==j):
                        det_list[index] = [[nb_occ+i, nb_occ+j], [na_occ+a, nbf+nb_occ+b]]
                        index = index + 1
                        #print(det_list)
                        #det_list[index] = [[nb_occ+i, nb_occ+j], [nbf+nb_occ+b, na_occ+a]]
                        #index = index + 1
                        #print(det_list)
    #print(det_list)
    return det_list

# Forms the CIS Hamiltonian (not spin adapted)
def get_sf_H(wfn, conf_space):
    # get necessary integrals/matrices from Psi4 (AO basis)
    # References: Psi4NumPy tutorials
    Ca = psi4.core.Matrix.to_array(wfn.Ca())
    Cb = psi4.core.Matrix.to_array(wfn.Cb())
    C = np.block([[Ca, np.zeros_like(Cb)],
                      [np.zeros_like(Ca), Cb]])
    # one-electron part
    Fa = psi4.core.Matrix.to_array(wfn.Fa(), copy=True)
    Fb = psi4.core.Matrix.to_array(wfn.Fb(), copy=True)
    F = np.block([[Fa, np.zeros_like(Fa)],
                  [np.zeros_like(Fb), Fb]])
    F = np.dot(C.T, np.dot(F, C))
    # two-electron part
    mints = psi4.core.MintsHelper(wfn.basisset())
    tei = psi4.core.Matrix.to_array(mints.ao_eri(), copy=True)
    I = np.eye(2)
    tei = np.kron(I, tei)
    tei = np.kron(I, tei.T)
    tei = tei.transpose(0, 2, 1, 3) - tei.transpose(0, 2, 3, 1)
    tei = np.einsum('pqrs,pa',tei,C)
    tei = np.einsum('aqrs,qb',tei,C)
    tei = np.einsum('abrs,rc',tei,C)
    tei = np.einsum('abcs,sd',tei,C)
    # Get determinant list (hole-particle format)
    a_occ = wfn.doccpi()[0] + wfn.soccpi()[0]
    b_occ = wfn.doccpi()[0]
    a_virt = wfn.basisset().nbf() - a_occ
    b_virt = wfn.basisset().nbf() - b_occ
    nbf = wfn.basisset().nbf()
    if(conf_space == ""):
        dets = generate_sf_dets(a_occ, a_virt, b_occ, b_virt)
    elif(conf_space == "p"):
        dets = generate_sf_p_dets(a_occ, a_virt, b_occ, b_virt)
    n_dets = dets.shape[0]
    # Build CIS Hamiltonian matrix
    H = np.zeros((n_dets, n_dets))
    for d1index, det1 in enumerate(dets):
        for d2index, det2 in enumerate(dets):
            # from 1st det (S + D)
            i1 = det1[0][0]
            j1 = det1[0][1]
            a1 = det1[1][0]
            b1 = det1[1][1]
            i2 = det2[0][0]
            j2 = det2[0][1]
            a2 = det2[1][0]
            b2 = det2[1][1]
            # first eliminated same
            if(i1 == i2):
                # all eliminated same
                if(j1 == j2):
                    # first added same
                    if(a1 == a2):
                        # all added same -> D0
                        if(b1 == b2): #OK
                            H[d1index, d2index] = F[a1, a2] - F[i1,i2] + tei[a1, i2, i1, a2]
                        # differ by b excited orbital -> D1
                        else:
                            H[d1index, d2index] = F[a1, a2] + F[b1, b2] + tei[a1, i2, i1, a2] + tei[b1, j2, j1, b2]
                    # differ by a excited orbital
                    else:
                        # differ by a only -> D1
                        if(b1 == b2): #OK
                            H[d1index, d2index] = F[a1, a2] + tei[a1, i2, i1, a2]
                        # differ by a+b excited orbital -> D2
                        else:
                            H[d1index, d2index] = tei[a1, i2, i1, a2] + tei[b1, j2, j1, b2]
                # differ in second elimination j
                else:
                    # first added same
                    if(a1 == a2):
                        # all added same -> D1
                        if(b1 == b2):
                            H[d1index, d2index] = - F[i1,i2] + tei[a1, i2, i1, a2] 
                        # differ by b excited orbital -> D2
                        else:
                            H[d1index, d2index] = tei[a1, i2, i1, a2]
                    # differ by a excited orbital
                    else:
                        # differ by a only -> D2
                        if(b1 == b2):
                            H[d1index, d2index] = tei[a1, i2, i1, a2]             
                        # differ by a+b excited orbital -> 0
            # differ in first elimination i
            else:
                # all eliminated same
                if(j1 == j2):
                    # first added same
                    if(a1 == a2):
                        # all added same -> D1
                        if(b1 == b2):
                            H[d1index, d2index] = - F[i1, i2] + tei[a1, i2, i1, a2] 
                        # differ by b excited orbital -> D2
                        else:
                            H[d1index, d2index] = tei[a1, i2, i1, a2] 
                    # differ by a excited orbital
                    else:
                        # differ by a only -> D2
                        if(b1 == b2):
                            H[d1index, d2index] = tei[a1, i2, i1, a2]             

                # differ in second elimination j
                else:
                    # first added same
                    if(a1 == a2):
                        # all added same -> D2
                        if(b1 == b2):
                            H[d1index, d2index] = tei[a1, i2, i1, a2]          
            #H[d1index, d2index] = F[a, b]*kdel(i,j) - F[i,j]*kdel(a,b) + tei[a, j, i, b]
    return (H, dets, F, tei)

def get_nsa_F(wfn):
    # get necessary integrals/matrices from Psi4 (AO basis)
    # References: Psi4NumPy tutorials
    Ca = psi4.core.Matrix.to_array(wfn.Ca())
    Cb = psi4.core.Matrix.to_array(wfn.Cb())
    C = np.block([[Ca, np.zeros_like(Cb)],
                      [np.zeros_like(Ca), Cb]])
    # one-electron part
    Fa = psi4.core.Matrix.to_array(wfn.Fa(), copy=True)
    Fb = psi4.core.Matrix.to_array(wfn.Fb(), copy=True)
    F = np.block([[Fa, np.zeros_like(Fa)],
                  [np.zeros_like(Fb), Fb]])
    F = np.dot(C.T, np.dot(F, C)) 
    return F

def get_nsa_tei(wfn):
    # get necessary integrals/matrices from Psi4 (AO basis)
    # References: Psi4NumPy tutorials
    Ca = psi4.core.Matrix.to_array(wfn.Ca())
    Cb = psi4.core.Matrix.to_array(wfn.Cb())
    C = np.block([[Ca, np.zeros_like(Cb)],
                      [np.zeros_like(Ca), Cb]])
    # two-electron part
    mints = psi4.core.MintsHelper(wfn.basisset())
    tei = psi4.core.Matrix.to_array(mints.ao_eri(), copy=True)
    I = np.eye(2)
    tei = np.kron(I, tei)
    tei = np.kron(I, tei.T)
    tei = tei.transpose(0, 2, 1, 3) - tei.transpose(0, 2, 3, 1)
    tei = np.einsum('pqrs,pa',tei,C)
    tei = np.einsum('aqrs,qb',tei,C)
    tei = np.einsum('abrs,rc',tei,C)
    tei = np.einsum('abcs,sd',tei,C)
    return tei

# Forms the CIS Hamiltonian (not spin adapted)
def get_cis_H(wfn):
    # get necessary integrals/matrices from Psi4 (AO basis)
    # References: Psi4NumPy tutorials
    Ca = psi4.core.Matrix.to_array(wfn.Ca())
    Cb = psi4.core.Matrix.to_array(wfn.Cb())
    C = np.block([[Ca, np.zeros_like(Cb)],
                      [np.zeros_like(Ca), Cb]])
    # one-electron part
    Fa = psi4.core.Matrix.to_array(wfn.Fa(), copy=True)
    Fb = psi4.core.Matrix.to_array(wfn.Fb(), copy=True)
    F = np.block([[Fa, np.zeros_like(Fa)],
                  [np.zeros_like(Fb), Fb]])
    F = np.dot(C.T, np.dot(F, C))
    # two-electron part
    mints = psi4.core.MintsHelper(wfn.basisset())
    tei = psi4.core.Matrix.to_array(mints.ao_eri(), copy=True)
    I = np.eye(2)
    tei = np.kron(I, tei)
    tei = np.kron(I, tei.T)
    tei = tei.transpose(0, 2, 1, 3) - tei.transpose(0, 2, 3, 1)
    tei = np.einsum('pqrs,pa',tei,C)
    tei = np.einsum('aqrs,qb',tei,C)
    tei = np.einsum('abrs,rc',tei,C)
    tei = np.einsum('abcs,sd',tei,C)
    # Get determinant list (hole-particle format)
    a_occ = wfn.doccpi()[0] + wfn.soccpi()[0]
    b_occ = wfn.doccpi()[0]
    a_virt = wfn.basisset().nbf() - a_occ
    b_virt = wfn.basisset().nbf() - b_occ
    na_dets = a_occ*a_virt
    nb_dets = b_occ*b_virt
    nbf = wfn.basisset().nbf()
    dets = generate_dets(a_occ, a_virt, b_occ, b_virt)
    n_dets = dets.shape[0]
    # Build CIS Hamiltonian matrix
    H = np.zeros((n_dets, n_dets))
    for d1index, det1 in enumerate(dets):
        for d2index, det2 in enumerate(dets):
            i = det1[0][0]
            a = det1[1][0]
            j = det2[0][0]
            b = det2[1][0]
            H[d1index, d2index] = F[a, b]*kdel(i,j) - F[i,j]*kdel(a,b) + tei[a, j, i, b]
    return (H, dets, F, tei)

def do_sf_cas( charge, mult, mol, conf_space="", add_opts={}, sf_diag_method="LinOp", num_roots=6 ):
    psi4.core.clean()
    opts = {'basis': 'cc-pvdz',
            'scf_type': 'pk',
            'e_convergence': 1e-10,
            'd_convergence': 1e-10,
            'reference': 'rohf'}
    opts.update(add_opts)
    psi4.set_options(opts)
    e, wfn = psi4.energy('scf', molecule=mol, return_wfn=True)
    #H, dets, F, tei = get_sf_H(wfn, conf_space)
    #print(dets.shape)
    F = get_nsa_F(wfn)
    tei = get_nsa_tei(wfn)
    '''
    H_cis, dets_cis, F_cis, tei_cis = get_cis_H(wfn)
    tf_matrix = np.isclose(H, H_cis)
    for i, det in enumerate(dets):
        print("DET")
        print(det)
        print("CONFLICTS WITH")
        for j in range(dets.shape[0]):
            if(not tf_matrix[i, j]):
                print(dets[j])
    '''
    socc = wfn.soccpi()[0]
    nb_virt = wfn.basisset().nbf() - wfn.doccpi()[0]
    if(conf_space==""):
        n_dets = socc * socc
    if(conf_space=="p"):
        n_dets = socc * nb_virt
    if(sf_diag_method == "RSP"):
        print("FROM DIAG: ", e + np.sort(LIN.eigvalsh(H))[0:8])
        print("FROM DIAG: ", np.sort(LIN.eigvalsh(H))[0:6])
        return(e + np.sort(LIN.eigvalsh(H))[0])
    if(sf_diag_method == "LinOp"):
        #A = SPLIN.LinearOperator(H.shape, matvec=mv)
        a_occ = wfn.doccpi()[0] + wfn.soccpi()[0]
        b_occ = wfn.doccpi()[0]
        a_virt = wfn.basisset().nbf() - a_occ
        b_virt = wfn.basisset().nbf() - b_occ
        print("Number of determinants:", n_dets)
        A = LinOpH((n_dets,n_dets), a_occ, b_occ, a_virt, b_virt, F, tei, conf_space_in=conf_space)
        vals, vects = SPLIN.eigsh(A, which='SA', k=num_roots)
        print("FROM LinOp:  ", vals)
        return(e + vals[0])

