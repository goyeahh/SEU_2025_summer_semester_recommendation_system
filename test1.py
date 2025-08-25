import numpy as np

for i in range(9):
    for j in range(i+1):
        print(f"{i+1} * {j+1} = {(i+1) * (j+1)}", end="\t")
    print()


def jiecheng(i):
    num = 1
    for j in range(i):
        num *= (j+1)
    return num

k = 4
print(f"{k}的阶乘：{jiecheng(k)}")