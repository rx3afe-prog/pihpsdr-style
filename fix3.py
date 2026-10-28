p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

M2 = """      drag_button = GDK_BUTTON_PRIMARY;
    } else if (event->button == GDK_BUTTON_SECONDARY) {
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
    } else if (event->button == GDK_BUTTON_SECONDARY) {"""

G2 = """      drag_button = GDK_BUTTON_PRIMARY;
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
    } else if (event->button == GDK_BUTTON_SECONDARY) {"""

if M2 in r:
    r = r.replace(M2, G2, 1)
    print('OK: blok 2 ispravlen')
elif G2 in r:
    print('blok 2 uzhe ispravlen')
else:
    print('!! blok 2 ne nayden')

M4 = """      int x = (int)(event->x + 0.5);  } else {
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

      int x = (int)(event->x + 0.5);"""

G4 = """      //
      // An AGC line drag ends here: do not treat it as a
      // VFO click or a scale drag.
      //
      if (agc_drag) {
        agc_drag = 0;
        pressed = FALSE;
        return TRUE;
      }

      int x = (int)(event->x + 0.5);"""

if M4 in r:
    r = r.replace(M4, G4, 1)
    print('OK: blok 4 ispravlen')
elif G4 in r:
    print('blok 4 uzhe ispravlen')
else:
    print('!! blok 4 ne nayden')

M5 = """          if (rx->agc_hang < -200.0) { rx->agc_hang = -200.0; }
        }

        last_y = y;"""

G5 = """          if (rx->agc_hang < -200.0) { rx->agc_hang = -200.0; }
        }

        rx_set_agc(rx);

        last_y = y;"""

try:
    h = open('/home/rx3afe/piHPSDR-style/src/receiver.h').read()
    declared = ('rx_set_agc' in h)
except Exception:
    declared = False

if M5 in r and declared:
    r = r.replace(M5, G5, 1)
    print('OK: vyzov rx_set_agc dobavlen')
elif M5 in r:
    print('rx_set_agc ne nayden v receiver.h - vyzov ne dobavlen')
else:
    print('vyzov rx_set_agc uzhe stoit')

open(p, 'w').write(r)
print('receiver.c: remont zavershen')

