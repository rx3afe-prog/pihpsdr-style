p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

old = '  int bym = vy + (vh - 22) / 2;'
new = '  int bym = vy + (vh - 22) / 2 - 12;  /* ZMHLIFT */'

if 'ZMHLIFT' in r:
    print('OK: uzhe sdelano')
elif r.count(old) >= 1:
    r = r.replace(old, new)
    print('OK: sdvig -12 dobavlen')
else:
    print('!! staryj blok ne najden'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

