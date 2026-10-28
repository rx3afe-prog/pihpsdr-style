p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

# --- 1. radio_reconfigure_screen: vozvrashaem knopki v fixed dazhe esli ih ukrali ---
old = '''  if (gtk_widget_get_parent(menu_b) == fixed) {
    gtk_widget_set_size_request(hide_b, 26, 22);
    gtk_widget_set_size_request(menu_b, 26, 22);
    gtk_fixed_move(GTK_FIXED(fixed), menu_b, display_width[display_size] - 156, 4);
    gtk_fixed_move(GTK_FIXED(fixed), hide_b, display_width[display_size] - 124, 4);
    gtk_widget_show(menu_b);
    gtk_widget_show(hide_b);
  }'''
new = '''  gtk_widget_set_size_request(hide_b, 26, 22);
  gtk_widget_set_size_request(menu_b, 26, 22);
  if (gtk_widget_get_parent(menu_b) != fixed) {
    GtkWidget *par = gtk_widget_get_parent(menu_b);
    if (par != NULL) {
      g_object_ref(menu_b);
      gtk_container_remove(GTK_CONTAINER(par), menu_b);
      gtk_fixed_put(GTK_FIXED(fixed), menu_b, display_width[display_size] - 156, 4);
      g_object_unref(menu_b);
    }
  } else {
    gtk_fixed_move(GTK_FIXED(fixed), menu_b, display_width[display_size] - 156, 4);
  }
  if (gtk_widget_get_parent(hide_b) != fixed) {
    GtkWidget *par = gtk_widget_get_parent(hide_b);
    if (par != NULL) {
      g_object_ref(hide_b);
      gtk_container_remove(GTK_CONTAINER(par), hide_b);
      gtk_fixed_put(GTK_FIXED(fixed), hide_b, display_width[display_size] - 124, 4);
      g_object_unref(hide_b);
    }
  } else {
    gtk_fixed_move(GTK_FIXED(fixed), hide_b, display_width[display_size] - 124, 4);
  }
  gtk_widget_show(menu_b);
  gtk_widget_show(hide_b);'''
if 'gtk_widget_get_parent(menu_b) != fixed' in r:
    print('1. OK: vozvrat knopok uzhe stoit')
elif old in r:
    r = r.replace(old, new, 1)
    print('1. OK: pri peresborke knopki vozvrashayutsya i podnimayutsya')
else:
    print('1. !! blok peresborki ne najden'); ok = False

# --- 2. radio_create_visual: v samom konce podnimaem M i H nad vsem ---
old = '''  if (floating_toolbar) {
    toolbar_create_floating(TOOLBAR_HEIGHT, menu_b, hide_b);
  } else if (toolbar_rows > 0) {
    toolbar_create(my_width, TOOLBAR_HEIGHT, toolbar_rows);
    toolbar_show(y);
  }'''
new = old + '''

  // ZMHFIX: podnyaat M/H nad panaramoj (poslednij dobavlennyj widget sverhu)
  if (GTK_IS_WIDGET(menu_b) && gtk_widget_get_parent(menu_b) != fixed) {
    g_object_ref(menu_b);
    gtk_container_remove(GTK_CONTAINER(gtk_widget_get_parent(menu_b)), menu_b);
    gtk_fixed_put(GTK_FIXED(fixed), menu_b, my_width - 156, 4);
    g_object_unref(menu_b);
  } else if (GTK_IS_WIDGET(menu_b)) {
    gtk_fixed_move(GTK_FIXED(fixed), menu_b, my_width - 156, 4);
  }
  if (GTK_IS_WIDGET(hide_b) && gtk_widget_get_parent(hide_b) != fixed) {
    g_object_ref(hide_b);
    gtk_container_remove(GTK_CONTAINER(gtk_widget_get_parent(hide_b)), hide_b);
    gtk_fixed_put(GTK_FIXED(fixed), hide_b, my_width - 124, 4);
    g_object_unref(hide_b);
  } else if (GTK_IS_WIDGET(hide_b)) {
    gtk_fixed_move(GTK_FIXED(fixed), hide_b, my_width - 124, 4);
  }
  gtk_widget_set_size_request(menu_b, 26, 22);
  gtk_widget_set_size_request(hide_b, 26, 22);
  gtk_widget_show(menu_b);
  gtk_widget_show(hide_b);'''
if 'ZMHFIX: podnyaat M/H' in r:
    print('2. OK: podnyatie v konce sborki uzhe stoit')
elif old in r:
    r = r.replace(old, new, 1)
    print('2. OK: M i H podnimayutsya nad panaramoj')
else:
    print('2. !! blok toolbar_create ne najden'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False

if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi ne budet')
    raise SystemExit(1)

