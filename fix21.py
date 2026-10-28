p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

# --- 1. peremennaya sostoyaniya knopki H ---
a = 'static int zen_old_tool = 0;'
if 'zen_h_open' in r:
    print('1. OK: zen_h_open uzhe est')
elif a in r:
    r = r.replace(a, a + '\nstatic int zen_h_open = 0;', 1)
    print('1. OK: zen_h_open dobavlena')
else:
    print('1. !! ne naydeno mesto dlya zen_h_open'); ok = False

# --- 2. zen_show_menuhide: malenkie M i H v stile bara ---
old = '''  g_object_unref(hide_b);
  gtk_widget_show(menu_b); gtk_widget_show(hide_b);'''
new = '''  g_object_unref(hide_b);
  gtk_button_set_label(GTK_BUTTON(menu_b), "M");
  gtk_button_set_label(GTK_BUTTON(hide_b), "H");
  gtk_widget_set_name(menu_b, "tb-btn");
  gtk_widget_set_name(hide_b, "tb-btn");
  gtk_widget_set_size_request(menu_b, 26, 22);
  gtk_widget_set_size_request(hide_b, 26, 22);
  gtk_widget_show(menu_b); gtk_widget_show(hide_b);'''
if 'gtk_button_set_label(GTK_BUTTON(menu_b), "M");' in r:
    print('2. OK: stilizaciya uzhe stoit')
elif old in r:
    r = r.replace(old, new, 1)
    print('2. OK: zen_show_menuhide teper delaeet M/H malenikimi')
else:
    print('2. !! telo zen_show_menuhide ne naydeno'); ok = False

# --- 3. zen_cb, vetka Z3: knopki u Z, a ne u bara ---
old = '''    if (zen_mode == 3 && GTK_IS_WIDGET(thetis_bar)) {
      int mbx = 0, mby = 0, mbw = 0;
      gtk_container_child_get(GTK_CONTAINER(fixed), thetis_bar, "x", &mbx, "y", &mby, NULL);
      mbw = gtk_widget_get_allocated_width(thetis_bar);
      gtk_fixed_move(GTK_FIXED(fixed), menu_b, mbx + mbw - MENU_WIDTH, mby - VFO_HEIGHT / 2 - 2);
      gtk_fixed_move(GTK_FIXED(fixed), hide_b, mbx + mbw - MENU_WIDTH, mby - VFO_HEIGHT - 4);
      gtk_widget_show(menu_b); gtk_widget_show(hide_b);
    }'''
new = '''    if (zen_mode == 3 && GTK_IS_WIDGET(zen_zbtn)) {
      int zx = 0, zy = 0, zw = 0;
      if (!gtk_widget_translate_coordinates(zen_zbtn, fixed, 0, 0, &zx, &zy)) { zx = 0; zy = 0; }
      zw = gtk_widget_get_allocated_width(zen_zbtn);
      zen_show_menuhide(zx + zw + 6, zy, zx + zw + 34, zy);
    }'''
if 'zen_show_menuhide(zx + zw + 6, zy, zx + zw + 34, zy);' in r:
    print('3. OK: peremeschenie uzhe zameneno')
elif old in r:
    r = r.replace(old, new, 1)
    print('3. OK: v Z3 knopki teper ryadom s Z')
else:
    print('3. !! blok thetis_bar v zen_cb ne nayden'); ok = False

# --- 4. vyhod iz zena: vozvrashaem vid Menu/Hide ---
old = '''    gtk_fixed_move(GTK_FIXED(fixed), menu_b, zen_menu_x, zen_menu_y);
    gtk_fixed_move(GTK_FIXED(fixed), hide_b, zen_hide_x, zen_hide_y);
    gtk_widget_show(menu_b); gtk_widget_show(hide_b);'''
new = '''    gtk_fixed_move(GTK_FIXED(fixed), menu_b, zen_menu_x, zen_menu_y);
    gtk_fixed_move(GTK_FIXED(fixed), hide_b, zen_hide_x, zen_hide_y);
    gtk_button_set_label(GTK_BUTTON(menu_b), "Menu");
    gtk_button_set_label(GTK_BUTTON(hide_b), hide_status ? "Show" : "Hide");
    gtk_widget_set_name(menu_b, "");
    gtk_widget_set_name(hide_b, "");
    gtk_widget_set_size_request(menu_b, MENU_WIDTH, VFO_HEIGHT / 2);
    gtk_widget_set_size_request(hide_b, MENU_WIDTH, VFO_HEIGHT / 2);
    gtk_widget_show(menu_b); gtk_widget_show(hide_b);'''
if 'gtk_widget_set_name(menu_b, "");' in r:
    print('4. OK: vozvrat vida uzhe stoit')
elif old in r:
    r = r.replace(old, new, 1)
    print('4. OK: pri vyhode iz zena knopki vozvrashayutsya v Menu/Hide')
else:
    print('4. !! blok vyhoda iz zena ne nayden'); ok = False

# --- 5. hideall_cb: v zene H pokazyvaet/pryachet polnuyu panel ruchek ---
old = '''  if (hide_status == 0) {
    //
    // Hide everything but store old status
    //'''
new = '''  if (zen_status) {
    if (slider_rows > 0) {
      zen_h_open = 0;
      slider_rows = 0;
    } else {
      if (zen_old_slid <= 0) zen_old_slid = 1;
      zen_h_open = 1;
      slider_rows = zen_old_slid;
    }
    radio_reconfigure();
    return TRUE;
  }

  if (hide_status == 0) {
    //
    // Hide everything but store old status
    //'''
if 'if (zen_status) {\n    if (slider_rows > 0) {' in r:
    print('5. OK: zen-vetka v hideall_cb uzhe est')
elif old in r:
    r = r.replace(old, new, 1)
    print('5. OK: H v zene teper krutit panel ruchek')
else:
    print('5. !! hideall_cb ne nayden'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False

if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi ne budet')
    raise SystemExit(1)

