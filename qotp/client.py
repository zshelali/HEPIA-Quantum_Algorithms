# fmt: off
# In update_key:
#
# TODO: Make sure that P(pi/2) is handled as a P or S gate,
# and that P(pi/4) is handled as T gate.
#
# TODO: Include gate adjoints (_dg)
#
# TODO: Handle the non-Clifford T gate
#
# TODO: Maybe? Include P(pi) = Z gates
from qiskit import QuantumCircuit
import random as random
from qiskit.circuit.library import HGate
import numpy as np

from ciphertext import Ciphertext
from server import Server

class Client:
    def __init__(self):
        self.keys = {}

    def load_int(self, val: int) -> QuantumCircuit:
        """
        Loads an unencrypted integer into a circuit
        """
        bin_len = max(2, val.bit_length())
        val_bin = format(val, f"0{bin_len}b")[::-1]
        qc = QuantumCircuit(max(4, bin_len))
        for i, bit in enumerate(val_bin):
            if bit == "1":
                qc.x(i)
        return qc

    def encrypt(self, psi: int, server: Server, offset: int = 0) -> Ciphertext:
        """
        Returns Cipher(physical: QuantumCircuit, keys: dict)
        """
        bin_len = max(2, psi.bit_length())
        val_bin = format(psi, f"0{bin_len}b")[::-1]
        num_qubits = server.get_num_qubits()
        physical = QuantumCircuit(bin_len)
        keys = {}
        for i, bit in enumerate(val_bin):
            if bit == "1" and offset + i < num_qubits:
                physical.x(i)
        for k in range(num_qubits):
            a, b = random.randint(0, 1), random.randint(0, 1)
            keys[k] = (a, b)
        for i in range(bin_len):
            a, b = keys[i + offset]
            if a == 1:
                physical.x(i)
            if b == 1:
                physical.z(i)
        return Ciphertext(physical, keys)

    def decrypt(self, psi_tilde: str) -> str:
        """
        Decrypts a measured state.
        For a classical Z-basis measurement, only the X mask affects the outcome,
        as Z is only a phase that is invisible when measured.
        """
        res = []
        for i, bit in enumerate(psi_tilde):
            decrypted_bit = str((self.keys[i][0]) ^ int(bit))
            res.append(decrypted_bit)
        return "".join(res)

    @staticmethod
    def get_qubit_index(qc, i: int, n: int) -> int:
        """
        Returns the index of a qubit inside a QuantumCircuit
        """
        return qc.find_bit(qc.data[i].qubits[n]).index

    def update_key(self, qc: QuantumCircuit):
        """
        Updates QOTP private keys for circuits containing only Clifford gates.
        Handles: h, s (p), and cx gates.
        """
        names = []
        # print(f"Before update, current state:\n{self.keys}")
        for i in range(len(qc.data)):
            gate_name = qc.data[i].name
            gate_theta = 0
            if qc.data[i].params:
                gate_theta = qc.data[i].params[0]
            names.append(gate_name)

            # Hadamard gate
            if gate_name == "h":
                a, b = self.keys[Client.get_qubit_index(qc, i, 0)]
                a, b = b, a
                self.keys[Client.get_qubit_index(qc, i, 0)] = a, b
                print(f"✅ update key: encountered H gate at index {i}\n\n")

            # S or P gate / S_dg or P_dg
            elif gate_name == "p" and (np.isclose(gate_theta, np.pi / 2) or np.isclose(gate_theta, -np.pi / 2)):
                a, b = self.keys[Client.get_qubit_index(qc, i, 0)]
                a, b = a, a ^ b
                self.keys[Client.get_qubit_index(qc, i, 0)] = a, b
                print(f"✅ update key: encountered P({gate_theta}) gate (pi/2) or (-pi/2) at index {i}\n\n")

            # CNOT gate
            elif gate_name == "cx":
                ai, bi = self.keys[Client.get_qubit_index(qc, i, 0)]
                aj, bj = self.keys[Client.get_qubit_index(qc, i, 1)]
                ai, bi = ai, bi ^ bj
                aj, bj = ai ^ aj, bj
                self.keys[Client.get_qubit_index(qc, i, 0)] = ai, bi
                self.keys[Client.get_qubit_index(qc, i, 1)] = aj, bj
                print(f"✅ update key: encountered CNOT gate at index {i}\n\n")

            
            # pauli gates 
            elif gate_name in ["x", "y", "z", "i", "id"]:
                print(f"ℹ️ nothing updated: encountered Pauli {gate_name} gate at index {i}\n\n")
                pass

            else:
                print(f"🚨 unverified gate encountered: {gate_name} theta={gate_theta} at index {i}\n\n")
                pass
        # print(f"Update key, current state:\n{self.keys}")
        print("names: ", names)
