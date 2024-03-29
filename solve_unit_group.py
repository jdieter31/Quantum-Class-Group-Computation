from typing import Iterable, Union, List
from sage.all import *
from sage.rings.number_field.number_field_ideal import NumberFieldIdeal
import numpy as np
import olll
from pyquil.quilatom import QubitPlaceholder
from pyquil import Program

# Compute the group of S_units for a number field k
def compute_S_units(S: NumberFieldIdeal, k: NumberField):
    # TODO 
    # Using functions for creating quantum oracle state below,
    # use quantum algorithm for solving hidden subgroup problem
    # presented in one of the two main papers referenced
    pass

# Gets basis of \phi(x) * O_k * p_1^{-v_1}...p_k^{-v_k}
def get_lattice_basis(S: Iterable[NumberFieldIdeal], k: NumberField, z_input: Iterable[Integer], input_component_real: np.ndarray , input_component_real_sign: np.ndarray, input_component_complex: np.ndarray, input_component_complex_phase: np.ndarray):
    input_lattice_representation_real = input_component_real_sign * np.exp(input_component_real)
    input_lattice_representation_complex = np.exp(1j * input_component_complex_phase) * np.exp(input_component_complex)

    # Get ideal generated by p_i^v_i 
    ideal_product = None
    for ideal, z in zip(S, z_input):
        if ideal_product:
            ideal_product = ideal_product*(ideal**(-z))
        else:
            ideal_product = ideal ** -z

    real_embedding, complex_embedding = get_E_embedding(k)
    
    if ideal_product:
        if real_embedding.size > 0:
            ideal_embed_basis_real = [np.matmul(real_embedding.T, generator.vector().numpy(dtype='float64')) for generator in ideal_product.basis()]
            ideal_embed_basis_real = np.array(ideal_embed_basis_real)
        else:
            ideal_embed_basis_real = real_embedding

        if complex_embedding.size > 0:
            ideal_embed_basis_complex = [np.matmul(complex_embedding.T, generator.vector().numpy(dtype="complex")) for generator in ideal_product.basis()]
            ideal_embed_basis_complex = np.array(ideal_embed_basis_complex)
        else:
            ideal_embed_basis_complex = complex_embedding
    else:
        ideal_embed_basis_real = real_embedding
        ideal_embed_basis_complex = complex_embedding

    real_part = None
    if ideal_embed_basis_real.size != 0:
        real_part = (input_lattice_representation_real * ideal_embed_basis_real).T

    complex_part = None
    if ideal_embed_basis_complex.size != 0:
        complex_part = (input_lattice_representation_complex * ideal_embed_basis_complex).T

    return real_part, complex_part


def get_E_embedding(k: NumberField):
    # Get real minkowski embedding
    mink = k.minkowski_embedding().numpy(dtype="float64")
    real_embeddings = len(k.embeddings(RR))
    
    real_part = mink[:,:real_embeddings]
    complex_part = np.ascontiguousarray(mink[:,real_embeddings:]).astype(np.complex)
    
    for i in range(complex_part.shape[1]//2):
        scaling_array = 0.5 * np.sqrt(2) * np.array([
            [1, -1j],
            [1, 1j]
        ])
        complex_part[:,2*i:2*(i + 1)] = np.matmul(scaling_array, complex_part[:,2*i:2*(i + 1)].T).T    
    return (real_part, complex_part)

# Makes a real representation of a complex embedding that has complex conjugate in adjacent coordinates as all
# complex embeddings of a number field will
# Does't preserve contents of array
def get_real_representation_of_complex_embedding(complex_embedding):

    for i in range(complex_embedding.shape[1]//2):
        scaling_array = 0.5 * np.sqrt(2) * np.array([
            [1, 1],
            [-1j, 1j]
        ])
        complex_embedding[:,2*i:2*(i + 1)] = np.matmul(scaling_array, complex_embedding[:,2*i:2*(i + 1)].T).T
    return complex_embedding.astype('float64')

# Compute lattice superposition as described in paper with straddle encoding parameter nu, s
# nu should be small enough that no two basis vectors
def get_oracle_superposition_for_lattice(lattice_basis_real, lattice_basis_complex, qubits: List[QubitPlaceholder], nu, s):
    real_representation = get_real_representation_of_complex_embedding(lattice_basis_complex)
    if real_representation.size == 0:
        concatenated_basis = lattice_basis_real
    elif lattice_basis_real.size == 0:
        concatenated_basis = real_representation
    else:
        concatenated_basis = np.concatenate([lattice_basis_real,real_representation], axis=-1)
    
    concatenated_basis = get_lll_lattice_basis(concatenated_basis)
    n = concatenated_basis.shape[-1] 

    qubits_per_dim = len(qubits)//n

    state_program = Program()

    # Largest integer in each coordinate that can be represented with this configuration
    max_grid_representable = 2 ** qubits_per_dim
    
    def build_scaling_array_recursive(basis=[]):
        if len(basis) != n:
            return [build_scaling_array_recursive(basis + [i]) for i in range(max_grid_representable)]
        else:
            lattice_vector = np.array(basis).dot(concatenated_basis.T)
            return np.squeeze(np.exp(- np.pi * (np.linalg.norm(lattice_vector) ** 2) / (s ** 2)))

    gaussian_basis_scale = np.array(
        build_scaling_array_recursive()
    )
    
    for i in range(n_dim
    desired_state = np.zeros([n, 2 ** qubits_per_dim])

    assert 0 == 1

# Get base 2 representation of k
def get_base_2(k, num_qubits):
    sign_bit = 1 if k < 0 else 0
    out = [sign_bit]
    for i in range(num_qubits - 1):
        out.append((k % (2 ** (num_qubits - i)))//(2 ** (num_qubits + - i - 1)))
    return out


# Uses lll to get lattice basis with nicer properties
def get_lll_lattice_basis(lattice_basis, dimension: int, precision=0.0001):
    
    lattice_basis_round = np.rint(ideal_basis * (1/precision))
    lll_basis = np.array(olll.reduction(lattice_basis_round, 0.75), dtype="float64")
    return lll_basis * precision

# Reduces approximate lattice basis to smaller dimension
def reduce_lattice_basis(lattice_basis: np.ndarray, dimension: int, precision=0.0001):
    lattice_basis_round = np.rint(ideal_basis * (1/precision))
    lattice_basis = lattice_basis_round.concatenate((np.eye(lattice_basis.shape[0]), lattice_basis_round), axis=1)

    # Perform LLL reduction with delta=0.75
    reduced_basis = np.array(olll.reduction(lattice_basis.tolist(), 0.75), dtype="float64")
    reduced_basis = reduced_basis[-dimension:,lattice_basis.shape[0]:]
    return reduced_basis * precision

