p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

ok = True

# 0. Est li GetRXAAGCTop v wdsp.h
h = open('/home/rx3afe/piHPSDR-style/wdsp/wdsp.h').read()
sync_gain = 'GetRXAAGCTop' in h
print('GetRXAAGCTop v wdsp.h:', 'est' if sync_gain else 'net')

gain_call = '\n          GetRXAAGCTop(rx->id, &rx->agc_gain);' if sync_gain else ''

# 1. Vetka tyagi: zamenyaem tselikom
start = r.find('if (agc_drag && from == 0) {')
if start < 0:
    print('!! nachalo vetki tyagi ne naydeno')
    ok = False
else:
    j = r.find('{', start)
    depth = 0
    k = j
    while k < len(r):
        if r[k] == '{':
            depth += 1
        elif r[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    old = r[start:k+1]
    print('vetka tyagi naydena: %d simvolov, fprintf v nej: %d' % (len(old), old.count('fprintf')))

    new = ('if (agc_drag && from == 0) {\n'
           '      int dyagc = y - last_y;\n'
           '\n'
           '      if (dyagc != 0) {\n'
           '        double ddb = (double)dyagc * pan_dbm_per_pixel;\n'
           '        int lo_dB = rx->panadapter_low + 2;\n'
           '        int hi_dB = rx->panadapter_high - 2;\n'
           '\n'
           '        if (agc_drag == 1) {\n'
           '          rx->agc_thresh -= ddb;\n'
           '\n'
           '          if (rx->agc_thresh > hi_dB) { rx->agc_thresh = hi_dB; }\n'
           '\n'
           '          if (rx->agc_thresh < lo_dB) { rx->agc_thresh = lo_dB; }\n'
           '\n'
           '          SetRXAAGCThresh(rx->id, rx->agc_thresh, (double)rx->afft_size, (double)rx->sample_rate);'
           + gain_call + '\n'
           '        } else {\n'
           '          rx->agc_hang -= ddb;\n'
           '\n'
           '          if (rx->agc_hang > hi_dB) { rx->agc_hang = hi_dB; }\n'
           '\n'
           '          if (rx->agc_hang < lo_dB) { rx->agc_hang = lo_dB; }\n'
           '\n'
           '          SetRXAAGCHangLevel(rx->id, rx->agc_hang);\n'
           '        }\n'
           '\n'
           '        last_y = y;\n'
           '      }\n'
           '\n'
           '      return TRUE;\n'
           '    }')

    r = r[:start] + new + r[k+1:]
    print('OK: vetka tyagi zamenena tselikom')

# 2. Blok otpuskaniya: zamenyaem tselikom
start2 = r.find('if (agc_drag) {')
if start2 < 0:
    print('!! blok otpuskaniya ne nayden')
    ok = False
else:
    j2 = r.find('{', start2)
    depth = 0
    k2 = j2
    while k2 < len(r):
        if r[k2] == '{':
            depth += 1
        elif r[k2] == '}':
            depth -= 1
            if depth == 0:
                break
        k2 += 1
    old2 = r[start2:k2+1]
    new2 = ('if (agc_drag) {\n'
            '        agc_drag = 0;\n'
            '        pressed = FALSE;\n'
            '        rx_save_state(rx);\n'
            '        return TRUE;\n'
            '      }')
    r = r[:start2] + new2 + r[k2+1:]
    print('OK: blok otpuskaniya zamenen (sohranenie pri otpuskanii)')

# 3. Ubrayem ostavshiesya otladochnye fprintf s "AGC:"
def strip_debug(text):
    out = []
    idx = 0
    removed = 0
    while True:
        f = text.find('fprintf(', idx)
        if f < 0:
            out.append(text[idx:])
            break
        if '"AGC:' in text[f:f+400]:
            e = text.find(');', f)
            if e < 0:
                out.append(text[idx:])
                break
            e2 = e + 2
            if e2 < len(text) and text[e2] == '\n':
                e2 += 1
            out.append(text[idx:f])
            removed += 1
            idx = e2
        else:
            out.append(text[idx:f+8])
            idx = f + 8
    return ''.join(out), removed

r, n = strip_debug(r)
print('udaleno otladochnykh fprintf:', n)

# 4. Proverka balansa skobok i zapis
if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, nichego ne zapisano')
    ok = False

if ok:
    open(p, 'w').write(r)
    print('receiver.c: chistovaya versiya zapisana')
else:
    print('nichego ne zapisano')

