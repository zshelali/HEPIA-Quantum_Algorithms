import quantum_tools as qt
import random as random
from qiskit import QuantumCircuit, ClassicalRegister, transpile
import numpy as np
from rich.traceback import install
import itertools
import matplotlib.pyplot as plt

install()
qt.init()


# Source - https://stackoverflow.com/questions/12988351/split-a-dictionary-in-half
# Posted by Blckknght
# Retrieved 2025-11-06, License - CC BY-SA 3.0


def splitDict(d):
    n = len(d) // 2  # length of smaller half
    i = iter(d.items())  # alternatively, i = d.iteritems() works in Python 2

    d1 = dict(itertools.islice(i, n))  # grab first n items
    d2 = dict(i)  # grab the rest

    return d1, d2


class Ciphertext:
    def __init__(self, circuit, keys):
        self.circuit = circuit
        self.keys = keys


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

    def encrypt(self, psi, server, offset=0):
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
        Handles: h, s (p), and cx gates.
        """
        # TODO: Make sure that P(pi/2) is handled as a P or S gate,
        # and that P(pi/4) is handled as T gate.
        #
        # TODO: Include gate adjoints (_dg)
        #
        # TODO: Handle the non-Clifford T gate
        #
        # TODO: Maybe? Include P(pi) = Z gates
        names = []
        # print(f"Before update, current state:\n{self.keys}")
        for i in range(len(qc.data)):
            gate_name = qc.data[i].name
            names.append(gate_name)
            if gate_name == "h":
                a, b = self.keys[Client.get_qubit_index(qc, i, 0)]
                a, b = b, a
                self.keys[Client.get_qubit_index(qc, i, 0)] = a, b
                print(f"✅ update key: encountered H gate at index {i}\n\n")
            elif gate_name == "s":
                a, b = self.keys[Client.get_qubit_index(qc, i, 0)]
                a, b = a, a ^ b
                self.keys[Client.get_qubit_index(qc, i, 0)] = a, b
                print(f"✅ update key: encountered S gate at index {i}\n\n")
            elif gate_name == "cx":
                ai, bi = self.keys[Client.get_qubit_index(qc, i, 0)]
                aj, bj = self.keys[Client.get_qubit_index(qc, i, 1)]
                ai, bi = ai, bi ^ bj
                aj, bj = ai ^ aj, bj
                self.keys[Client.get_qubit_index(qc, i, 0)] = ai, bi
                self.keys[Client.get_qubit_index(qc, i, 1)] = aj, bj
                print(f"✅ update key: encountered CNOT gate at index {i}\n\n")
            elif gate_name == "t":
                print(f"✅ update key: Non-Clifford gate encountered at index {i}\n\n")
            elif gate_name == "p":
                print(
                    f"❓ update key: encountered P gate at index {i}\n{qc.data[i].params}\n"
                )
        # print(f"Update key, current state:\n{self.keys}")
        print("names: ", names)


class Server:
    def __init__(self, circuit):
        self.circuit = circuit
        self.num_qubits = circuit.num_qubits

    def get_num_qubits(self):
        return self.num_qubits


def adder_pipe(a, b, shots=1):
    # TODO: find a way to deal with ancilla qubits (see quantum bootstrapping...)
    # FIXME:
    results = []
    if shots < 1:
        raise ValueError("At least give me one shot!")

    for _ in range(shots):
        sv = Server(qt.two_qubit_adder().decompose())
        cl = Client()
        # sv.circuit.draw("text", fold=-1)
        # sv.circuit.draw("mpl", fold=-1)
        # plt.show()
        cipher_x = cl.encrypt(a, sv)
        offset = cipher_x.circuit.num_qubits
        # print(f"offset={offset}")
        cipher_y = cl.encrypt(b, sv, offset)
        merged_keys = {}
        for i in range(cipher_x.circuit.num_qubits):
            merged_keys[i] = cipher_x.keys[i]
        for i in range(cipher_y.circuit.num_qubits):
            merged_keys[i + offset] = cipher_y.keys[i + offset]
        cl_reg = ClassicalRegister(cipher_y.circuit.num_qubits)
        full_circuit = cipher_y.circuit ^ cipher_x.circuit
        full_circuit.add_register(cl_reg)
        full_circuit.append(
            sv.circuit,
            [_ for _ in range(full_circuit.num_qubits)],
            [_ for _ in range(sv.circuit.num_clbits)],
        )

        full_circuit.measure(
            [k for k in range(offset, cipher_y.circuit.num_qubits + offset)], [0, 1]
        )

        basis_gates = ["h", "s", "sdg", "cx", "x", "z", "t", "tdg", "p"]
        qc_standard = transpile(
            full_circuit, basis_gates=basis_gates, optimization_level=0
        )
        # print(cipher_x.circuit)
        # print(cipher_y.circuit)
        # print(sv.circuit)
        # print(full_circuit)
        cl.keys = merged_keys
        cl.update_key(qc_standard)
        # print("before update keys:\n", merged_keys)
        # print("updated keys:\n", cl.keys)


adder_pipe(1, 2)
