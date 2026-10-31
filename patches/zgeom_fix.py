import glob

changed = 0
for fn in sorted(glob.glob('src/*.c') + glob.glob('src/*.h')):
    s = open(fn).read()
    orig = s
    s = s.replace('GtkFixed *fixed', 'GtkWidget *fixed')
    s = s.replace('GtkFixed * fixed', 'GtkWidget * fixed')
    s = s.replace('fixed = gtk_fixed_new()', 'fixed = gtk_layout_new(NULL, NULL)')
    s = s.replace('fixed = gtk_fixed_new ()', 'fixed = gtk_layout_new (NULL, NULL)')
    s = s.replace('GTK_FIXED(fixed)', 'GTK_LAYOUT(fixed)')
    s = s.replace('GTK_FIXED (fixed)', 'GTK_LAYOUT (fixed)')
    if s != orig:
        open(fn, 'w').write(s)
        changed += 1
        print('izmenen:', fn)
print('faylov izmeneno =', changed)

src = open('src/main.c').read()
old = 'gtk_window_set_resizable(GTK_WINDOW(top_window), TRUE);'
new = 'gtk_window_set_resizable(GTK_WINDOW(top_window), TRUE);\n  gtk_window_unfullscreen(GTK_WINDOW(top_window));\n  gtk_window_set_keep_above(GTK_WINDOW(top_window), FALSE);'
if old in src:
    src = src.replace(old, new)
    print('ZGEOMFIX: fullscreen i keep_above snyaty')
else:
    print('VNIMANIE: blok ne nayden')
open('src/main.c', 'w').write(src)
print('gotovo')
