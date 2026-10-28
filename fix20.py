p = '/home/rx3afe/piHPSDR-style/src/rx_panadapter.c'
r = open(p).read()

lines = r.split('\n')
keep = []
removed = 0
for ln in lines:
    if 'cairo_rectangle(cr, mywidth - 24.0,' in ln:
        removed += 1
        continue
    keep.append(ln)

if removed == 0:
    print('!! dubl-kubiki ne najdeny')
    raise SystemExit(1)

r2 = '\n'.join(keep)

if r2.count('{') != r2.count('}'):
    print('!! balans skobok narushen, nichego ne zapisano')
    raise SystemExit(1)

open(p, 'w').write(r2)
print('OK: ostalnye dubl-kubiki udaleny (%d)' % removed)

