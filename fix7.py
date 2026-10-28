p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

if 'dbmpp' in r:
    print('usilennaya otladka uzhe stoit')
    raise SystemExit(0)

ok = True

def rep(a, b, tag):
    global r, ok
    if a not in r:
        print('!! ne nayden:', tag)
        ok = False
        return
    r = r.replace(a, b, 1)
    print('OK:', tag)

rep('AGC: nazhal x=%d y=%d G=%d H=%d zakhvat=%d\\n',
    'AGC: nazhal x=%d y=%d G=%d H=%d zakhvat=%d t=%.1f h=%.1f dbmpp=%.3f\\n',
    '1a. format nazhatiya')

rep('pan_agc_knee_y, pan_agc_hang_y, agc_drag);',
    'pan_agc_knee_y, pan_agc_hang_y, agc_drag,\n              rx->agc_thresh, rx->agc_hang, pan_dbm_per_pixel);',
    '1b. argumenty nazhatiya')

rep('AGC: tyanem liniyu %d, sdvig %d pikseley\\n',
    'AGC: tyanem liniyu %d, sdvig %d pikseley t=%.1f h=%.1f\\n',
    '2a. format tyagi')

rep('agc_drag, dyagc);',
    'agc_drag, dyagc, rx->agc_thresh, rx->agc_hang);',
    '2b. argumenty tyagi')

if ok:
    open(p, 'w').write(r)
    print('receiver.c: usilennaya otladka ustanovlena')
else:
    print('nichego ne zapisano')

