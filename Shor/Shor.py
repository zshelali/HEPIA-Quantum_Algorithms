import random as rndm
from math import floor, log2, pi
from typing import List

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def check_parity(N: int) -> bool:
    """
    Vérifiez si un entier est pair. Si oui, il peut être directement factorisé par 2

    Steps
    ------
    1. Vérifier si N est divisible par 2
    2. Si oui, retourner True : 2 est un facteur de N
    3. Sinon, retourner False : N est impair

    Parameters
    ----------
    N : int
        Entier strictement supérieur à 2 à tester

    Returns
    -------
    bool
        True si N est pair (donc facteur 2 trouvé), False sinon
    """
    return N % 2 == 0


def miller_rabin(N: int) -> bool:
    """
    Test de primalité de Miller-Rabin (version probabiliste)

    Steps
    ------
    1. Écrire N - 1 sous la forme 2^r * d avec d impair
    2. Choisir un entier aléatoire a dans [2, N-2]
    3. Calculer x = a^d mod N.
    4. Si x == 1 ou x == N - 1, alors a n'est pas un témoin
    5. Répéter r - 1 fois :
        a. x ← x^d mod N
        b. Si x == N - 1, a n'est pas un témoin
    6. Si aucun test ne réussit, a est un témoin → N est composé

    Parameters
    ----------
    N : int
        Entier strictement supérieur à 2 à tester

    Returns
    -------
    bool
        True si N est composé, False s'il est probablement premier
    """
    if N < 2:
        return False
    if N == 2 or N == 3:
        return True
    # 1
    r = 0
    d = N - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    # 2
    a = rndm.randint(2, N - 2)
    # 3
    x = pow(a, d, N)
    # 4
    if x == 1 or x == N - 1:
        return True
    for _ in range(r - 1):
        x = pow(x, 2, N)
        if x == N - 1:
            return True
    return False


def is_power_of_prime(N: int) -> bool:
    """
    Vérifie si N est une puissance d'un entier premier : N = p^k avec k ≥ 2

    Steps
    ------
    1. Parcourir k de 2 à log2(N)
    2. Calculer p = N^(1/k) arrondi
    3. Vérifier si p^k == N

    Parameters
    ----------
    N : int
        Entier à tester

    Returns
    -------
    bool
        True si N est une puissance parfaite, False sinon
    """
    for k in range(2, floor(log2(N)) + 1):
        p = floor(pow(N, 1 / k))
        for q in (p - 1, p, p + 1):
            if pow(q, k) == N:  # and miller_rabin(q)
                return True
    return False


def oracle(n: int, m: int, precomputed_value: List[int]) -> QuantumCircuit:
    """
    Implémente un oracle quantique à partir d'une table de valeurs pré-calculées : f(k) = a^k mod N

    Steps
    ------
    1. Créer deux registres quantiques :
        - Registre de contrôle `O1` (taille n qubits, index k)
        - Registre cible `O2` (taille m qubits, pour stocker a^k mod N)

    2. Pour chaque valeur k de la table :
        a. Convertir l'index du tableau (k) en binaire (sur n bits)
        b. Convertir la valeur du tableau en binaire (sur m bits)
        c. Appliquer une porte X sur les qubits de `O1` correspondant aux bits à 0 (préparation pour le contrôle)
        d. Pour chaque bit 1 dans la valeur du tableau :
            - Appliquer une porte MCX (multi-controlled-X) depuis tous les qubits de `O1` vers le bit cible de `O2`
        d. Réinitialiser les qubits de `O1` modifiés (retour à l'état initial)

    Parameters
    ----------
    n : int
        Nombre de qubits dans le registre d'entrée (registre k)

    m : int
        Nombre de qubits nécessaires pour stocker les résultats a^k mod N

    precomputed_value : List[int]
        Liste contenant les résultats a^k mod N pour chaque k de 0 à 2^n - 1

    Returns
    -------
    QuantumCircuit
        Le circuit quantique implémentant l'oracle.
    """

    O = QuantumCircuit(n + m)
    O.name = "Oracle"
    for i, val in enumerate(precomputed_value):
        k_bin = format(i, f"0{n}b")
        val_bin = format(val, f"0{m}b")
        for qubit, bit in enumerate(k_bin):
            if bit == "0":
                O.x(qubit)
        for qubit, bit in enumerate(val_bin):
            if bit == "1":
                O.mcx(list(range(n)), n + qubit)

        for qubit, bit in enumerate(k_bin):
            if bit == "0":
                O.x(qubit)
    return O


def qft(n, inverse=False) -> QuantumCircuit:
    """
    Transformée de Fourier Quantique (QFT) factorisée

    Steps
    ------
    1. Parcourir les qubits du plus à droite (index le plus élevé) au plus à gauche
    2. Pour chaque qubit courant :
        a. Appliquer une porte Hadamard pour créer une superposition
        b. Appliquer une série de portes de phase contrôlées (CP) entre le qubit courant (contrôle) et les qubits plus à gauche (cibles)
           - L'angle de phase est donné par : 2π / 2^d, avec d = distance entre les qubits

    Parameters
    ----------
    n : int
        Nombre de qubits sur lesquels appliquer la QFT

    Returns
    -------
    QuantumCircuit
        Le circuit quantique avec la QFT appliquée
    """
    qc = QuantumCircuit(n)
    qc.name = "QFTn"
    for i in range(n - 1, -1, -1):
        qc.h(i)
        for j in range(i - 1, -1, -1):
            d = i - j + 1
            qc.cp((2 * pi) / (pow(2, d)), i, j)

    for k in range(n // 2):
        qc.swap(k, n - k - 1)

    if inverse == True:
        return qc.inverse()

    return qc


def continued_fraction_expansion(a: int, b: int) -> list[int]:
    """
    Développe la fraction a/b en fraction continue

    Steps
    ------
    1. Réaliser des divisions euclidiennes successives
    2. Stocker les quotients dans une liste
    3. Terminer quand le reste devient 0

    Parameters
    ----------
    a : int
        Numérateur.
    b : int
        Dénominateur.

    Returns
    -------
    list of int
        Liste des quotients de la fraction continue
    """
    results = []

    q = a // b
    r = a % b
    results.append(q)
    while r > 0:
        a = b
        b = r
        q = a // b
        r = a % b
        results.append(q)

    return results


def convergents_from_cf(cf: list[int]) -> list[tuple[int, int]]:
    """
    Calcule les convergents associés à une fraction continue

    Steps
    ------
    1. Pour chaque sous-liste [a0], [a0, a1], ..., [a0, ..., an] :
        a. Appliquer la récurrence inverse :
           num, den = den + q * num, num
    2. Stocker les couples (numérateur, dénominateur)

    Parameters
    ----------
    cf : list of int
        Liste des quotients de la fraction continue

    Returns
    -------
    list of tuple of int
        Liste des convergents (numérateur, dénominateur)
    """
    res = []

    p2, q2 = 0, 1
    p1, q1 = 1, 0
    p, q = 0, 0
    for a in cf:
        p = a * p1 + p2
        q = a * q1 + q2
        res.append((p, q))
        p2, q2 = p1, q1
        p1, q1 = p, q

    return res


def gcd(a: int, b: int) -> int:
    """
    Calcule le plus grand commun diviseur (PGCD) de deux entiers

    Steps
    ------
    1. Répéter tant que b ≠ 0 :
       a ← b, b ← a mod b
    2. Retourner a

    Parameters
    ----------
    a : int
        Premier entier
    b : int
        Deuxième entier

    Returns
    -------
    int
        Le PGCD de a et b
    """
    if a % b == 0:
        return b
    return gcd(b, a % b)


def recover_factors_from_r(convergents, a, N):
    """
    Récupérez les facteurs de N à partir des convergents associés à la période r

    Steps
    ------
    1. Parcourir les convergents (s, r) issus de la fraction continue
    2. Ne garder que les r pairs (condition nécessaire pour le calcul de a^{r/2})
    3. Calculer v = a^{r/2}
    4. Calculer deux candidats :
       - t1 = gcd(v + 1, N)
       - t2 = gcd(v - 1, N)
    5. Si t1 × t2 == N et t1, t2 sont non triviaux (≠ 1 et ≠ N), on retourne les facteurs

    Parameters
    ----------
    convergents : List[Tuple[int, int]]
        Convergents (s, r) issus de l'expansion en fraction continue

    a : int
        Base utilisée dans la fonction modulaire f(k) = a^k mod N

    N : int
        Entier à factoriser

    Returns
    -------
    Tuple[int, int] or Tuple[None, None]
        Deux facteurs non triviaux de N si trouvés, sinon None
    """
    pair_r_convergents = []
    for c in convergents:
        if c[1] % 2 == 0:
            pair_r_convergents.append(c)
    for p in pair_r_convergents:
        v = pow(a, p[1] // 2)
        t1 = gcd(v + 1, N)
        t2 = gcd(v - 1, N)
        if t1 * t2 == N and t1 != 1 and t2 != 1 and t1 != N and t2 != N:
            return t1, t2


def quantum_shor_algorithm(
    q: int, n: int, m: int, a: int, precalculated_values: List[int]
) -> QuantumCircuit:
    """
    Implémente la partie quantique de l'algorithme de Shor.
    Utilise la fonction get_result pour exécuter le circuit quantique

    Steps
    ------
    1. Préparer deux registres quantiques :
       - `R1` (n qubits) pour la superposition des entrées `k`
       - `R2` (m qubits) pour stocker le résultat `a^k mod N`

    2. Appliquer une superposition Hadamard sur `R1`

    3. Appliquer l'oracle quantique qui encode la fonction `f(k) = a^k mod N`

    4. Appliquer la QFT inverse sur `R1` pour extraire l'information de période

    5. Mesurer les qubits de `R1`

    Parameters
    ----------
    q : int
        L'entier à factoriser (N), utilisé seulement dans la partie classique

    n : int
        Nombre de qubits dans le registre d'entrée `R1`

    m : int
        Nombre de qubits dans le registre de sortie `R2`

    a : int
        Valeur de la base choisie pour la fonction modulaire f(k) = a^k mod N

    precalculated_values : List[int]
        Résultats classiques de a^k mod N pour chaque k dans [0, 2^n - 1]

    Returns
    -------
    int
        Le résultat brut mesuré (en entier), à convertir en fraction s/r ensuite
    """
    # Registres quantiques et classique
    R = QuantumCircuit(n + m, n)
    qft_n = qft(n, inverse=True)

    # Hadamard for superposition
    for i in range(n):
        R.h(i)

    # Oracle
    orac = oracle(n, m, precalculated_values)
    R.append(orac, range(n + m))

    # QFT dagger
    R.append(qft_n, range(n))

    # Measure
    for i in range(n):
        R.measure(i, i)

    return R


def shor_algorithm(N) -> tuple[int, int]:
    """
    Implémente l'algorithme complet de Shor (quantique + classique)

    Steps
    ------
    1. Vérifier si N est pair, premier ou une puissance d'un seul facteur (cas triviaux à exclure)
    2. Choisir une précision q telle que N^2 =< q < 2N^2, et calculer :
       a. n = ⌈log2(q)⌉ (nombre de qubits pour le registre d'entrée)
       b. m = ⌈log2(N)⌉ (nombre de qubits pour le registre de sortie)
    3. Tant qu'aucune factorisation n'est trouvée :
       a. Choisir une base a aléatoire dans [2, N - 1] telle que gcd(a, N) = 1
       b. Pré-calculer les valeurs de f(k) = a^k mod N pour k dans [0, 2^n - 1]
       c. Construire et exécuter le circuit quantique avec q, n, m, a
       d. Récupérer les deux mesures les plus probables (en ignorant `000...0`)
       e. Convertir le résultat en fraction s/r à l'aide des fractions continues
       f. Extraire les convergents et tester ceux qui sont pairs
       g. Calculer gcd(a^{r/2} ± 1, N). Si les facteurs trouvés sont non triviaux, les retourner

    Parameters
    ----------
    N : int
        L'entier à factoriser

    Returns
    -------
    Tuple[int, int]
        Deux facteurs non triviaux de N
    """
    if check_parity(N) or miller_rabin(N) or is_power_of_prime(N):
        return (-1, -1)
    m = N.bit_length()
    q = 2 ** (2 * m)
    n = floor(log2(q))
    Q = 2**n
    simulator = AerSimulator()

    found_factors = False

    while True:
        a = rndm.randint(2, N - 1)
        while gcd(a, N) != 1:
            a = rndm.randint(2, N - 1)
        pfc = quantum_shor_algorithm(
            q, n, m, a, [pow(a, k, N) for k in range(2**n)]
        )  # pfc = period finding circuit
        circ = transpile(pfc, simulator)
        result = simulator.run(circ).result()
        counts = result.get_counts(circ)
        for k in sorted(counts, key=counts.get, reverse=True)[:5]:
            if k == "0" * n:
                continue
            s = int(k[::-1], 2)
            frac = continued_fraction_expansion(s, Q)
            conv = convergents_from_cf(frac)
            factors = recover_factors_from_r(conv, a, N)
            if factors:
                return factors

    return factors
