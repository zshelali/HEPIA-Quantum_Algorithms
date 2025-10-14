from quantum_tools import qft, get_result
import random as rand
from qiskit import QuantumCircuit
from math import pi

class Client:
    def __init__(self):
        self.local_keys = {}

    def encrypt(self, psi):
        bin_len = max(1, psi.bit_length())
        val_bin = format(psi, f"0{2}b")[::-1]
        P = QuantumCircuit(max(2, bin_len))
        P.name = f"Encrypted: {psi}"
        self.local_keys = {}
        # Encoding the binary value in the quantum register
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
        Hardcoded for two_qubit_adder() for now.
        """
        pass


class Server:
    def __init__(self):
        self.circuit = QuantumCircuit()

    def two_qubit_adder(self, enc_x, enc_y):
        #TODO: universalize the function to take n odd and even.
        n = 4
        if n % 2 != 0:
            n_odd = n - 1 
        qc = QuantumCircuit(n, n // 2)
        qc.append(qft(n//2), [s for s in range(n - 1, n // 2, -1)])
        qc.append(enc_x, [s for s in range ((n // 4) + 1)])
        qc.append(enc_y, [s for s in range((n // 4) + 1, (n // 2) + 1)])
        for i in range(n//2 +1):
            for j in range(n//2 + 1, n):
                # TODO: fix the angle with the correct theta value
                qc.cp(theta=(2*pi)/(2**(n-i-j)), control_qubit=i, target_qubit=j)
            qc.barrier()
        qc.append(qft(n // 2, inverse=True), [s for s in range(n - 1, n // 2, -1)])
        for s in range(n // 2 + 1, n):
            qc.measure(s, n - s - 1)
        return qc


cl = Client()
sv = Server()


x = cl.encrypt(2)
y = cl.encrypt(1)
sv.two_qubit_adder(x, y).draw("mpl", filename="test.png", fold=False)
    











