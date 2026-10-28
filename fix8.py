p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

if 'AGC: posle' in r:
    print('fix8 uzhe stoit, nichego ne delayu')
    raise SystemExit(0)

M = "        rx_set_agc(rx);\n\n        last_y = y;"

if M not in r:
    print('!! vysov rx_set_agc v vetke tyagi ne nayden')
    raise SystemExit(1)

G = ("        last_y = y;\n"
     "        fprintf(stderr, \"AGC: posle t=%.1f h=%.1f\\n\", rx->agc_thresh, rx->agc_hang);")

r = r.replace(M, G, 1)
open(p, 'w').write(r)
print('OK: rx_set_agc ubran iz tyagi, dobavlen otchet "posle"')

