import Shor as s

N = 39
p, q = s.shor_algorithm(N)
print(f"----------\n N:{N}, p:{p}, q: {q} p*q :{p*q}")