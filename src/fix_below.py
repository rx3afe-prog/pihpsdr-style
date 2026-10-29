lines = open('main.c.bak', encoding='utf-8', errors='replace').read().splitlines(True)
out, ok = [], False
for ln in lines:
    out.append(ln)
    if not ok and 'top_window = gtk_application_window_new (app);' in ln:
        out.append('  gtk_window_set_keep_below(GTK_WINDOW(top_window), TRUE);\n')
        ok = True
open('main.c', 'w', encoding='utf-8').write(''.join(out))
print('main.c : keep_below inserted=%s' % ok)
