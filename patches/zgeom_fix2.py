import glob

names = [
    ('gtk_fixed_move(GTK_LAYOUT(fixed)', 'gtk_layout_move(GTK_LAYOUT(fixed)'),
    ('gtk_fixed_move(GTK_FIXED(fixed)', 'gtk_layout_move(GTK_LAYOUT(fixed)'),
    ('gtk_fixed_put(GTK_LAYOUT(fixed)', 'gtk_layout_put(GTK_LAYOUT(fixed)'),
    ('gtk_fixed_put(GTK_FIXED(fixed)', 'gtk_layout_put(GTK_LAYOUT(fixed)'),
]
changed = 0
for fn in sorted(glob.glob('src/*.c')):
    s = open(fn).read()
    orig = s
    for a, b in names:
        s = s.replace(a, b)
    if s != orig:
        open(fn, 'w').write(s)
        changed += 1
        print('izmenen:', fn)
print('gotovo, faylov izmeneno =', changed)
