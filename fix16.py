p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

M = 'sliders_agc_gain(GINT_TO_POINTER(100 + rx->id));'

if M not in r:
    print('!! vysov sliders_agc_gain(100+id) ne nayden')
    raise SystemExit(1)

r = r.replace(M, 'sliders_agc_gain(GINT_TO_POINTER(rx->id));', 1)

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, nichego ne zapisano')
    raise SystemExit(1)

open(p, 'w').write(r)
print('OK: teper pri tyage linii G polzunok ili dvigaetsya, ili poyavlyaetsya popup')

