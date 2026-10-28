# --- 1. receiver.c: argument vyzova dolzhen byt rx->id (bez 100+) ---
p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

old = 'sliders_agc_gain(GINT_TO_POINTER(100 + rx->id));'
new = 'sliders_agc_gain(GINT_TO_POINTER(rx->id));'

if old in r:
    r = r.replace(old, new, 1)
    open(p, 'w').write(r)
    print('1. OK: argument ispravlen (100+id -> id), zapisano')
elif new in r:
    print('1. OK: argument uzhe id, nichego ne delal')
else:
    print('1. !! vyzov sliders_agc_gain v receiver.c voobshe ne nayden')
    raise SystemExit(1)

# --- 2. sliders.c: vremennaya diagnostika ZSYNC ---
p2 = '/home/rx3afe/piHPSDR-style/src/sliders.c'
r2 = open(p2).read()

if 'ZSYNC' in r2:
    print('2. diagnostika uzhe stoit')
else:
    i = r2.find('int sliders_agc_gain(gpointer data) {')
    if i < 0:
        print('2. !! funkciya sliders_agc_gain ne naydena')
        raise SystemExit(1)
    j = r2.find('int id = val % 100;', i)
    if j < 0:
        print('2. !! stroka id ne naydena')
        raise SystemExit(1)
    e = r2.find('\n', j)
    diag = ('\n  fprintf(stderr, "ZSYNC: val=%d id=%d active=%d scale=%s gain=%.1f\\n",\n'
            '          val, id, active_receiver->id, agc_scale ? "da" : "net", receiver[id]->agc_gain);')
    r2 = r2[:e] + diag + r2[e:]
    open(p2, 'w').write(r2)
    print('2. OK: diagnostika ZSYNC dobavlena v sliders_agc_gain')

