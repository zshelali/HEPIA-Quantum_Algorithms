import unittest
from Grover import *
from qiskit import QuantumCircuit

class TestLoad1(unittest.TestCase):

    def setUp(self):
        self.base_qc = load_array([1, 0, 2])
        self.simulator = AerSimulator()

    def _run_counts(self, qc):
        transpiled = transpile(qc, self.simulator)
        result = self.simulator.run(transpiled).result()
        return result.get_counts(transpiled)


    def test_for_index_zero(self):
        qc = self.base_qc.copy()
        qc.measure_all()
        counts = self._run_counts(qc)
        best_result = max(counts, key=counts.get)
        self.assertEqual(best_result, '0100') # value 1, index 0 

    def test_for_index_one(self):
        prep = QuantumCircuit(self.base_qc.num_qubits)
        prep.x(0)
        qc = prep.compose(self.base_qc, inplace=False)
        qc.measure_all()
        counts = self._run_counts(qc)
        best_result = max(counts, key=counts.get)
        self.assertEqual(best_result, '0001') # value 0, index 1
    
    def test_for_index_two(self):
        prep = QuantumCircuit(self.base_qc.num_qubits)
        prep.x(1)
        qc = prep.compose(self.base_qc, inplace=False)
        qc.measure_all()
        counts = self._run_counts(qc)
        best_result = max(counts, key=counts.get)
        self.assertEqual(best_result, '1010') # value 2, index 2
        


if __name__ == '__main__':
    unittest.main()