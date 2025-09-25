import unittest
from Grover import *
from qiskit import QuantumCircuit

class TestLoad2(unittest.TestCase):

    def setUp(self):
        self.base_qc = load_array([5, 3, 0, 2, 1, 4])
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
        self.assertEqual(best_result, '101000') # value 5, index 0

    def test_for_index_one(self):
        prep = QuantumCircuit(self.base_qc.num_qubits)
        prep.x(0)
        qc = prep.compose(self.base_qc, inplace=False)
        qc.measure_all()
        counts = self._run_counts(qc)
        best_result = max(counts, key=counts.get)
        self.assertEqual(best_result, '011001') # value 3, index 1
    
    def test_for_index_five(self):
        prep = QuantumCircuit(self.base_qc.num_qubits)
        prep.x(0)
        prep.x(2)
        qc = prep.compose(self.base_qc, inplace=False)
        qc.measure_all()
        counts = self._run_counts(qc)
        best_result = max(counts, key=counts.get)
        self.assertEqual(best_result, '100101') # value 4, index 5
        


if __name__ == '__main__':
    unittest.main()