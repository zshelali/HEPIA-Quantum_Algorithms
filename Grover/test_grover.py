import Grover as g

target = 74
nb_qubits = 7
algo = g.grover(nb_qubits, target)
result = g.get_result_with_noise(algo)

sorted_items = sorted(result.items(), key=lambda x: x[0])

g.plot_grover_results(sorted_items, target, nb_qubits)