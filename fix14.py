p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

if 'sliders_agc_gain' in r:
    print('vysov sliders_agc_gain uzhe est, nichego ne delayu')
    raise SystemExit(0)

M = '''            extern void GetRXAAGCTop(int channel, double *max_agc);
            GetRXAAGCTop(rx->id, &rx->agc_gain);'''

if M not in r:
    print('!! blok GetRXAAGCTop ne nayden (fix13 zapushchen?)')
    raise SystemExit(1)

G = M + '''
            extern int sliders_agc_gain(gpointer data);
            sliders_agc_gain(GINT_TO_POINTER(100 + rx->id));'''

r = r.replace(M, G, 1)

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, nichego ne zapisano')
    raise SystemExit(1)

open(p, 'w').write(r)
print('OK: polzunok AGC Gain teper edet za liniej G')
p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

M = '''          SetRXAAGCThresh(rx->id, rx->agc_thresh, (double)rx->afft_size, (double)rx->sample_rate);'''

if M not in r:
    print('!! osnovnoy blok SetRXAAGCThresh ne nayden')
    raise SystemExit(1)

# Проверяем, есть ли уже наш вызов
if 'sliders_agc_gain' in r:
    print('vysov sliders_agc_gain uzhe est, nichego ne delayu')
    raise SystemExit(0)

# Формируем новый блок с вызовом
G = (M + '\n'
     '          {\n'
     '            extern void GetRXAAGCTop(int channel, double *max_agc);\n'
     '            GetRXAAGCTop(rx->id, &rx->agc_gain);\n'
     '            extern int sliders_agc_gain(gpointer data);\n'
     '            sliders_agc_gain(GINT_TO_POINTER(100 + rx->id));\n'
     '          }')

r = r.replace(M, G, 1)

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, nichego ne zapisano')
    raise SystemExit(1)

open(p, 'w').write(r)
print('OK: polzunok AGC Gain teper edet za liniej G')

