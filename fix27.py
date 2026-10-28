p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

def rep(name, old, new):
    global r, ok
    if new in r:
        print(name + ': OK: uzhe sdelano')
    elif old in r:
        r = r.replace(old, new, 1)
        print(name + ': OK: zameneno')
    else:
        print(name + ': !! blok ne najden'); ok = False

# 1. zen_cycle_cb: vyhod iz Z3 — ne pryachem knopki
rep('1. vyhod iz Z3',
'''    if (GTK_IS_WIDGET(menu_b) && gtk_widget_get_visible(menu_b)) {
      gtk_widget_hide(menu_b);
      gtk_widget_hide(hide_b);
      zen_state = 0;''',
'''    if (GTK_IS_WIDGET(menu_b) && gtk_widget_get_visible(menu_b)) {
      /* ZMHFIX3: knopki postoyannye, ne pryachem */
      zen_state = 0;''')

# 2. zen_cycle_cb: blok Z3 s zen_show_menuhide i hide
rep('2. blok Z3 v zen_cycle_cb',
'''  if (zen_state == 3 && GTK_IS_WIDGET(zen_zbtn)) {
    int zx = 0, zy = 0, zw = 0;
    if (!gtk_widget_translate_coordinates(zen_zbtn, fixed, 0, 0, &zx, &zy)) { zx = 0; zy = 0; }
    zw = gtk_widget_get_allocated_width(zen_zbtn);
    g_print("Z4MENU: zx=%d zy=%d zw=%d\\n", zx, zy, zw); zen_show_menuhide(zx + zw + 6, zy,
                      zx + zw + 6 + MENU_WIDTH + 6, zy);
  } else {
    gtk_widget_hide(menu_b); gtk_widget_hide(hide_b);
  }''',
'''  /* ZMHFIX3: knopki postoyannye, menuhide ne nuzhen */''')

# 3. zen_reapply: blok Z3 s zen_show_menuhide i hide
rep('3. blok Z3 v zen_reapply',
'''  if (zen_entered && zen_state == 3 && GTK_IS_WIDGET(zen_zbtn)) {
    int zx = 0, zy = 0, zw = 0;
    if (!gtk_widget_translate_coordinates(zen_zbtn, fixed, 0, 0, &zx, &zy)) { zx = 0; zy = 0; }
    zw = gtk_widget_get_allocated_width(zen_zbtn);
    g_print("Z4MENU: zx=%d zy=%d zw=%d\\n", zx, zy, zw); zen_show_menuhide(zx + zw + 6, zy,
                      zx + zw + 6 + MENU_WIDTH + 6, zy);
  } else {
    if (GTK_IS_WIDGET(menu_b)) gtk_widget_hide(menu_b);
    if (GTK_IS_WIDGET(hide_b)) gtk_widget_hide(hide_b);
  }''',
'''  /* ZMHFIX3: knopki postoyannye, menuhide ne nuzhen */''')

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

