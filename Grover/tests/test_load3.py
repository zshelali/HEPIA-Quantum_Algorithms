import unittest
from Grover import *
from qiskit import QuantumCircuit

class TestLoad1(unittest.TestCase):

    def setUp(self):
        self.simulator = AerSimulator()

    def _run_counts(self, qc):
        transpiled = transpile(qc, self.simulator)
        result = self.simulator.run(transpiled).result()
        return result.get_counts(transpiled)


    def test_for_empty(self):
        qc = load_array([])
        self.assertEqual(qc.num_qubits, 0)

    def test_for_max_zero(self):
        qc = load_array([0, 0, 0, 0, 0])
        qc.measure_all()
        counts = self._run_counts(qc)
        best_result = max(counts, key=counts.get)
        self.assertEqual(best_result, '000') # log2(1) = 0 ==> only 3 qubits and not 4 
        


if __name__ == '__main__':
    unittest.main()