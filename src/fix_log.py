# ---------- radio.c ----------
lines = open('radio.c.bak', encoding='utf-8', errors='replace').read().splitlines(True)
statics_r = ['static int zrc_last_w = -1;\n', 'static int zrc_last_h = -1;\n', '\n']
guard_r = (
    '  if (zrc_last_w != my_width || zrc_last_h != rx_height) {\n'
    '    t_print("%s: receivers=%d  %dx%d\\n", __func__, receivers, my_width, rx_height);\n'
    '    zrc_last_w = my_width;\n'
    '    zrc_last_h = rx_height;\n'
    '  }\n'
)
anchor_r = 'rx_height = zen_status ? my_height : my_height - VFO_HEIGHT;'
out, ok_static, ok_print, ok_guard = [], False, False, False
for ln in lines:
    if 't_print("%s: receivers=%d\\n", __func__, receivers);' in ln:
        ok_print = True
        continue
    if ln.startswith('void radio_reconfigure(') and not ok_static:
        out.extend(statics_r)
        ok_static = True
    out.append(ln)
    if anchor_r in ln:
        out.append(guard_r)
        ok_guard = True
open('radio.c', 'w', encoding='utf-8').writelines(out)
print('radio.c    : statics=%s, old print removed=%s, guard added=%s' % (ok_static, ok_print, ok_guard))

# ---------- receiver.c ----------
lines = open('receiver.c.bak', encoding='utf-8', errors='replace').read().splitlines(True)
out, ok_static, ok_wrap, ok_wf = [], False, False, False
for ln in lines:
    if 't_print' in ln and 'waterfall set_size_request' in ln:
        ok_wf = True
        continue
    if 't_print' in ln and 'rx=%d width=%d height=%d' in ln:
        indent = ln[:len(ln) - len(ln.lstrip())]
        i = ln.find('(')
        args = ln[i + 1:ln.rfind(');')].strip()
        out.append(indent + 'if (zrx_last_w != width || zrx_last_h != height) {\n')
        out.append(indent + '  ' + ln)
        out.append(indent + '  zrx_last_w = width;\n')
        out.append(indent + '  zrx_last_h = height;\n')
        out.append(indent + '}\n')
        ok_wrap = True
        continue
    if not ok_static and 'void rx_reconfigure' in ln:
        out.append('static int zrx_last_w = -1;\n')
        out.append('static int zrx_last_h = -1;\n')
        out.append('\n')
        ok_static = True
    out.append(ln)
open('receiver.c', 'w', encoding='utf-8').write(''.join(out))
print('receiver.c : statics=%s, rx print wrapped=%s, waterfall print removed=%s' % (ok_static, ok_wrap, ok_wf))
