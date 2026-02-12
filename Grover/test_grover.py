import Grover as g


# target and list 1:
my_list1 = [5, 12, 9, 74]
target1 = 74

algo1 = g.grover_arr(target1, my_list1)
result1 = g.get_result(algo1)

print(f"result1: {result1}")
# should print 3

# target and list 2:
my_list2 = [1, 100, 23, 2, 3, 85, 22]
target2 = 3

algo2 = g.grover_arr(target2, my_list2)
result2 = g.get_result(algo2)

print(f"result2: {result2}")
# should print 4
