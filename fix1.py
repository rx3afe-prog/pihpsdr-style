p = 'src/rx_panadapter.c'
s = open(p).read()

if 'pan_agc_knee_y' in s:
    print('rx_panadapter.c: патч уже стоит, ничего не делаю')
else:
    def ins(anchor, addition, tag):
        global s
        i = s.find(anchor)
        if i < 0:
            print('!! NE NAIDEN YAKOR:', tag)
            raise SystemExit(1)
        j = i + len(anchor)
        s = s[:j] + '\n' + addition + s[j:]
        print('OK:', tag)

    ins('#include "vfo.h"', '''
//
// Last drawn screen positions (pixels) of the AGC knee (G) and
// hang (H) lines, plus the scale (dB per pixel). Used by receiver.c
// to make these lines draggable with the mouse. -1 = not drawn.
//
int pan_agc_knee_y = -1;
int pan_agc_hang_y = -1;
int pan_agc_right_x = -1;
double pan_dbm_per_pixel = 0.0;
''', '1. peremennye')

    ins('  double dbm_per_line = (double)myheight / ((double)(panhi - panlo));',
        '  pan_dbm_per_pixel = (double)(panhi - panlo) / (double)myheight;',
        '2. masshtab shkaly')

    ins('''    double hang_y = rx->agc_hang + soffset;
    hang_y = floor((panhi - hang_y)
                   * (double) myheight
                   / (double) (panhi - panlo));''',
'''    //
    // Remember line positions for mouse dragging (receiver.c)
    //
    pan_agc_knee_y = (int) knee_y;
    pan_agc_hang_y = (rx->agc != AGC_MEDIUM && rx->agc != AGC_FAST)
                     ? (int) hang_y : -1;
    pan_agc_right_x = (int)mywidth - 40;''', '3. zapominanie liniy')

    ins('''      cairo_move_to(cr, 40.0, hang_y - 8.0);
      cairo_rectangle(cr, 40, hang_y - 8.0, 8.0, 8.0);
      cairo_fill(cr);''',
'''      cairo_rectangle(cr, mywidth - 48.0, hang_y - 8.0, 8.0, 8.0);
      cairo_fill(cr);''', '4. pravyy kubik H')

    ins('''    cairo_move_to(cr, 40.0, knee_y - 8.0);
    cairo_rectangle(cr, 40, knee_y - 8.0, 8.0, 8.0);
    cairo_fill(cr);''',
'''    cairo_rectangle(cr, mywidth - 48.0, knee_y - 8.0, 8.0, 8.0);
    cairo_fill(cr);''', '5. pravyy kubik G')

    open(p, 'w').write(s)
    print('rx_panadapter.c: vse pravki vneseny i sohraneny')

print()
print('=== receiver.c: svodka dlya Alisy ===')
r = open('src/receiver.c').read()
for token in ['agc_drag', 'pan_agc_knee_y', 'Grab an AGC line',
              'GDK_BUTTON_PRIMARY', 'drag_button', 'left_down',
              'scale_zone', 'PAN_SCALE_ZONE', 'pan_updown_drag',
              'rx_button_release_event']:
    lines = [str(n+1) for n, l in enumerate(r.splitlines()) if token in l]
    print(token + ': ' + (', '.join(lines) if lines else 'net'))

