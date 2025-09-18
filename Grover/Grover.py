
import matplotlib.pyplot as plt
import random as rndm
import numpy as np
import random as rndm
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit import transpile
from qiskit.circuit.library import RealAmplitudes
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_state_city, plot_state_hinton
from typing import List
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
from math import floor, log2, pi, ceil, sqrt


def get_result(qc):
    simulator = AerSimulator()
    compiled = transpile(qc, simulator)
    return simulator.run(compiled, shots=100).result().get_counts()


def get_result_with_noise(qc):
    # https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models
    error = depolarizing_error(1e-3, 1)  # (errreur qubit,nombre de qubit impacté)
    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(
        error,
        [
            "x",
            "h",
            "z",
        ],
    )
    simulator = AerSimulator(noise_model=noise_model)
    compiled = transpile(qc, simulator)
    return simulator.run(compiled, shots=100).result().get_counts()


def plot_grover_results(sorted_items, target, nb_qubits):
    # qiskit = little endian
    states = [item[0] for item in sorted_items]
    counts = [item[1] for item in sorted_items]
    colors = [
        "tab:red" if s == format(target, f"0{nb_qubits}b") else "tab:blue"
        for s in states
    ]
    plt.figure(figsize=(14, 6))
    plt.bar(states, counts, color=colors)
    plt.xticks(states, rotation=90, fontsize=8)

    plt.xlabel("États mesurés")
    plt.ylabel("Occurrences")
    plt.title("Distribution des résultats de Grover")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()


def oracle(nb_qubits: int, value: int) -> QuantumCircuit:
    """
    Implémentez un oracle quantique simple qui marque un état cible en inversant sa phase.

    Étapes
    ------
    1. Convertir la valeur cible en binaire sur nb_qubits bits.
    2. Appliquer une porte X sur les qubits dont le bit correspondant vaut 0
       afin de préparer l'état de contrôle où tous les qubits sont à |1⟩.
    3. Appliquer une porte Z contrôlée sur l'état cible :
       a. Convertir Z en H–X–H sur le premier qubit pour inverser la phase.
       b. Utiliser une porte MCX contrôlée par les autres qubits sur le premier.
    4. Annuler les portes X appliquées à l'étape 2 pour revenir à l'état initial.

    Parameters
    ----------
    nb_qubits : int
        Nombre total de qubits dans le registre.
    value : int
        Valeur cible à marquer, encodée sur nb_qubits bits.

    Returns
    -------
    QuantumCircuit
        Circuit quantique représentant l'oracle, avec un contrôle de phase
        appliqué uniquement sur l'état cible.
    """
    qc = QuantumCircuit(nb_qubits)
    val_bin = format(value, f"0{nb_qubits}b")

    qc.barrier()
    for i, bit in enumerate(reversed(val_bin)):
        if bit == "0":
            qc.x(i)

    qc.h(nb_qubits - 1)
    if nb_qubits == 1:
        qc.z(nb_qubits - 1)
    else:
        qc.mcx([k for k in range(nb_qubits - 1)], nb_qubits - 1)
    qc.h(nb_qubits - 1)

    for i, bit in enumerate(reversed(val_bin)):
        if bit == "0":
            qc.x(i)
    qc.barrier()

    return qc

def diffusion(nb_qubits):
    """
    Implémentez l'opérateur de diffusion utilisé dans l'algorithme de Grover.

    L'opérateur de diffusion applique une inversion par rapport à la moyenne
    des amplitudes, ce qui augmente la probabilité de l'état marqué par l'oracle
    et diminue celle des autres états.

    Étapes
    ------
    1. Appliquer une porte Hadamard sur tous les qubits pour passer en base de Fourier.
    2. Appliquer une porte X sur tous les qubits pour inverser les états.
    3. Appliquer une inversion de phase sur l'état |00...0⟩ (index 0) :
       a. Appliquer une porte H sur le premier qubit.
       b. Appliquer une porte MCX contrôlée par les autres qubits vers le premier.
       c. Appliquer une porte H sur le premier qubit.
    4. Annuler les portes X appliquées à l'étape 2.
    5. Appliquer une porte Hadamard sur tous les qubits pour revenir à la base initiale.

    Parameters
    ----------
    nb_qubits : int
        Nombre total de qubits du registre.

    Returns
    -------
    QuantumCircuit
        Circuit quantique correspondant à l'opérateur de diffusion.
    """
    qc = QuantumCircuit(nb_qubits)

    for i in range(nb_qubits):
        qc.h(i)
        qc.x(i)

    qc.h(nb_qubits - 1)
    if nb_qubits == 1:
        qc.z(nb_qubits - 1)
    else:
        qc.mcx([k for k in range(nb_qubits - 1)], nb_qubits - 1)
    qc.h(nb_qubits - 1)

    for i in range(nb_qubits):
        qc.x(i)
        qc.h(i)

    return qc


def grover(nb_qubits: int, x: int):
    """
    Implémentez l’algorithme de Grover pour rechercher un élément marqué.

    Steps
    ------
    1. Initialiser un registre de `nb_qubits` dans une superposition uniforme.
    2. Calculer le nombre optimal d’itérations : k = ⌈(π/4) * √N⌉, où N = 2^nb_qubits.
    3. Construire l’oracle qui inverse la phase de l’état marqué |x⟩.
    4. Construire l’opérateur de diffusion qui amplifie la probabilité de l’état marqué.
    5. Répéter k fois :
       a. Appliquer l’oracle.
       b. Appliquer la diffusion.
    6. Mesurer tous les qubits.

    Parameters
    ----------
    nb_qubits : int
        Nombre de qubits du registre (détermine la taille de l’espace de recherche).
    x : int
        Valeur cible (état marqué) à rechercher.

    Returns
    -------
    QuantumCircuit
        Circuit quantique complet de l’algorithme de Grover.
    """
    qc = QuantumCircuit(nb_qubits)
    for i in range(nb_qubits):
        qc.h(i)
    k = floor((pi / 4) * sqrt(pow(2, nb_qubits)))  # optimal amount of operations
    qc_oracle = oracle(nb_qubits, x)
    qc_diffusion = diffusion(nb_qubits)
    for j in range(k):
        qc.append(qc_oracle, range(nb_qubits))
        qc.append(qc_diffusion, range(nb_qubits))

    qc.measure_all()

    return qc
