# --- radio.c: убрать save после разбора радио ---
lines = open('radio.c', encoding='utf-8').read().splitlines(keepends=True)
hits = [i for i, ln in enumerate(lines) if 'zen_geom_save' in ln and 'extern' not in ln]
assert len(hits) == 1, 'ожидался 1 вызов, найдено %d' % len(hits)
i = hits[0]
print('--- контекст radio.c вокруг вызова ---')
for k in range(max(0, i-6), min(len(lines), i+4)):
    print('%5d: %s' % (k+1, lines[k].rstrip()))
print('-------------------------------------')
del lines[i]
open('radio.c', 'w', encoding='utf-8').write(''.join(lines))
print('radio.c: вызов после разбора радио удалён')

# --- main.c: вернуть save в main_delete (там размер ещё настоящий) ---
m = open('main.c', encoding='utf-8').read()
old = '''static gboolean main_delete (GtkWidget *widget) {
  // ZGEOMFIX: radio_stop_program уже сохранил геометрию с реальным размером;
  // здесь окно может быть уже схлопнуто к дефолту — не перезаписываем'''
new = '''static gboolean main_delete (GtkWidget *widget) {
  zen_geom_save();  // ZGEOMFIX: единственное место сохранения, размер ещё реальный'''
assert old in m, 'якорь main_delete не найден'
m = m.replace(old, new, 1)
open('main.c', 'w', encoding='utf-8').write(m)
print('main.c: честный save возвращён в main_delete')
