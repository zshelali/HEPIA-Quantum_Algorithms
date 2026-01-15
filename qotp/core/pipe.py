from qiskit.visualization import plot_histogram
from qiskit import ClassicalRegister, QuantumCircuit
from rich.traceback import install
from copy import deepcopy
import os

from util import two_qubit_adder, to_standard, get_result_geneva

from .client import Client
from .server import Server

install()


def adder_pipe(a: int, b: int, debug_mode: bool = False):
    if not os.path.exists("./images"):
        os.makedirs("./images")
    # create server with two_qubit_adder, and client
    sv = Server(two_qubit_adder())
    cl = Client()

    # convert and store server circuit to standard
    filename = "./images/original_circuit.png"
    sv.circuit.draw("mpl", filename=filename, fold=-1)
    print(f"Circuit saved at {filename}")

    sv.circuit = to_standard(sv.circuit)

    filename = "./images/standardized_circuit.png"
    sv.circuit.draw("mpl", filename=filename, fold=-1)
    print(f"Circuit saved at {filename}")

    # encrypt x and y
    cipher_x = cl.encrypt(a, sv)
    offset = cipher_x.circuit.num_qubits
    cipher_y = cl.encrypt(b, sv, offset)

    # merge keys using the offset
    merged_keys = {}
    for i in range(cipher_x.circuit.num_qubits):
        merged_keys[i] = cipher_x.keys[i]
    for i in range(cipher_y.circuit.num_qubits):
        merged_keys[i + offset] = cipher_y.keys[i + offset]

    # update client's keys
    cl.keys = deepcopy(merged_keys)

    # add encrypted x,y states and the classical registers to the server circuit
    total_qubits = cipher_x.circuit.num_qubits + cipher_y.circuit.num_qubits

    final_circuit = QuantumCircuit(total_qubits + 1)  # +1 for dummy ancilla
    dummy_idx = total_qubits

    custom_gate = cipher_y.circuit ^ cipher_x.circuit
    # NOTE: is this necessary?
    custom_gate.name = "input gate"
    final_circuit.append(custom_gate, [k for k in range(total_qubits)])

    # the following lines fix a bug that caused a crash due to
    # registers having the same names when added automatically

    # --- FIX STARTS HERE --- (SOURCE: GOOGLE GEMINI)
    # 1. Track existing names to avoid "q" collision
    existing_q_names = {r.name for r in final_circuit.qregs}

    for qreg in sv.circuit.qregs:
        # Only add if a register with this NAME doesn't exist yet
        if qreg.name not in existing_q_names:
            final_circuit.add_register(qreg)
            existing_q_names.add(qreg.name)

    # 2. Do the same for Classical Registers
    existing_c_names = {r.name for r in final_circuit.cregs}

    for creg in sv.circuit.cregs:
        if creg.name not in existing_c_names:
            final_circuit.add_register(creg)
            existing_c_names.add(creg.name)
    # --- FIX ENDS HERE ---

    # creating and adding the measurement register to the final circuit
    meas_reg = ClassicalRegister(cipher_y.circuit.num_qubits, "meas")
    final_circuit.add_register(meas_reg)

    final_circuit.compose(
        sv.circuit,
        qubits=[k for k in range(total_qubits)],  # ancilla qubit omitted
        inplace=True,
    )

    if debug_mode:
        print(f"\nBefore update: {merged_keys}")

    # update keys routine according to the circuit in the server
    corrected_circuit = cl.update_key(
        server_qc=final_circuit, dummy_qubit_idx=dummy_idx, debug_mode=debug_mode
    )

    if debug_mode:
        print(f"After update: {cl.keys}")

    # measure end result
    corrected_circuit.measure(
        [k for k in range(offset, cipher_y.circuit.num_qubits + offset)], meas_reg
    )

    filename = "./images/final_circuit.png"
    corrected_circuit.draw("mpl", filename=filename, fold=-1)
    print(f"Circuit saved at {filename}")

    # fetch and decrypt measured result(s)
    result_counts = get_result_geneva(corrected_circuit)
    decrypted_counts = {}
    if debug_mode:
        print("counts:", result_counts)
    for bitstring, count in result_counts.items():
        decrypted_key = cl.decrypt(bitstring, offset=offset)
        decrypted_counts[decrypted_key] = count
    fig = plot_histogram(decrypted_counts)
    filename = "./images/histogram.png"
    fig.savefig(filename)
    print(f"Histogram saved at {filename}")
    return decrypted_counts
