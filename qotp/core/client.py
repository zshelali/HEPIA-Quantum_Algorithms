from qiskit import QuantumCircuit
import random as random
import numpy as np

from util import is_t_gate, is_t_dg

from .ciphertext import Ciphertext
from .server import Server


class Client:
    def __init__(self):
        self.keys = {}

    def load_int(self, val: int) -> QuantumCircuit:
        """
        Loads an unencrypted integer into a circuit
        """
        bin_len = max(2, val.bit_length())
        val_bin = format(val, f"0{bin_len}b")[::-1]
        qc = QuantumCircuit(max(4, bin_len))
        for i, bit in enumerate(val_bin):
            if bit == "1":
                qc.x(i)
        return qc

    def encrypt(self, psi: int, server: Server, offset: int = 0) -> Ciphertext:
        """
        Returns Cipher(physical: QuantumCircuit, keys: dict)
        """
        bin_len = max(2, psi.bit_length())
        val_bin = format(psi, f"0{bin_len}b")[::-1]
        num_qubits = server.get_num_qubits()
        physical = QuantumCircuit(bin_len)
        keys = {}
        for i, bit in enumerate(val_bin):
            if bit == "1" and offset + i < num_qubits:
                physical.x(i)
        for k in range(num_qubits):
            a, b = random.randint(0, 1), random.randint(0, 1)
            keys[k] = (a, b)
        for i in range(bin_len):
            a, b = keys[i + offset]
            if a == 1:
                physical.x(i)
            if b == 1:
                physical.z(i)
        return Ciphertext(physical, keys)

    def decrypt(self, psi_tilde: str, offset: int = 0) -> str:
        """
        Decrypts a measured state.
        For a classical Z-basis measurement, only the X mask affects the outcome,
        as Z is only a phase that is invisible when measured.
        """
        res = []
        for i, bit in enumerate(psi_tilde[::-1]):
            a = self.keys[i + offset][0]
            decrypted_bit = str(a ^ int(bit))
            res.append(decrypted_bit)
        return "".join(res)[::-1]

    def update_key(
        self, server_qc: QuantumCircuit, dummy_qubit_idx: int, debug_mode: bool = False
    ) -> QuantumCircuit:
        """
        Updates QOTP private keys for circuits containing only Clifford gates.
        Handles: h, s (p), and cx gates.
        """
        names = []
        new_qc = QuantumCircuit(*server_qc.qregs, *server_qc.cregs)
        # print(f"Before update, current state:\n{self.keys}")
        for instruction in server_qc.data:
            op = instruction.operation
            qubits = instruction.qubits
            clbits = instruction.clbits
            q_indices = [server_qc.find_bit(q).index for q in qubits]
            new_qc.append(op, qubits, clbits)
            gate_name = op.name
            gate_params = op.params
            gate_theta = gate_params[0] if gate_params else 0
            names.append(gate_name)

            # -------------------- #
            #
            # CLIFFORD GATES
            #
            # -------------------- #

            # Hadamard gate
            if gate_name == "h":
                idx = q_indices[0]
                a, b = self.keys[idx]
                self.keys[idx] = b, a
                if debug_mode:
                    print(f"🟢 update key: encountered H gate at index {idx}\n\n")

            # CNOT gate
            elif gate_name == "cx":
                idx_1, idx_2 = q_indices[0], q_indices[1]
                ai, bi = self.keys[idx_1]
                aj, bj = self.keys[idx_2]
                self.keys[idx_1] = ai, bi ^ bj
                self.keys[idx_2] = ai ^ aj, bj
                if debug_mode:
                    print(
                        f"🟢 update key: encountered CNOT gate at indices control: {idx_1}, target = {idx_2}\n\n"
                    )

            # S or P gate / S_dg or P_dg
            elif gate_name == "p" and (
                np.isclose(gate_theta, np.pi / 2) or np.isclose(gate_theta, -np.pi / 2)
            ):
                idx = q_indices[0]
                a, b = self.keys[idx]
                self.keys[idx] = a, a ^ b
                if debug_mode:
                    print(
                        f"🟢 update key: encountered P({gate_theta}) gate (pi/2) or (-pi/2) at index {idx}\n\n"
                    )

            # -------------------- #
            #
            # NON-CLIFFORD GATES
            #
            # -------------------- #

            elif is_t_gate(op):
                idx = q_indices[0]
                a, b = self.keys[idx]

                needs_correction = a == 1
                if needs_correction:
                    target_qubit_idx = idx
                else:
                    target_qubit_idx = dummy_qubit_idx

                new_qc.s(target_qubit_idx)

                if needs_correction:
                    self.keys[idx] = (a, b ^ 1)

                if debug_mode:
                    print(
                        f"🔴 t gate at {idx}. a={a}. Correction applied to {target_qubit_idx}\n\n"
                    )

            elif is_t_dg(op):
                idx = q_indices[0]
                a, b = self.keys[idx]

                needs_correction = a == 1
                if needs_correction:
                    target_qubit_idx = idx
                else:
                    target_qubit_idx = dummy_qubit_idx

                new_qc.sdg(target_qubit_idx)

                if needs_correction:
                    self.keys[idx] = (a, b ^ 1)

                if debug_mode:
                    print(
                        f"🔴 tdg Gate at {idx}. a={a}. Correction applied to {target_qubit_idx}\n\n"
                    )

            else:
                if debug_mode:
                    print(
                        f"🟡 unverified gate encountered: {gate_name} theta={gate_theta}\n\n"
                    )
                continue

        if debug_mode:
            print("names: ", names)
        return new_qc
