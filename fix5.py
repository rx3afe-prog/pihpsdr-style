p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

start = r.find('gboolean rx_button_press_event(')
end = r.find('gboolean rx_scroll_event(')

if start < 0 or end < 0 or end <= start:
    print('!! ne naydeny granitsy')
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
      }

      fprintf(stderr, "AGC: nazhal x=%d y=%d G=%d H=%d zakhvat=%d\\n",
              last_x, last_y, pan_agc_knee_y, pan_agc_hang_y, agc_drag);
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

// cppcheck-suppress constParameterPointer
gboolean rx_button_release_event(GtkWidget *widget, GdkEventButton *event, gpointer data, int from) {
  RECEIVER *rx = (RECEIVER *)data;

  if (making_active) {
    making_active = FALSE;
    rx_set_active(rx);

    //
    // Right click no longer opens the RX menu anywhere on the
    // panadapter: it is now the VFO snap ("cursor") action.
    //
  } else {
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

      int x = (int)(event->x + 0.5);
      int y = (int)(event->y + 0.5);
      int dy = (y - last_y) / 5;

      if (event->button == GDK_BUTTON_PRIMARY) {
        int id = active_receiver->id;

        if (has_movedx) {
          // drag
          vfo_id_move(id, (long long)((x - last_x)*rx->cB), vfo_snap);
          last_x = x;
        } else {
          //
          // Calculate target frequency and move to that one
          // Add 0.5 to pixel number, so on a 800 pix screen the pix numbers
          // 0...799 are converted to 0.5, 1.5, ... 799.5
          //
          long long f = (long long) (rx->cA + rx->cB * ((double) x + 0.5));
          //
          // Add center frequency
          //
          f += vfo[id].frequency;
          vfo_id_move_to(id, f, vfo_snap);
        }

        if (has_movedy && from == 0 && dy && pan_updown_drag) {
          rx->panadapter_low += dy;

          //
          // Keep value within reasonable bounds
          //
          if (rx->panadapter_low < -160) { rx->panadapter_low = -160; }

          if (rx->panadapter_low > rx->panadapter_high - 50) { rx->panadapter_low = rx->panadapter_high - 50; }

          radio_set_panlow(rx->id, rx->panadapter_low);   // store "by the band"
          last_y = y;
        }

        pressed = FALSE;
      } else if (event->button == GDK_BUTTON_SECONDARY) {
        //
        // Right button: a vertical drag lowers/raises the TOP of
        // the scale (panadapter_high) while the bottom stays put;
        // a plain click (no movement) opens the RX menu as before.
        //
        if (has_movedy && from == 0 && pan_updown_drag) {
          if (dy) {
            rx->panadapter_high -= dy;

            //
            // Keep the top within reasonable bounds
            //
            if (rx->panadapter_high > 0) { rx->panadapter_high = 0; }

            if (rx->panadapter_high < rx->panadapter_low + 50) { rx->panadapter_high = rx->panadapter_low + 50; }

            radio_set_panhigh(rx->id, rx->panadapter_high);

          }
        } else if (!has_movedx && !has_movedy && from == 0) {
          //
          // Right click on the panadapter: toggle the cursor
          // line ("visir"). While visible, it follows the mouse
          // position. The VFO is NOT tuned; tuning is a left click.
          //
          if (pan_cursor_on) {
            pan_cursor_on = 0;   // hide the cursor line
            pan_cursor_x = -1;
          } else {
            pan_cursor_on = 1;   // show it; it follows the mouse
            pan_cursor_x = x;
          }
        }

        pressed = FALSE;
      }
    }
  }

  return TRUE;
}

gboolean rx_motion_notify_event(GtkWidget *widget, GdkEventMotion *event, gpointer data, int from) {
  int x, y;
  GdkModifierType state;
  RECEIVER *rx = (RECEIVER *)data;
  //
  // This solves a problem observed since with GTK about mid-2023:
  // when re-focusing a (sub-)menu window after it has lost focus,
  // it may happen that the button press event for "re-focusing"
  // the menu window also ends up in the receiver panel, and that
  // the subsequent button release event is not forwarded to the
  // receiver panel.
  // Subsequent mouse moves (without a button pressed) then led to
  // wild VFO frequency changes. The first temporary solution was to
  // ignore all button press events if a (sub-)menu window is open, but
  // this reduces piHPSDR functionality. Now we solve this problem by
  // looking HERE if the mouse button is pressed, and if not, ignore the
  // move.
  //
  //
  // The cursor line follows the mouse position over the
  // panadapter in real time.
  //
  if (from == 0 && pan_cursor_on) {
    pan_cursor_x = (int)(event->x + 0.5);
  }

  int button_down = (event->state & (GDK_BUTTON1_MASK | GDK_BUTTON3_MASK)) != 0;
  int left_down = (event->state & GDK_BUTTON1_MASK) != 0;

  //
  // if !pressed, we may come from the destruction
  // of a menu, and should not move the VFO.
  //
  if (!making_active && pressed && button_down) {
    gdk_window_get_device_position (event->window,
                                    event->device,
                                    &x,
                                    &y,
                                    &state);

    //
    // Dragging an AGC line (G or H): adjust the value and skip
    // the usual VFO / scale handling.
    //
    if (agc_drag && from == 0) {
      int dyagc = y - last_y;

      if (dyagc != 0) {
        fprintf(stderr, "AGC: tyanem liniyu %d, sdvig %d pikseley\\n", agc_drag, dyagc);
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

        rx_set_agc(rx);

        last_y = y;
      }

      return TRUE;
    }

    //
    // Sometimes it turned out to be difficult to "jump" to a
    // new frequency by just clicking in the panadapter. Further analysis
    // showed that there were "moves" with zero offset arriving between
    // pressing and releasing the mouse button.
    // Accepting such a "move" between a  "press" and the next "release" event
    // sets "has_moved" and results in a "VFO drag" instead of a "VFO set".
    //
    // So we do the following:
    // - "moves" with zero offset are always ignored
    // - the first "move" to be accepted after a "press" must lead us
    //   at least 2 pixels away from the original position.
    //
    int dx = x - last_x;
    int dy = (y - last_y) / 5;

    //
    // The vertical scale drag is only active if the drag started
    // in the dBm scale area at the left edge of the display.
    //
    int scale_zone = (last_x <= PAN_SCALE_ZONE);

    if (left_down && dx != 0) {
      if (has_movedx || dx < -1 || dx > 1) {
        int id = active_receiver->id;
        vfo_id_move(id, (long long)((double)dx * rx->cB), FALSE);
        last_x = x;
        has_movedx = TRUE;
      }
    }

    if (scale_zone && dy != 0 && from == 0 && pan_updown_drag) {
      if (has_movedy || dy < -1 || dy > 1) {
        if (drag_button == GDK_BUTTON_SECONDARY) {
          //
          // Right button drives the TOP of the scale:
          // drag down lowers the ceiling (compress), drag up
          // raises it (expand). The bottom stays put.
          //
          rx->panadapter_high -= dy;

          //
          // Keep the top within reasonable bounds
          //
          if (rx->panadapter_high > 0) { rx->panadapter_high = 0; }

          if (rx->panadapter_high < rx->panadapter_low + 50) { rx->panadapter_high = rx->panadapter_low + 50; }

          radio_set_panhigh(rx->id, rx->panadapter_high);

        } else {
          rx->panadapter_low += dy;

          //
          // Keep value within reasonable bounds
          //
          if (rx->panadapter_low < -160) { rx->panadapter_low = -160; }

          if (rx->panadapter_low > rx->panadapter_high - 50) { rx->panadapter_low = rx->panadapter_high - 50; }

          radio_set_panlow(rx->id, rx->panadapter_low);   // store "by the band"
        }

        last_y = y;
        has_movedy = TRUE;
      }
    }
  }

  return TRUE;
}

// cppcheck-suppress constParameterPointer
'''

if new.count('{') != new.count('}'):
    print('!! balans skobok v novom tekste narushen, nichego ne zapisano')
    raise SystemExit(1)

r = r[:start] + new + r[end:]
open(p, 'w').write(r)
print('receiver.c: tri funktsii myshi zameneny tselikom, skobki sbalansirovany')

