from qiskit import QuantumCircuit


class Server:
    def __init__(self, circuit: QuantumCircuit):
        self.circuit = circuit
        self.num_qubits = circuit.num_qubits

    def get_num_qubits(self) -> int:
        return self.num_qubits
