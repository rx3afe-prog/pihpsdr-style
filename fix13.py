ok = True

# --- 1. receiver.c: синхронизация ручки AGC Gain с линией G ---
p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

M = 'SetRXAAGCThresh(rx->id, rx->agc_thresh, (double)rx->afft_size, (double)rx->sample_rate);'

if 'GetRXAAGCTop' in r:
    print('receiver.c: vysov GetRXAAGCTop uzhe est')
else:
    if M in r:
        G = (M + '\n'
             '          {\n'
             '            extern void GetRXAAGCTop(int channel, double *max_agc);\n'
             '            GetRXAAGCTop(rx->id, &rx->agc_gain);\n'
             '          }')
        r = r.replace(M, G, 1)
        print('OK: rx->agc_gain teper chitaetsya obratno iz DSP posle tyagi linii G')
    else:
        print('!! vysov SetRXAAGCThresh v receiver.c ne nayden')
        ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, nichego ne zapisano')
    ok = False

if ok:
    open(p, 'w').write(r)

# --- 2. rx_panadapter.c: bukvy G i H sprava ot pravykh kubikov ---
p2 = '/home/rx3afe/piHPSDR-style/src/rx_panadapter.c'
r2 = open(p2).read()

if 'ZAGC_LABEL' in r2:
    print('rx_panadapter.c: bukvy uzhe stoit')
else:
    n = 0
    for var, letter in (('hang', 'H'), ('knee', 'G')):
        pat = 'cairo_rectangle(cr, mywidth - 48.0, %s_y - 8.0, 8.0, 8.0);' % var
        if pat in r2:
            ins = (pat + '\n'
                   '      cairo_save(cr);\n'
                   '      cairo_set_source_rgba(cr, COLOUR_ATTN);\n'
                   '      cairo_select_font_face(cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);\n'
                   '      cairo_set_font_size(cr, 14.0);\n'
                   '      cairo_move_to(cr, (double)mywidth - 36.0, %s_y + 5.0);\n'
                   '      cairo_show_text(cr, "%s");\n'
                   '      cairo_restore(cr);') % (var, letter)
            r2 = r2.replace(pat, ins, 1)
            print('OK: bukva %s dobavlena (pravyi kubik linii %s)' % (letter, letter))
            n += 1
        else:
            print('!! pravyi kubik linii %s ne nayden (pat: %s)' % (letter, pat))

    if r2.count('{') != r2.count('}'):
        print('!! balans skobok narushen v rx_panadapter.c, nichego ne zapisano')
        ok = False
    elif n > 0:
        open(p2, 'w').write(r2)
        print('rx_panadapter.c: zapisano')

