p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

old = '''  if (GTK_IS_WIDGET(menu_b) && GTK_IS_WIDGET(hide_b)) {
    static int zmh_n = 0;
    int wfx = gtk_widget_get_allocated_width(fixed);
    if (gtk_widget_get_parent(menu_b) == fixed) {
      g_object_ref(menu_b);
      gtk_container_remove(GTK_CONTAINER(fixed), menu_b);
      gtk_fixed_put(GTK_FIXED(fixed), menu_b, wfx - 156, 4);
      g_object_unref(menu_b);
    }
    if (gtk_widget_get_parent(hide_b) == fixed) {
      g_object_ref(hide_b);
      gtk_container_remove(GTK_CONTAINER(fixed), hide_b);
      gtk_fixed_put(GTK_FIXED(fixed), hide_b, wfx - 124, 4);
      g_object_unref(hide_b);
    }
    gtk_widget_set_size_request(menu_b, 26, 22);
    gtk_widget_set_size_request(hide_b, 26, 22);
    gtk_widget_show(menu_b);
    gtk_widget_show(hide_b);
    if ((zmh_n++) % 25 == 0) {
      g_print("ZMH: raise, shirina_okna=%d, menu_x=%d\\n", wfx, wfx - 156);
    }
  }'''

new = '''  if (GTK_IS_WIDGET(menu_b) && GTK_IS_WIDGET(hide_b)) {
    static int zmh_n = 0;
    int wfx = gtk_widget_get_allocated_width(fixed);
    int vy = 0, vh = 0;
    /* ZMHCENTER: centriruem knopki po liniif cifrovoj shkaly (VFO-plan#shet) */
    if (GTK_IS_WIDGET(vfo_panel) && gtk_widget_get_parent(vfo_panel) == fixed) {
      int vtop = 0;
      if (gtk_widget_translate_coordinates(vfo_panel, fixed, 0, 0, NULL, &vtop)) { vy = vtop; }
      vh = gtk_widget_get_allocated_height(vfo_panel);
    }
    if (vh <= 1) { vh = VFO_HEIGHT; }
    int bym = vy + (vh - 22) / 2;
    if (bym < 0) { bym = 0; }
    if (gtk_widget_get_parent(menu_b) == fixed) {
      g_object_ref(menu_b);
      gtk_container_remove(GTK_CONTAINER(fixed), menu_b);
      gtk_fixed_put(GTK_FIXED(fixed), menu_b, wfx - 156, bym);
      g_object_unref(menu_b);
    }
    if (gtk_widget_get_parent(hide_b) == fixed) {
      g_object_ref(hide_b);
      gtk_container_remove(GTK_CONTAINER(fixed), hide_b);
      gtk_fixed_put(GTK_FIXED(fixed), hide_b, wfx - 124, bym);
      g_object_unref(hide_b);
    }
    gtk_widget_set_size_request(menu_b, 26, 22);
    gtk_widget_set_size_request(hide_b, 26, 22);
    gtk_widget_show(menu_b);
    gtk_widget_show(hide_b);
    if ((zmh_n++) % 25 == 0) {
      g_print("ZMH: raise, w=%d vfo_y=%d vfo_h=%d btn_y=%d\\n", wfx, vy, vh, bym);
    }
  }'''

n = r.count(old)
if 'ZMHCENTER' in r:
    print('OK: uzhe sdelano')
elif n >= 1:
    r = r.replace(old, new)
    print('OK: zameneno blokov: %d' % n)
else:
    print('!! staryj blok ne najden'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

