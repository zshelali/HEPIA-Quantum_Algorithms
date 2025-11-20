import quantum_tools as qt
from qiskit import ClassicalRegister
from rich.traceback import install
from copy import deepcopy

from client import Client
from server import Server

install()
qt.init()


def adder_pipe(a, b):
    # create server with two_qubit_adder, and client
    sv = Server(qt.two_qubit_adder())
    cl = Client()

    # convert and store server circuit to standard
    qc_standard = qt.to_standard(sv.circuit)

    # encrypt x and y
    cipher_x = cl.encrypt(a, sv)
    offset = cipher_x.circuit.num_qubits
    cipher_y = cl.encrypt(b, sv, offset)

    # merge keys
    merged_keys = {}
    for i in range(cipher_x.circuit.num_qubits):
        merged_keys[i] = cipher_x.keys[i]
    for i in range(cipher_y.circuit.num_qubits):
        merged_keys[i + offset] = cipher_y.keys[i + offset]

    # update client's keys
    cl.keys = deepcopy(merged_keys)
    cl.update_key(qc_standard)
    print(f"\nBefore update: {merged_keys}")
    print(f"After update: {cl.keys}")

    # add encrypted x,y states and the classical registers to the server circuit
    cl_reg = ClassicalRegister(cipher_y.circuit.num_qubits)
    full_circuit = cipher_y.circuit ^ cipher_x.circuit
    full_circuit.add_register(cl_reg)
    full_circuit.append(
        sv.circuit,
        [_ for _ in range(full_circuit.num_qubits)],
        [_ for _ in range(sv.circuit.num_clbits)],
    )
    # measure end result
    full_circuit.measure(
        [k for k in range(offset, cipher_y.circuit.num_qubits + offset)], [0, 1]
    )

    # fetch and decrypt measured result
    result = qt.get_result(full_circuit)
    result_decrypted = cl.decrypt(result)

    print("Final result: ", result_decrypted)


adder_pipe(2, 0)
