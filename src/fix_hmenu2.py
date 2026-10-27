s = open('main.c', encoding='utf-8').read()
old = 'f / 1000000LL, (f / 1000LL) % 1000LL, f % 1000LL, hfreq_tail_hex);'
new = 'f / 1000000LL, (f / 1000LL) % 1000LL, hfreq_tail_hex, f % 1000LL);'
assert old in s, 'якорь не найден'
s = s.replace(old, new, 1)
open('main.c', 'w', encoding='utf-8').write(s)
print('порядок аргументов исправлен')
