from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit_ibm_runtime.fake_provider import FakeGeneva


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
