p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

# --- 1. zen_show_menuhide: peredannye koordinaty bolshe ne ispolzuem ---
a = 'static void zen_show_menuhide(int mx, int my, int hx, int hy) {'
if '(void)mx; (void)my;' in r:
    print('1. OK: zagolovok uzhe podpravlen')
elif a in r:
    r = r.replace(a, a + '\n  (void)mx; (void)my; (void)hx; (void)hy;', 1)
    print('1. OK: koordinaty u Z ignoriruyutsya')
else:
    print('1. !! zen_show_menuhide ne naydena'); ok = False

# --- 2. M i H teper vverhu sprava, u knopok okna ---
old = '''  g_object_ref(menu_b);
  gtk_container_remove(GTK_CONTAINER(fixed), menu_b);
  gtk_fixed_put(GTK_FIXED(fixed), menu_b, mx, my);
  g_object_unref(menu_b);
  g_object_ref(hide_b);
  gtk_container_remove(GTK_CONTAINER(fixed), hide_b);
  gtk_fixed_put(GTK_FIXED(fixed), hide_b, hx, hy);
  g_object_unref(hide_b);'''
new = '''  int ztop = gtk_widget_get_allocated_width(fixed);
  g_object_ref(menu_b);
  gtk_container_remove(GTK_CONTAINER(fixed), menu_b);
  gtk_fixed_put(GTK_FIXED(fixed), menu_b, ztop - 200, 8);
  g_object_unref(menu_b);
  g_object_ref(hide_b);
  gtk_container_remove(GTK_CONTAINER(fixed), hide_b);
  gtk_fixed_put(GTK_FIXED(fixed), hide_b, ztop - 168, 8);
  g_object_unref(hide_b);'''
if 'gtk_fixed_put(GTK_FIXED(fixed), menu_b, ztop - 200, 8);' in r:
    print('2. OK: perenos vverh uzhe stoit')
elif old in r:
    r = r.replace(old, new, 1)
    print('2. OK: M i H teper vverhu sprava')
else:
    print('2. !! telo zen_show_menuhide ne naydeno'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False

if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi ne budet')
    raise SystemExit(1)

