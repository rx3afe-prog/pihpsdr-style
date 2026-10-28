p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

old = '''  int ztop = gtk_widget_get_allocated_width(fixed);
  g_object_ref(menu_b);
  gtk_container_remove(GTK_CONTAINER(fixed), menu_b);
  gtk_fixed_put(GTK_FIXED(fixed), menu_b, ztop - 200, 8);
  g_object_unref(menu_b);
  g_object_ref(hide_b);
  gtk_container_remove(GTK_CONTAINER(fixed), hide_b);
  gtk_fixed_put(GTK_FIXED(fixed), hide_b, ztop - 168, 8);
  g_object_unref(hide_b);'''
new = '''  int vfy = 0, vfh = 0;
  if (GTK_IS_WIDGET(vfo_panel)) {
    int vfx = 0;
    gtk_container_child_get(GTK_CONTAINER(fixed), vfo_panel, "x", &vfx, "y", &vfy, NULL);
    vfh = gtk_widget_get_allocated_height(vfo_panel);
    (void)vfx;
  }
  int byy = (vfh > 30) ? vfy + (vfh - 22) / 2 : vfy + 6;
  if (byy < 2) byy = 2;
  int wtop = gtk_widget_get_allocated_width(fixed);
  g_object_ref(menu_b);
  gtk_container_remove(GTK_CONTAINER(fixed), menu_b);
  gtk_fixed_put(GTK_FIXED(fixed), menu_b, wtop - 150, byy);
  g_object_unref(menu_b);
  g_object_ref(hide_b);
  gtk_container_remove(GTK_CONTAINER(fixed), hide_b);
  gtk_fixed_put(GTK_FIXED(fixed), hide_b, wtop - 118, byy);
  g_object_unref(hide_b);'''

if 'gtk_fixed_put(GTK_FIXED(fixed), menu_b, wtop - 150, byy);' in r:
    print('OK: privyazka k planke chastotomeru uzhe stoit')
elif old in r:
    r = r.replace(old, new, 1)
    print('OK: M i H teper na planke chastotomeru, u pravogo kraya')
else:
    print('!! blok razmescheniya ne najden, nichego ne zapisano')
    ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False

if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi ne budet')
    raise SystemExit(1)

