m = open('main.c', encoding='utf-8').read()
old = '''static gboolean main_delete (GtkWidget *widget) {
  zen_geom_save();'''
new = '''static gboolean main_delete (GtkWidget *widget) {
  // ZGEOMFIX: radio_stop_program уже сохранил геометрию с реальным размером;
  // здесь окно может быть уже схлопнуто к дефолту — не перезаписываем'''
assert old in m, 'якорь main_delete не найден'
m = m.replace(old, new, 1)
open('main.c', 'w', encoding='utf-8').write(m)
print('лишний save из main_delete убран')
