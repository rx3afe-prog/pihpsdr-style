p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

if 'AGC: posle' not in r:
    print('!! ozhidaemaya versiya ne naydena (net "posle")')
    raise SystemExit(1)

ok = True

def rep(a, b, tag):
    global r, ok
    if a not in r:
        print('!! ne nayden:', tag)
        ok = False
        return
    r = r.replace(a, b, 1)
    print('OK:', tag)

rep('''      fprintf(stderr, "AGC: nazhal x=%d y=%d G=%d H=%d zakhvat=%d t=%.1f h=%.1f dbmpp=%.3f\\n",
              last_x, last_y, pan_agc_knee_y, pan_agc_hang_y, agc_drag,
              rx->agc_thresh, rx->agc_hang, pan_dbm_per_pixel);
''', '', '1. ubran otchet o nazhatii')

rep('''        fprintf(stderr, "AGC: tyanem liniyu %d, sdvig %d pikseley t=%.1f h=%.1f\\n",
                agc_drag, dyagc, rx->agc_thresh, rx->agc_hang);
''', '', '2. ubran otchet o tyage')

rep('''        last_y = y;
        fprintf(stderr, "AGC: posle t=%.1f h=%.1f\\n", rx->agc_thresh, rx->agc_hang);''',
'''        if (agc_drag == 1) {
          SetRXAAGCThresh(rx->id, rx->agc_thresh, (double)rx->afft_size, (double)rx->sample_rate);
        } else {
          SetRXAAGCHangLevel(rx->id, rx->agc_hang);
        }

        last_y = y;''', '3. vysov DSP pri tyage')

rep('''      if (agc_drag) {
        agc_drag = 0;
        pressed = FALSE;
        return TRUE;
      }''',
'''      if (agc_drag) {
        if (agc_drag == 1) {
          SetRXAAGCThresh(rx->id, rx->agc_thresh, (double)rx->afft_size, (double)rx->sample_rate);
        } else {
          SetRXAAGCHangLevel(rx->id, rx->agc_hang);
        }

        rx_save_state(rx);
        agc_drag = 0;
        pressed = FALSE;
        return TRUE;
      }''', '4. vysov DSP i sohranenie pri otpuskanii')

if ok:
    open(p, 'w').write(r)
    print('receiver.c: finalnaya versiya zapisana')
else:
    print('nichego ne zapisano')

