from numpy import pi
from qiskit import QuantumCircuit


def random_circuit() -> QuantumCircuit:
    """
    Visualize circuit @
    https://algassert.com/quirk#circuit={%22cols%22:[[%22X%22,1,%22H%22],[%22%E2%80%A2%22,1,1,%22X%22],[1,1,1,%22X%22],[1,1,%22H%22],[%22Measure%22,%22Measure%22,%22Measure%22,%22Measure%22],[%22Chance4%22]],%22init%22:[1,0,1]}
    """
    qc = QuantumCircuit(4)
    qc.name = "Server circuit"
    qc.x(0)
    qc.h(2)
    qc.cx(0, 3)
    qc.x(3)
    qc.h(2)
    return qc


def qft(n, swap=True, inverse=False) -> QuantumCircuit:
    """
    Build a Quantum Fourier Transform (QFT) circuit.
    The `inverse=False` here is qiskit's `inverse=True`.

    Args:
        n (int): Number of qubits.
        swap (bool): If True, add final swap gates to reverse qubit order
            (standard QFT layout). If False, output is in bit-reversed order.
        inverse (bool): If True, construct the inverse QFT (IQFT) by using
            negative phase angles.

    Returns:
        QuantumCircuit: Qiskit QuantumCircuit implementing the QFT or IQFT
        on n qubits.

    Example:
        >>> qft(2, inverse=False).draw(output="mpl", filename="my_qft.png", fold=False)

    """
    qc = QuantumCircuit(n)
    qc.name = "QFT"
    for current in range(n):
        qc.barrier()
        qc.h(current)
        for others in range(current + 1, n):
            qc.cp(
                theta=-2 * pi / 2 ** (others - current + 1),
                control_qubit=others,
                target_qubit=current,
            )

    if swap:
        for j in range(n // 2):
            qc.swap(j, n - 1 - j)

    if inverse:
        inverted_qc = qc.inverse()
        return inverted_qc

    return qc


def two_qubit_adder() -> QuantumCircuit:
    # TODO: universalize the function to take n odd and even.
    n = 4
    qc = QuantumCircuit(4)
    # qc.append(x, [0, 1])
    # qc.append(y, [2, 3])
    qc.append(qft(2, inverse=True, swap=False), [2, 3])

    for i in range(n):
        for j in range(i + 2, n):
            theta = 2 ** (i) * pi / (2 ** (j - (n // 2)))
            qc.cp(theta=theta, control_qubit=i, target_qubit=j)
    qc.append(qft(2, inverse=False, swap=False), [2, 3])

    # qc.measure([2, 3], [0, 1])
    return qc
