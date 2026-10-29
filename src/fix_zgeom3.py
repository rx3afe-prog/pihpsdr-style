# --- main.c: снять static с zen_geom_reapply, чтобы её видел radio.c ---
m = open('main.c', encoding='utf-8').read()
old = 'static int zen_geom_reapply(gpointer data) {'
assert old in m, 'якорь zen_geom_reapply не найден'
m = m.replace(old, 'int zen_geom_reapply(gpointer data) {  // ZGEOMFIX: не static — зовётся из radio.c после построения', 1)
open('main.c', 'w', encoding='utf-8').write(m)
print('main.c: zen_geom_reapply теперь публичная')

# --- radio.c: extern-объявление + вызов после обоих radio_create_visual() ---
r = open('radio.c', encoding='utf-8').read()
old = 'extern void zen_geom_save(void);'
assert old in r, 'якорь extern zen_geom_save не найден'
r = r.replace(old, old + '\nextern int zen_geom_reapply(gpointer data);  // ZGEOMFIX', 1)

calls = r.count('  radio_create_visual();')
assert calls == 2, 'ожидалось 2 вызова radio_create_visual, найдено %d' % calls
r = r.replace('  radio_create_visual();',
              '  radio_create_visual();\n  zen_geom_reapply();  // ZGEOMFIX: вернуть сохранённую геометрию после построения радио')
open('radio.c', 'w', encoding='utf-8').write(r)
print('radio.c: reapply вставлен после обоих вызовов radio_create_visual')
