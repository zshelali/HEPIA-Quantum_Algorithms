import quantum_tools as qt
import random as rand
from qiskit import QuantumCircuit
from math import pi
from rich.traceback import install

install()


class Client:
    def __init__(self):
        self.local_keys = {}

    def load_int(self, val):
        bin_len = max(2, val.bit_length())
        val_bin = format(val, f"0{bin_len}b")[::-1]
        qc = QuantumCircuit(max(2, bin_len))
        for i, bit in enumerate(val_bin):
            if bit == "1":
                qc.x(i)
        return qc

    def encrypt(self, psi):
        bin_len = max(1, psi.bit_length())
        val_bin = format(psi, f"0{2}b")
        P = QuantumCircuit(max(1, bin_len))
        P.name = f"Encrypted: {psi}"
        self.local_keys = {}
        # Encoding the binary value into the quantum register
        for i, bit in enumerate(val_bin):
            if bit == "1":
                P.x(i)
        for k in range(bin_len):
           a, b = rand.randint(0, 1), rand.randint(0, 1)
           if a == 1:
               P.x(k)
           if b == 1:
               P.z(k)
           self.local_keys[k] = (a, b)
        return P

    def get_local_keys(self):
        return self.local_keys

    def decrypt(self, psi_tilde):
        # TODO: write this function
        pass
          
    def update_key(self, key_pair: tuple[int, int]):
        """
        Hardcoded for two_qubit_adder().
        """
        pass

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
                theta = 2**(i)*pi/(2**(j-(n//2)))
                qc.cp(theta=theta, control_qubit=i, target_qubit=j)
        qc.append(qt.qft(2, inverse=False, swap=False), [2, 3])

        qc.measure([2, 3], [0, 1])
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

print(adder_pipeline(1, 2))

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

