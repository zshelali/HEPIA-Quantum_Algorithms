from typing import Tuple
from qiskit import QuantumCircuit, transpile
from math import pi
import numpy as np
import numpy.typing as npt


def init_gate():
    global GATE
    GATE = {
        "I": np.array([[1, 0], [0, 1]], complex),
        "X": np.array([[0, 1], [1, 0]], complex),
        "Y": np.array([[0, -1j], [1j, 0]], complex),
        "Z": np.array([[1, 0], [0, -1]], complex),
        "H": (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], complex),
        "CNOT": np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], complex
        ),
        "P": np.array([[1, 0], [0, 1j]], complex),
        "CPpi/2": np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, np.exp(1j * (np.pi / 2))],
            ]
        ),
        "QFT2": 0.5
        * np.array(
            [
                [1, 1, 1, 1],
                [1, 1j, -1, -1j],
                [1, -1, 1, -1],
            ]
        ),
        "T": np.diag([1, np.exp(1j * pi / 4)]),
    }


init_gate()


def clifford_matrix(u) -> dict[str, npt.NDArray]:
    """
    For 1 qubit matrices only.
    Returns UXU_dg and UZU_dg.
    If the output matrix is c*P
    with P in {X,Y,Z,I}
    and c a constant generally in {i, -i, 1, -1}
    then the matrix is Clifford.
    """
    u_dg = u.conj().T
    x_result = 0
    z_result = 0
    if len(u) == 2:
        x_result = u @ GATE["X"] @ u_dg
        z_result = u @ GATE["Z"] @ u_dg

    elif len(u) == 4:
        X = np.kron(GATE["X"], GATE["I"])
        Z = np.kron(GATE["Z"], GATE["I"])
        x_result = u @ X @ u_dg
        z_result = u @ Z @ u_dg

    else:
        raise ValueError("Unsupported gate size")

    return {"x_result": x_result, "z_result": z_result}


def to_standard(qc: QuantumCircuit) -> QuantumCircuit:
    """
    Transpiles a circuit into a circuit composed of
    only Clifford and T/T_dg gates.
    """
    basis_gates = ["h", "s", "sdg", "cx", "x", "z", "t", "tdg", "p", "pdg", "bonsoir"]
    qc_standard = transpile(
        qc.decompose(), basis_gates=basis_gates, optimization_level=0
    )
    # print(qc_standard)
    return qc_standard


# Source - https://stackoverflow.com/questions/12988351/split-a-dictionary-in-half
# Posted by Blckknght
# Retrieved 2025-11-06, License - CC BY-SA 3.0
import itertools


def splitDict(d: dict) -> Tuple[dict, dict]:
    n = len(d) // 2  # length of smaller half
    i = iter(d.items())  # alternatively, i = d.iteritems() works in Python 2

    d1 = dict(itertools.islice(i, n))  # grab first n items
    d2 = dict(i)  # grab the rest

    return d1, d2


### END OF SOURCE stackoverflow


def is_t_gate(instruction) -> bool:
    gate_theta = 0
    if instruction.name in ["t", "td"]:
        return True
    if not instruction.params:
        return False
    gate_theta = instruction.params[0]
    if instruction.name == "p" and np.isclose(gate_theta, np.pi / 4):
        return True
    return False


def is_t_dg(instruction) -> bool:
    gate_theta = 0
    if instruction.params:
        gate_theta = instruction.params[0]
    if instruction.name == "p" and np.isclose(gate_theta, -np.pi / 4):
        return True
    return False


def get_qubit_index(
    qc: QuantumCircuit, instruction=None, i: int | None = None, n: int | None = None
) -> int | list[int]:
    """
    Returns the qubit index/indices from a quantum circuit.

    Parameters:
        qc: The quantum circuit
        instruction: A circuit instruction (gate/operation). If provided, returns indices of all qubits it acts on.
        i: Instruction position in qc.data. Must be used with parameter n.
        n: Qubit position within the instruction. Must be used with parameter i.

    Returns:
        int: Single qubit index (when using i,n or when instruction acts on 1 qubit)
        list[int]: Multiple qubit indices (when instruction acts on multiple qubits)

    Raises:
        ValueError: If both modes are provided, neither mode is provided, or instruction has no qubits

    Examples:
        # Get the 0th qubit from the 5th instruction
        >>> idx = get_qubit_index(qc, i=5, n=0)

        # Get all qubit indices that a gate acts on
        >>> indices = get_qubit_index(qc, instruction=my_gate)
    """
    has_i_and_n = i is not None and n is not None
    has_instruction = instruction is not None

    if has_i_and_n and has_instruction:
        raise ValueError(
            "ambiguous inputs. provide either (i, n) or instruction, not both"
        )
    if not has_i_and_n and not has_instruction:
        raise ValueError("must provide either (i, n) or instruction")

    if has_i_and_n:
        return qc.find_bit(qc.data[i].qubits[n]).index

    elif has_instruction:
        l = len(instruction.qubits)
        if l == 0:
            raise ValueError("instruction length is 0")
        else:
            indices = [qc.find_bit(qubit).index for qubit in instruction.qubits]
            if l == 1:
                return indices[0]
            return indices
    else:
        raise ValueError("unreachable: validation failed")


# def get_qubit_index(qc: QuantumCircuit, instruction) -> int | list[int]:
#     """
#     Returns the index of an instruction.
#     If the instruction acts on multiple qubits,
#     returns a list of indices.
#     """
#     n = len(instruction.qubits)
#     if n == 0:
#         raise ValueError("instruction length is 0")
#     if n >= 1:
#         indices = [qc.find_bit(qubit).index for qubit in instruction.qubits]
#         if n == 1:
#             return indices[0]
#         return indices
#     return -2
