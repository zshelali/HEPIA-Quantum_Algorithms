from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, AncillaRegister
from qiskit.circuit import CircuitInstruction
from qiskit.circuit.library import TGate, TdgGate, CXGate, Measure, SdgGate
import numpy as np
import warnings

import quantum_tools as qt


class Server:
    def __init__(self, circuit: QuantumCircuit):
        self.circuit = circuit
        self.num_qubits = circuit.num_qubits

    def get_num_qubits(self) -> int:
        return self.num_qubits

    def populate_magic_state(self, qc: QuantumCircuit, curr_idx: int, dg: bool) -> None:
        # add needed regiters
        ancilla = AncillaRegister(1, f"ancilla_{len(qc.ancillas)}")
        cr = ClassicalRegister(1, f"c_magic{len(qc.cregs)}")
        qc.add_register(ancilla)
        qc.add_register(cr)

        # ancilla = T|+>
        qc.h(ancilla[0])
        if dg:
            qc.tdg(ancilla[0])
        else:
            qc.t(ancilla[0])

        # CNOT with control=current, target=ancilla
        qc.cx(curr_idx, ancilla[0])
        qc.measure(ancilla[0], cr[0])

        # if m = 0
        if dg:
            qc.sdg(curr_idx).c_if(cr, 0)
        else:
            qc.s(curr_idx).c_if(cr, 0)

        #if m = 1
        qc.x(curr_idx).c_if(cr, 1)
        if dg:
            qc.sdg(curr_idx).c_if(cr, 1)
        else:
            qc.s(curr_idx).c_if(cr, 1)
        qc.barrier()

        # # put the new result back in the data qubit
        # qc.swap(curr_idx, ancilla[0])

    def populate_clifford_state(self, qc: QuantumCircuit, curr_idx: int | list[int], curr_instr) -> None:
        """
        Adds a Clifford state to the server circuit
        """
        name = curr_instr.name
        gate = getattr(qc, name)
        params = curr_instr.params
        if name in ["barrier", "measure"]:
            return

        if isinstance(curr_idx, list):
            if params:
                gate(*params, *curr_idx)
            else:
                gate(*curr_idx)
        else:
            if params:
                gate(*params, curr_idx)
            else:
                gate(curr_idx)
        qc.barrier()


    def magic_state_builder(self) -> None:
       # new_circ = QuantumCircuit(self.circuit.num_qubits)
        new_circ = QuantumCircuit(*self.circuit.qregs, *self.circuit.cregs)

        if not qt.has_t_gates(self.circuit):
            warnings.warn("no T gate in this circuit", UserWarning)
            return

        for instruction in self.circuit.data:
            is_t = qt.is_t_gate(instruction)
            is_t_dg = qt.is_t_dg(instruction)

            idx = qt.get_qubit_index(self.circuit, instruction)

            if is_t or is_t_dg:
                if not isinstance(idx, int):
                    raise TypeError(f"expected int, got {type(idx)}")
                self.populate_magic_state(new_circ, idx, is_t_dg)
            else:
                self.populate_clifford_state(new_circ, idx, instruction)

        self.circuit = new_circ


