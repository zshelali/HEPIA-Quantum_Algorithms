from typing import Tuple
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import CircuitInstruction, gate
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from math import pi
import numpy as np
import numpy.typing as npt
from qiskit_ibm_runtime.fake_provider import FakeGeneva
from qiskit.visualization import plot_histogram


def init():
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


init()


def qft(n, swap=True, inverse=False) -> QuantumCircuit:
    """
    Build a Quantum Fourier Transform (QFT) circuit.
    The `inverse=False` here is qiskit's `inverse=True`.

    Args:
        n (int): Number of qubits.
        swap (bool): If True, add final swap gates to reverse qubit order
            (standard QFT layout). If False, output is in bit-reversed order.
        inverse (bool): If True, construct the inverse QFT (IQFT) by using
            negative phase angles.

    Returns:
        QuantumCircuit: Qiskit QuantumCircuit implementing the QFT or IQFT
        on n qubits.

    Example:
        >>> qft(2, inverse=False).draw(output="mpl", filename="my_qft.png", fold=False)

    """
    qc = QuantumCircuit(n)
    qc.name = "QFT"
    for current in range(n):
        qc.barrier()
        qc.h(current)
        for others in range(current + 1, n):
            qc.cp(
                theta=-2 * pi / 2 ** (others - current + 1),
                control_qubit=others,
                target_qubit=current,
            )

    if swap:
        for j in range(n // 2):
            qc.swap(j, n - 1 - j)

    if inverse:
        inverted_qc = qc.inverse()
        return inverted_qc

    return qc


def get_result(qc, shots=100):
    """
    Simulate a quantum circuit and return its measurement outcomes.

    Args:
        qc (QuantumCircuit): The quantum circuit to simulate.

    Returns:
        dict: A dictionary mapping bitstrings to their measured counts
        after 100 simulation shots.

    Example:
        >>> counts = get_result(my_circuit)
        >>> print(counts)
        {'00': 51, '11': 49}

    Notes:
        The circuit is transpiled for the AerSimulator backend before execution.
        Adjust 'shots' or backend parameters as needed for higher precision.
    """
    simulator = AerSimulator()
    compiled = transpile(qc, simulator)
    return simulator.run(compiled, shots=shots).result().get_counts()


def get_result_geneva(qc, shots=1024):
    device_backend = FakeGeneva()
    sim_geneva = AerSimulator.from_backend(device_backend)
    tcirc = transpile(qc, sim_geneva)
    result_noise = sim_geneva.run(tcirc, shots=shots).result()
    counts_noise = result_noise.get_counts(0)
    return counts_noise


def get_result_with_noise(qc):
    # https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models
    error = depolarizing_error(1e-3, 1)  # (errreur qubit,nombre de qubit impacté)
    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(
        error,
        [
            "x",
            "h",
            "z",
        ],
    )
    simulator = AerSimulator(noise_model=noise_model)
    compiled = transpile(qc, simulator)
    return simulator.run(compiled, shots=100).result().get_counts()


def clifford(u) -> dict[str, npt.NDArray]:
    """
    Returns uxu_dg and uzu_dg
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


def two_qubit_adder() -> QuantumCircuit:
    # TODO: universalize the function to take n odd and even.
    n = 4
    qc = QuantumCircuit(4)
    # qc.append(x, [0, 1])
    # qc.append(y, [2, 3])
    qc.append(qft(2, inverse=True, swap=False), [2, 3])

    for i in range(n):
        for j in range(i + 2, n):
            theta = 2 ** (i) * np.pi / (2 ** (j - (n // 2)))
            qc.cp(theta=theta, control_qubit=i, target_qubit=j)
    qc.append(qft(2, inverse=False, swap=False), [2, 3])

    # qc.measure([2, 3], [0, 1])
    return qc


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


def has_t_gates(qc: QuantumCircuit) -> bool:
    """
    Returns True if the circuit contains at least one Non-Clifford gate.
    """
    for instruction in qc.data:
        if instruction.name in ["t", "tdg"]:
            return True
        if instruction.name == "p":
            gate_theta = instruction.params[0]
            if np.isclose(gate_theta, np.pi / 4) or np.isclose(gate_theta, -np.pi / 4):
                return True
    return False


def random_circuit() -> QuantumCircuit:
    """
    Visualize circuit @
    https://algassert.com/quirk#circuit={%22cols%22:[[%22X%22,1,%22H%22],[%22%E2%80%A2%22,1,1,%22X%22],[1,1,1,%22X%22],[1,1,%22H%22],[%22Measure%22,%22Measure%22,%22Measure%22,%22Measure%22],[%22Chance4%22]],%22init%22:[1,0,1]}
    """
    qc = QuantumCircuit(4)
    qc.name = "Server circuit"
    qc.x(0)
    qc.h(2)
    qc.cx(0, 3)
    qc.x(3)
    qc.h(2)
    return qc
