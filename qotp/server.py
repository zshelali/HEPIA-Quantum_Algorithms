from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, AncillaRegister
from qiskit.circuit import CircuitInstruction
from qiskit.circuit.library import TGate, TdgGate, CXGate, Measure, SdgGate
import numpy as np
import warnings

import quantum_tools as qt


class Server:
    def __init__(self, circuit: QuantumCircuit):
        self.circuit = circuit
        self.num_qubits = circuit.num_qubits

    def get_num_qubits(self) -> int:
        return self.num_qubits
