p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

start = r.find('gboolean rx_button_press_event(')
end = r.find('void rx_set_active(')

if start < 0 or end < 0 or end <= start:
    print('!! ne naydeny granitsy funkcii')
    raise SystemExit(1)

new = '''gboolean rx_button_press_event(GtkWidget *widget, GdkEventButton *event, gpointer data, int from) {
  const RECEIVER *rx = (RECEIVER *)data;

  if (rx == active_receiver) {
    if (event->button == GDK_BUTTON_PRIMARY) {
      last_x = (int)(event->x + 0.5);
      last_y = (int)(event->y + 0.5);
      has_movedx = has_movedy = FALSE;
      pressed = TRUE;
      drag_button = GDK_BUTTON_PRIMARY;
      //
      // Grab an AGC line if the click is close to it.
      //
      agc_drag = 0;

      if (from == 0
          && rx->agc != AGC_OFF
          && rx->agc != AGC_FIXED) {
        int dk = last_y - pan_agc_knee_y;
        int dh = last_y - pan_agc_hang_y;

        if (dk < 0) { dk = -dk; }

        if (dh < 0) { dh = -dh; }

        if (pan_agc_knee_y >= 0 && dk <= AGC_GRAB_ZONE) {
          agc_drag = 1;
        } else if (pan_agc_hang_y >= 0 && dh <= AGC_GRAB_ZONE) {
          agc_drag = 2;
        }

        fprintf(stderr, "AGC: nazhal x=%d y=%d G=%d H=%d zakhvat=%d\\n",
                last_x, last_y, pan_agc_knee_y, pan_agc_hang_y, agc_drag);
      }
    } else if (event->button == GDK_BUTTON_SECONDARY) {
      //
      // Right button: remember the start point and wait.
      // A vertical drag started in the dBm scale area adjusts
      // the TOP of the scale; a plain click (no movement)
      // still opens the menu.
      //
      last_x = (int)(event->x + 0.5);
      last_y = (int)(event->y + 0.5);
      has_movedx = has_movedy = FALSE;
      pressed = TRUE;
      drag_button = GDK_BUTTON_SECONDARY;
    }
  } else {
    making_active = TRUE;
  }

  return TRUE;
}

'''

r = r[:start] + new + r[end:]
open(p, 'w').write(r)
print('receiver.c: funkciya nazhatiya vosstanovlena s zakhvatom AGC')

