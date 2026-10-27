import re

# 1) Makefile
mk = open('Makefile').read()
if 'src/text_menu.o' not in mk:
    done = False
    for anchor in ['src/theme_menu.o \\', 'src/about_menu.o \\']:
        if anchor in mk:
            mk = mk.replace(anchor, anchor + '\nsrc/text_menu.o \\', 1)
            print('1/2: Makefile обновлён (после', anchor.strip() + ')')
            done = True
            break
    if not done:
        print('1/2: Makefile — якорь НЕ найден!')
    open('Makefile', 'w').write(mk)
else:
    print('1/2: Makefile уже обновлён')

# 2) new_menu.c
p = 'src/new_menu.c'
s = open(p).read()
if '#include "text_menu.h"' not in s:
    s = s.replace('#include "theme_menu.h"', '#include "theme_menu.h"\n#include "text_menu.h"', 1)
    print('2a: include добавлен')
else:
    print('2a: include уже есть')

if 'text_cb' not in s:
    m = re.search(r'static gboolean theme_cb\s*\(GtkWidget \*widget, GdkEventButton \*event, gpointer data\)\s*\{\s*cleanup\(\);\s*theme_menu\(top_window\);\s*return TRUE;\s*\}', s)
    if m:
        s = s[:m.end()] + '\n\n// cppcheck-suppress constParameterCallback\nstatic gboolean text_cb (GtkWidget *widget, GdkEventButton *event, gpointer data) {\n  cleanup();\n  text_menu(top_window);\n  return TRUE;\n}' + s[m.end():]
        print('2b: text_cb добавлен')
    else:
        print('2b: theme_cb НЕ найден!')

lines = s.split('\n')
try:
    conn_i = next(i for i, l in enumerate(lines) if 'G_CALLBACK(theme_cb)' in l and 'g_signal_connect' in l)
    conn = lines[conn_i]
    var = re.search(r'g_signal_connect\((\w+)', conn).group(1)
    create_i = next(i for i, l in enumerate(lines) if re.match(r'\s*' + var + r'\s*=\s*gtk_button_new', l))
    create = lines[create_i]
    attach_i = next(i for i, l in enumerate(lines) if 'gtk_grid_attach' in l and var in l)
    attach = lines[attach_i]
    m2 = re.search(r'gtk_grid_attach\(GTK_GRID\((\w+)\),\s*' + var + r',\s*([^,]+),\s*([^,]+),\s*(\d+),\s*(\d+)\)', attach)
    if m2 and 'gtk_button_new_with_label' in create:
        newvar = 'text_menu_button'
        newcreate = re.sub(r'"[^"]*"', '"Text"', create.replace(var, newvar, 1), count=1)
        newconn = conn.replace(var, newvar, 1).replace('G_CALLBACK(theme_cb)', 'G_CALLBACK(text_cb)')
        col = m2.group(2)
        newattach = attach[:m2.start(2)] + '(' + col + ' + 1)' + attach[m2.end(2):]
        newattach = newattach.replace(var, newvar, 1)
        for idx, line in sorted([(create_i, newcreate), (conn_i, newconn), (attach_i, newattach)], reverse=True):
            lines.insert(idx + 1, line)
        print('2c: кнопка Text добавлена')
    else:
        print('2c: создание/привязка Theme НЕ опознаны!')
except StopIteration:
    print('2c: theme_cb подключение НЕ найдено!')
open(p, 'w').write('\n'.join(lines))
print('Патч завершён.')
