confusion = {}
confusion[1] = 1
confusion['1'] = 2
confusion[1] += 1

print(confusion)
sum = 0
for k in confusion:
    print('sum:', sum)
    print(k)
    print('dict:',confusion[k])
    sum += confusion[k]

print(sum)