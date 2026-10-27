# 1) панорама: вырезаем блок цифровой шкалы целиком
src = open('rx_panadapter.c.zf2.bak', encoding='utf-8', errors='replace').read().splitlines(True)
anch = next((i for i,ln in enumerate(src) if '110.0, 27.0' in ln), None)
start, end = None, anch
if anch is not None:
    for i in range(anch, max(-1, anch-16), -1):
        if 'ZFREQ' in src[i].upper():
            start = i; break
    if start is None: start = anch
    for i in range(start, min(len(src), start+20)):
        if 'cairo_show_text' in src[i]:
            end = i; break
    del src[start:end+1]
    print('panadapter: cut lines %d..%d:' % (start+1, end+1))
    print(''.join(src[max(0,start-2):start]))
    print('  ... cut ...')
    open('rx_panadapter.c','w',encoding='utf-8').write(''.join(src))
else:
    print('panadapter: anchor NOT found')

# 2) radio.c: больше не обновляем заголовок окна
rc = open('radio.c.zf.bak', encoding='utf-8', errors='replace').read().splitlines(True)
n = 0
for i,ln in enumerate(rc):
    if 'gtk_window_set_title' in ln and 'top_window' in ln:
        rc[i] = '//' + ln; n += 1
open('radio.c','w',encoding='utf-8').write(''.join(rc))
print('radio.c: set_title commented =', n)

# 3) main.c: пустой custom-title — шапка не показывает заголовок окна вообще
mc = open('main.c.hb3.bak', encoding='utf-8', errors='replace').read()
needle = 'gtk_header_bar_pack_start(GTK_HEADER_BAR(hbar), hfreq_label);'
add = '\n  gtk_header_bar_set_custom_title(GTK_HEADER_BAR(hbar), gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0));\n  gtk_header_bar_set_has_subtitle(GTK_HEADER_BAR(hbar), FALSE);'
if needle in mc:
    mc = mc.replace(needle, needle + add, 1)
    print('main.c: empty custom title inserted')
else:
    print('main.c: needle NOT found')
open('main.c','w',encoding='utf-8').write(mc)
