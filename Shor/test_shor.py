import Shor as shr

N = 39
p, q = shr.shor_algorithm(N)
print(f"----------\n N:{N}, p:{p}, q: {q} p*q :{p*q}")