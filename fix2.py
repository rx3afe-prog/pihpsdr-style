p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

if 'AGC_GRAB_ZONE' in r:
    print('receiver.c: AGC patch uzhe stoit, nichego ne delayu')
else:
    def rep(anchor, addition, tag):
        global r
        i = r.find(anchor)
        if i < 0:
            print('!! NE NAIDEN YAKOR:', tag)
            raise SystemExit(1)
        j = i + len(anchor)
        r = r[:j] + addition + r[j:]
        print('OK:', tag)

    rep('#include <math.h>', '''

//
// Screen positions (pixels) of the AGC knee (G) and hang (H) lines
// in the panadapter. Maintained by rx_panadapter.c, -1 = not drawn.
//
extern int pan_agc_knee_y;
extern int pan_agc_hang_y;
extern int pan_agc_right_x;
extern double pan_dbm_per_pixel;

// 0 = no AGC line drag, 1 = knee (G), 2 = hang (H)
static int agc_drag = 0;

// Grab distance in pixels around an AGC line
#define AGC_GRAB_ZONE 12
''', '1. peremennye')

    rep('''      drag_button = GDK_BUTTON_PRIMARY;
    } else if (event->button == GDK_BUTTON_SECONDARY) {''',
'''
      //
      // Grab an AGC line if the click is close to it, near the
      // handles at the left or right edge of the panadapter.
      //
      agc_drag = 0;

      if (from == 0
          && rx->agc != AGC_OFF
          && rx->agc != AGC_FIXED
          && (last_x <= 120
              || (pan_agc_right_x > 0
                  && last_x >= pan_agc_right_x - 80))) {
        int dk = last_y - pan_agc_knee_y;
        int dh = last_y - pan_agc_hang_y;

        if (dk < 0) { dk = -dk; }

        if (dh < 0) { dh = -dh; }

        if (pan_agc_knee_y >= 0 && dk <= AGC_GRAB_ZONE) {
          agc_drag = 1;
        } else if (pan_agc_hang_y >= 0 && dh <= AGC_GRAB_ZONE) {
          agc_drag = 2;
        }
      }
    } else if (event->button == GDK_BUTTON_SECONDARY) {''', '2. zakhvat linii pri nazhatii')

    rep('''  if (!making_active && pressed && button_down) {
    gdk_window_get_device_position (event->window,
                                    event->device,
                                    &x,
                                    &y,
                                    &state);
''',
'''
    //
    // Dragging an AGC line (G or H): adjust the value and skip
    // the usual VFO / scale handling.
    //
    if (agc_drag && from == 0) {
      int dyagc = y - last_y;

      if (dyagc != 0) {
        double ddb = (double)dyagc * pan_dbm_per_pixel;

        if (agc_drag == 1) {
          rx->agc_thresh -= ddb;

          if (rx->agc_thresh > 0.0) { rx->agc_thresh = 0.0; }

          if (rx->agc_thresh < -160.0) { rx->agc_thresh = -160.0; }
        } else {
          rx->agc_hang -= ddb;

          if (rx->agc_hang > rx->agc_thresh) { rx->agc_hang = rx->agc_thresh; }

          if (rx->agc_hang < -200.0) { rx->agc_hang = -200.0; }
        }
{AGC_UPDATE}
        last_y = y;
      }

      return TRUE;
    }
''', '3. peretaskivanie linii')

    rep('''  } else {
    if (pressed) {
      int x = (int)(event->x + 0.5);''',
'''  } else {
    if (pressed) {
      //
      // An AGC line drag ends here: do not treat it as a
      // VFO click or a scale drag.
      //
      if (agc_drag) {
        agc_drag = 0;
        pressed = FALSE;
        return TRUE;
      }

      int x = (int)(event->x + 0.5);''', '4. okonchanie peretaskivaniya')

    try:
        h = open('/home/rx3afe/piHPSDR-style/src/receiver.h').read()
    except Exception:
        h = ''

    if 'rx_agc_update' in h:
        r = r.replace('{AGC_UPDATE}', '        rx_agc_update(rx);')
        print('OK: 5. obnovlenie AGC cherez rx_agc_update')
    else:
        r = r.replace('{AGC_UPDATE}', '')
        print('OK: 5. rx_agc_update v header ne nayden - vyzov ne dobavlen')

    open(p, 'w').write(r)
    print('receiver.c: vse pravki vneseny i sohraneny')

