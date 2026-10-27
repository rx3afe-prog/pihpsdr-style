lines = open('rx_panadapter.c.zf2.bak', encoding='utf-8', errors='replace').read().splitlines(True)
m = next((i for i, ln in enumerate(lines) if 'ZFREQ' in ln), None)
if m is None:
    raise SystemExit('маркер ZFREQ не найден')
e = next((i for i in range(m, min(len(lines), m + 25)) if 'cairo_show_text' in lines[i]), None)
print('--- отключаемый блок (строки %d..%d):' % (m + 1, e + 1))
print(''.join(lines[m:e + 1]))
n = 0
for i in range(m, e + 1):
    s = lines[i].strip()
    if s and not s.startswith('//') and '{' not in s and '}' not in s:
        lines[i] = '//' + lines[i]; n += 1
open('rx_panadapter.c', 'w', encoding='utf-8').write(''.join(lines))
print('закомментировано строк:', n)
full = ''.join(lines)
print('баланс скобок: { =', full.count('{'), ' } =', full.count('}'))
