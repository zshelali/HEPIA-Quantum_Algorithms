from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from math import pi
import numpy as np

def init():
    global GATE
    GATE = {
        "I": np.array([[1, 0],
                       [0, 1]], complex),

        "X":  np.array([[0, 1],
                        [1, 0]], complex),

        "Y":  np.array([[0, -1j],
                        [1j, 0]], complex),

        "Z":  np.array([[1, 0],
                        [0, -1]], complex),

        "H": (1/np.sqrt(2)) * np.array([[1, 1],
                                        [1, -1]], complex),
        "CNOT": np.array([[1, 0, 0, 0],
                          [0, 1, 0, 0],
                          [0, 0, 0, 1],
                          [0, 0, 1, 0]], complex),

        "P": np.array([[1, 0], 
                       [0, 1j]], complex),

        "CP": np.array([[1, 0, 0, 0],
                         [0, 1, 0, 0],
                         [0, 0, 1, 0],
                         [0, 0, 0, np.exp(1j*(np.pi/2))]]),
        
        "QFT2": 0.5 * np.array([
        [1,  1,  1,  1],
        [1,  1j, -1, -1j],
        [1, -1,  1, -1],
        [1, -1j, -1,  1]], complex)
    }




def qft(n, swap=True, inverse=False):
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
        for others in range(current+1, n):
            qc.cp(theta=-2*pi/2**(others-current+1), control_qubit=others, target_qubit=current)

    if swap == True:
        for j in range(n//2):
            qc.swap(j, n-1-j)
           
    if inverse == True: 
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



def clifford(u):
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

    else: raise ValueError("Unsupported gate size")

    return {"x_result": x_result, "z_result": z_result}


