import quantum_tools as qt
import random as random
from qiskit import QuantumCircuit
import numpy as np
from rich.traceback import install

install()
qt.init()

class Client:
    def __init__(self):
        self.keys = {}

    def load_int(self, val):
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

    def encrypt(self, psi, server):
        """
        Equivalent to load_int but encrypts `psi`, and generates a key pair for each qubit in the server circuit.
        """
        bin_len = max(2, psi.bit_length())
        val_bin = format(psi, f"0{bin_len}b")[::-1]
        num_qubits = server.get_num_qubits()
        P = QuantumCircuit(max(4, bin_len))
        P.name = f"Encrypted: {psi}"
        # Encoding the binary value into the quantum register
        for i, bit in enumerate(val_bin):
            if bit == "1":
                P.x(i)
        for k in range(num_qubits):
           a, b = random.randint(0, 1), random.randint(0, 1)
           if a == 1:
               P.x(k)
           if b == 1:
               P.z(k)
           self.keys[k] =  (a, b)
        return P


    def decrypt(self, psi_tilde):
        """
        Decrypts a measured state. 
        For a classical Z-basis measurement, only the X mask affects the outcome, 
        as Z is only a phase that is invisible when measured.
        """
        res = list(psi_tilde)
        for i, bit in enumerate(psi_tilde[::-1]):
            res[i] = str((self.keys[i][0]) ^ int(bit))
        return "".join(res[::-1])
            

    @staticmethod
    def get_qubit_index(qc, i, n):
        """
        Returns the index of a qubit inside a QuantumCircuit
        """
        return qc.find_bit(qc.data[i].qubits[n]).index


    def update_key(self, qc):
        """
        Updates QOTP private keys for circuits containing only Clifford gates.
        """
        print(f"Before update, current state:\n{self.keys}")
        for i in range(len(qc.data)):
            gate_name = qc.data[i].name
            if gate_name == "h":
                a, b = self.keys[Client.get_qubit_index(qc, i, 0)]
                a, b = b, a
                self.keys[Client.get_qubit_index(qc, i, 0)] = a, b
            if gate_name == "s":
                a, b = self.keys[Client.get_qubit_index(qc, i, 0)]
                a, b = a, a ^ b
                self.keys[Client.get_qubit_index(qc, i, 0)] = a, b
            if gate_name == "cx":
                ai, bi = self.keys[Client.get_qubit_index(qc, i, 0)]
                aj, bj = self.keys[Client.get_qubit_index(qc, i, 1)]

                ai, bi = ai, bi ^ bj
                aj, bj = ai ^ aj, bj
                self.keys[Client.get_qubit_index(qc, i, 0)] = ai, bi
                self.keys[Client.get_qubit_index(qc, i, 1)] = aj, bj
        
        print(f"Update key, current state:\n{self.keys}")



class Server:
    def __init__(self):
        self.circuit = Server.random_circuit()
        self.num_qubits = self.circuit.num_qubits

    def get_num_qubits(self):
        return self.num_qubits
   
    @staticmethod
    def random_circuit():
        """
        Visualize circuit @ https://algassert.com/quirk#circuit={%22cols%22:[[%22X%22,1,%22H%22],[%22%E2%80%A2%22,1,1,%22X%22],[1,1,1,%22X%22],[1,1,%22H%22],[%22Measure%22,%22Measure%22,%22Measure%22,%22Measure%22],[%22Chance4%22]],%22init%22:[1,0,1]}
        """
        qc = QuantumCircuit(4)
        qc.name = "Server circuit"
        qc.x(0)
        qc.h(2)
        qc.cx(0, 3)
        qc.x(3)
        qc.h(2)
        return qc


def pipe(p,shots=20):
    results = []
    for it in range(shots):
        print(f"Test num {it}")
        sv = Server()
        cl = Client()
        x = cl.encrypt(p, sv)
        server_circuit = sv.random_circuit()
        x.append(server_circuit, [k for k in range(server_circuit.num_qubits)])
        cl.update_key(server_circuit)
        x.measure_all()
        res = qt.get_result_with_noise(x)
        max_res = max(res, key=res.get)
        decrypted_res = cl.decrypt(max_res)
        results.append(decrypted_res)

    return results

print("final result :", pipe(5, shots=1), "\n")
