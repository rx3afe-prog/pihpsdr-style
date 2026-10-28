# --- 1. receiver.c: stoit li vyzov obnovleniya polzunka ---
p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

if 'sliders_agc_gain' in r:
    print('1. OK: vyzov sliders_agc_gain uzhe stoit')
else:
    lines = r.split('\n')
    at = -1
    for i, ln in enumerate(lines):
        if 'GetRXAAGCTop(rx->id' in ln:
            at = i
            break
    if at < 0:
        for i, ln in enumerate(lines):
            if 'SetRXAAGCThresh(rx->id' in ln:
                at = i
                break
    if at < 0:
        print('1. !! ne naydeno mesto dlya vstavki')
        raise SystemExit(1)
    ins = ['            extern int sliders_agc_gain(gpointer data);',
           '            sliders_agc_gain(GINT_TO_POINTER(100 + rx->id));']
    lines = lines[:at + 1] + ins + lines[at + 1:]
    r2 = '\n'.join(lines)
    if r2.count('{') != r2.count('}'):
        print('1. !! balans skobok narushen, nichego ne zapisano')
        raise SystemExit(1)
    open(p, 'w').write(r2)
    print('1. OK: vyzov obnovleniya polzunka vstavlen posle stroki %d' % (at + 1))

# --- 2. rx_panadapter.c: dubl-kubik ryadom s bukvoj ---
p2 = '/home/rx3afe/piHPSDR-style/src/rx_panadapter.c'
r2 = open(p2).read()

if 'ZAGC_DUP' in r2:
    print('2. dubl-kubiki uzhe narlisovany')
else:
    n = 0
    for var in ('hang', 'knee'):
        pat = 'cairo_rectangle(cr, mywidth - 48.0, %s_y - 8.0, 8.0, 8.0);' % var
        if pat in r2:
            r2 = r2.replace(pat, pat + '\n      // ZAGC_DUP: vtoroi kubik ryadom s bukvoj\n      cairo_rectangle(cr, mywidth - 24.0, %s_y - 8.0, 8.0, 8.0);' % var, 1)
            n += 1
        else:
            print('2. !! osnovnoy kubik linii %s ne nayden' % var)
    if r2.count('{') != r2.count('}'):
        print('2. !! balans skobok v rx_panadapter.c, nichego ne zapisano')
        raise SystemExit(1)
    if n:
        open(p2, 'w').write(r2)
        print('2. OK: dubl-kubiki narlisovany (%d)' % n)

