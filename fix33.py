p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

old = '  int bym = vy + 2;'
new = '''  /* ZMHVFO: centriruem v Verhnej polose (stroka s krupnoj cifroj chastoty) */
  int bym = (vy - 22) / 2;
  if (bym < 4) { bym = 4; }'''

n = r.count(old)
if 'ZMHVFO' in r:
    print('OK: uzhe sdelano')
elif n >= 1:
    r = r.replace(old, new)
    print('OK: formula zamenena')
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

