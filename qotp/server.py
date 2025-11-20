from qiskit.circuit import CircuitInstruction


class Server:
    def __init__(self, circuit):
        self.circuit = circuit
        self.num_qubits = circuit.num_qubits

    def get_num_qubits(self):
        return self.num_qubits

    @staticmethod
    def non_clifford_handler(qc, index):
        print("non_clifford_handler")
        pass
        # qc.data[index] = CircuitInstruction()
