src = open('main.c.hb2.bak', encoding='utf-8', errors='replace').read()

repl = [
  # частота теперь рисуется разметкой Pango: хвост ".ХХХ" — тёмно-зелёный
  ('gtk_label_set_text(GTK_LABEL(hfreq_label), buf);',
   'gtk_label_set_markup(GTK_LABEL(hfreq_label), buf);'),
  ('"%lld.%03lld.%03lld",',
   '"%lld.%03lld<span foreground=\\"#006400\\">.%03lld</span>",'),
  # из центра шапки — в левый край, с отступом ~19 px (это и есть ~5 мм)
  ('gtk_header_bar_set_custom_title(GTK_HEADER_BAR(hbar), hfreq_label);',
   '  gtk_widget_set_margin_start(hfreq_label, 19);\n  gtk_header_bar_pack_start(GTK_HEADER_BAR(hbar), hfreq_label);'),
]
ok = []
for old, new in repl:
    if old in src:
        src = src.replace(old, new, 1)
        ok.append('Y')
    else:
        ok.append('N')
open('main.c', 'w', encoding='utf-8').write(src)
print('replacements:', ok)
