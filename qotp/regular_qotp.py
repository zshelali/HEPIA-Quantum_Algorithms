import quantum_tools as qt
import random as random
from qiskit import QuantumCircuit
from math import pi
import numpy as np
from rich.traceback import install

install()
qt.init()

class Client:
    def __init__(self):
        # self.local_key = []
        # self.final_key = []
        self.keys = {"x": {}, "y": {}}

    # def reset_key(self):
    #     self.local_key = []
    #     self.final_key = []

    def load_int(self, val):
        bin_len = max(2, val.bit_length())
        val_bin = format(val, f"0{bin_len}b")[::-1]
        qc = QuantumCircuit(max(2, bin_len))
        for i, bit in enumerate(val_bin):
            if bit == "1":
                qc.x(i)
        return qc

    def encrypt(self, psi, reg):
        bin_len = max(2, psi.bit_length())
        val_bin = format(psi, f"0{bin_len}b")[::-1]
        P = QuantumCircuit(max(2, bin_len))
        P.name = f"Encrypted: {psi}"
        # Encoding the binary value into the quantum register
        for i, bit in enumerate(val_bin):
            if bit == "1":
                P.x(i)
        for k in range(bin_len):
           a, b = random.randint(0, 1), random.randint(0, 1)
           if a == 1:
               P.x(k)
           if b == 1:
               P.z(k)
           self.keys[reg][k] =  (a, b)
        return P

#    def get_local_key(self):
#        return self.local_key

    def decrypt(self, reg, psi):
        # TODO: implement 
        a_q3 = self.keys["y"][1][0]
        a_q2 = self.keys["y"][0][0]
        
        m1 = int(psi[0]) ^ a_q3
        m0 = int(psi[1]) ^ a_q2

        result = str(m1) + str(m0)
        return int(result, 2)
                          

    def update_key(self, reg):
        """
        Hardcoded for two_qubit_adder().
        Follows the rules of the QOTP key updates for Clifford gates.
        """
        twoQubits = False
        for i, (a, b) in self.keys[reg].items():
            # QFT(2)
            if i == 0: a, b = b, a # Hadamard
            if i == 1: a, b = a, a ^ b # pi/2 rotation
            if i == 2: a, b = b, a # Hadamard
            # Rotations (Z updates are skipped for they do not have an impact.)
            # Z
            if i == 4: a, b = a, a ^ b # pi/2 rotation
            # Z
            # QFT(2) dg
            if i == 6: a, b = b, a # Hadamard
            if i == 7: a, b = a, a ^ b # -pi/2 rotation
            if i == 8: a, b = b, a # Hadamard
            self.keys[reg][i] = (a, b)

    
    def universal_key_updater(self, qc, reg):
        """
        Updates QOTP private keys for circuits containing only Clifford gates.
        """
        for i in range(len(qc.data)):
            switch = qc.data[i].name
            print("qubits", qc.qubits, "\n")
            print("switch", switch, "\n")

            if switch == "h":
                a, b = b, a
            if switch == "s":
                a, b = a, a ^ b
            if switch == "cx":
                print(qc.data[i].qubits)

            self.keys[reg][i] = (a, b)
        print(f"Update key, current state:\n a = {a}, b = {b}")


            



class Server:
    def __init__(self):
        self.circuit = QuantumCircuit()

    @staticmethod
    def two_qubit_adder(x, y):
        #TODO: universalize the function to take n odd and even.
        n = 4
        qc = QuantumCircuit(4, 2)
        qc.append(x, [0, 1])
        qc.append(y, [2, 3])
        qc.append(qt.qft(2, inverse=True, swap=False), [2, 3])

        for i in range(n):
            for j in range(i + 2, n):
                theta = 2**(i)*np.pi/(2**(j-(n//2)))
                qc.cp(theta=theta, control_qubit=i, target_qubit=j)
        qc.append(qt.qft(2, inverse=False, swap=False), [2, 3])

        qc.measure([2, 3], [0, 1])
        return qc
    
    def random_circuit(self):
        qc = QuantumCircuit(4)
        qc.x(0)
        qc.h(1)
        qc.y(0)
        qc.cx(2, 3)
        qc.x(3)
        return qc

def adder_pipeline(x, y):
        """
        Two qubits adder without encryption (for now)
        """
        cl = Client()
        qx = cl.load_int(x)
        qy = cl.load_int(y)
        my_addition = Server.two_qubit_adder(qx, qy)
        return int(list(qt.get_result(my_addition, shots=100).keys())[0], 2)

def encrypted_adder_pipeline(x, y):
        cl = Client()
        qx = cl.encrypt(x, "x")
        qy = cl.encrypt(y, "y")
        addition = Server.two_qubit_adder(qx, qy)
        cl.update_key("x")
        cl.update_key("y")
        psi_tilde = list(qt.get_result(addition, shots=100).keys())[0]
        result = cl.decrypt("y", psi_tilde)
        return result


sv = Server()
cl = Client()
circ = sv.random_circuit()
cl.universal_key_updater(circ, "x")

# A = qt.clifford(qt.GATE["QFT2"])["x_result"]
# B = qt.clifford(qt.GATE["QFT2"])["z_result"]
# cleanA = np.real_if_close(A, tol=1000)
# cleanB = np.real_if_close(B, tol=1000)
# 
# cleanA[np.abs(cleanA) < 1e-12] = 0
# cleanB[np.abs(cleanB) < 1e-12] = 0
# 
# cleanA = np.real_if_close(cleanA, tol=1000)
# cleanB = np.real_if_close(cleanB, tol=1000)
# 
# cleanA[np.abs(cleanA) < 1e-12] = 0
# cleanB[np.abs(cleanB) < 1e-12] = 0
# 
# cleanA = np.round(cleanA, 6)
# cleanB = np.round(cleanB, 6)
# 
# print("x_result\n", cleanA)
# print("z_result\n", cleanB)


# [print(encrypted_adder_pipeline(1, 2)) for _ in range(50)]
#for i in range(4):
#    for j in range(4):
#        print(adder_pipeline(i, j))


# x = cl.encrypt(1)
# y = cl.encrypt(1)
# sv.two_qubit_adder(x, y).draw("mpl", filename="adder.png", fold=False)
#
#
# x = cl.load_int(0)
# y = cl.load_int(1)
#
#
#
# my_addition = sv.two_qubit_adder(x, y)
# my_addition.draw("mpl", filename="my_adder_test.png", fold=False)
#
# qiskit_addition = DraperQFTAdder(2).decompose()
# qiskit_addition.draw("mpl", filename="qiskit_test.png", fold=False)
#
# 

