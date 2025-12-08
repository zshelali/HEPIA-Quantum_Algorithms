from numpy import full
import quantum_tools as qt
from qiskit import ClassicalRegister, QuantumCircuit
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
    sv.circuit = qt.to_standard(sv.circuit)

    # execute magic state distillation
    # keep a copy of the original circuit for the key updating routine
    old_circuit = deepcopy(sv.circuit)
    sv.magic_state_builder()

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
    print(f"\nBefore update: {merged_keys}")
    print(f"After update: {cl.keys}")

    # add encrypted x,y states and the classical registers to the server circuit
    custom_gate = cipher_y.circuit ^ cipher_x.circuit
    custom_gate.name = "bonsoir"
    final_circuit = QuantumCircuit(custom_gate.num_qubits)
    final_circuit.append(custom_gate, [k for k in range(4)])
    for qreg in sv.circuit.qregs:
        if qreg not in final_circuit.qregs:
            final_circuit.add_register(qreg)
    for creg in sv.circuit.cregs:
        if creg not in final_circuit.cregs:
            final_circuit.add_register(creg)

    cl_reg = ClassicalRegister(cipher_y.circuit.num_qubits, "meas")
    final_circuit.add_register(cl_reg)

    final_circuit.compose(sv.circuit, inplace=True)
    cl.update_key(final_circuit)

    # measure end result
    final_circuit.measure(
        [k for k in range(offset, cipher_y.circuit.num_qubits + offset)], cl_reg
    )
    # fetch and decrypt measured result(s)
    result_counts = qt.get_result(final_circuit)
    # result_decrypted = [cl.decrypt(result_counts[i]) for i in range(len(result_counts))]
    # print("Final result: ", result_decrypted)
    print("counts:", result_counts)
    old_circuit.draw("mpl", filename="./images/old_circuit.png", fold=-1)
    final_circuit.draw("mpl", filename="./images/final_circuit.png", fold=-1)

    print(final_circuit.data[0].name)


adder_pipe(0, 1)
