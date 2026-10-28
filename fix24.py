p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

# --- 1. Sozdanie knopok: srazu malenkie M i H v verhnem pravom uglu ---
old = '''  menu_b = gtk_button_new_with_label("Menu");
  gtk_widget_set_name(menu_b, "menubutton");
  gtk_widget_set_size_request (menu_b, MENU_WIDTH, VFO_HEIGHT / 2);
  g_signal_connect (menu_b, "button-press-event", G_CALLBACK(menu_cb), NULL) ;
  gtk_fixed_put(GTK_FIXED(fixed), menu_b, my_width - MENU_WIDTH, y);
  y += VFO_HEIGHT / 2;
  hide_b = gtk_button_new_with_label("Hide");
  gtk_widget_set_name(hide_b, "hidebutton");
  gtk_widget_set_size_request (hide_b, MENU_WIDTH, VFO_HEIGHT / 2);
  g_signal_connect(hide_b, "button-press-event", G_CALLBACK(hideall_cb), NULL);
  gtk_fixed_put(GTK_FIXED(fixed), hide_b, my_width - MENU_WIDTH, y);
  y += VFO_HEIGHT / 2;'''
new = '''  menu_b = gtk_button_new_with_label("M");
  gtk_widget_set_name(menu_b, "tb-btn");
  gtk_widget_set_size_request (menu_b, 26, 22);
  g_signal_connect (menu_b, "button-press-event", G_CALLBACK(menu_cb), NULL) ;
  gtk_fixed_put(GTK_FIXED(fixed), menu_b, my_width - 156, 4);
  y += VFO_HEIGHT / 2;
  hide_b = gtk_button_new_with_label("H");
  gtk_widget_set_name(hide_b, "tb-btn");
  gtk_widget_set_size_request (hide_b, 26, 22);
  g_signal_connect(hide_b, "button-press-event", G_CALLBACK(hideall_cb), NULL);
  gtk_fixed_put(GTK_FIXED(fixed), hide_b, my_width - 124, 4);
  y += VFO_HEIGHT / 2;'''
if 'gtk_button_new_with_label("M")' in r:
    print('1. OK: sozdanie M/H uzhe peredelano')
elif old in r:
    r = r.replace(old, new, 1)
    print('1. OK: knopki sodayutsya malenkimi M/H vverhu sprava')
else:
    print('1. !! blok sozdaniya knopok ne najden'); ok = False

# --- 2. Peresborka pri reconfigure: vsegda malenkie, vsegda vverhu, vsegda pokazany ---
old = '''  if (!floating_toolbar && gtk_widget_get_parent(menu_b) == fixed) {
    gtk_widget_set_size_request(hide_b, MENU_WIDTH, VFO_HEIGHT / 2);
    gtk_widget_set_size_request(menu_b, MENU_WIDTH, VFO_HEIGHT / 2);
    //
    // Move Hide and Menu buttons to new position
    //
    if (!zen_status) {
      gtk_fixed_move(GTK_FIXED(fixed), menu_b, display_width[display_size] - MENU_WIDTH, 0);
      gtk_fixed_move(GTK_FIXED(fixed), hide_b, display_width[display_size] - MENU_WIDTH, VFO_HEIGHT / 2);
    }
  }'''
new = '''  if (gtk_widget_get_parent(menu_b) == fixed) {
    gtk_widget_set_size_request(hide_b, 26, 22);
    gtk_widget_set_size_request(menu_b, 26, 22);
    gtk_fixed_move(GTK_FIXED(fixed), menu_b, display_width[display_size] - 156, 4);
    gtk_fixed_move(GTK_FIXED(fixed), hide_b, display_width[display_size] - 124, 4);
    gtk_widget_show(menu_b);
    gtk_widget_show(hide_b);
  }'''
if 'display_width[display_size] - 156, 4' in r:
    print('2. OK: peresborka uzhe peredelana')
elif old in r:
    r = r.replace(old, new, 1)
    print('2. OK: knopki teper vsegda malenkie i na meste')
else:
    print('2. !! blok peresborki ne najden'); ok = False

# --- 3. zen_show_menuhide: polnaya zaglushka, knopki bolshе ne peremeshchaem ---
i = r.find('static void zen_show_menuhide')
if i < 0:
    print('3. !! zen_show_menuhide ne najdena'); ok = False
elif 'postoyannye knopki: nichego ne delaet' in r:
    print('3. OK: zen_show_menuhide uzhe zaglushka')
else:
    a = r.find('(void)mx; (void)my; (void)hx; (void)hy;', i)
    j = r.find('gtk_widget_show(menu_b); gtk_widget_show(hide_b);', a)
    k = r.find('\n}', j)
    if a < 0 or j < 0 or k < 0:
        print('3. !! ne udalos vychistit telo zen_show_menuhide'); ok = False
    else:
        a += len('(void)mx; (void)my; (void)hx; (void)hy;')
        r = r[:a] + '\n  /* postoyannye knopki: nichego ne delaet */' + r[k:]
        print('3. OK: zen_show_menuhide teper nichego ne delaet')

# --- 4. hideall_cb: H vsegda tolko pokazyvaet/pryachet panel polzunkov ---
i = r.find('static gboolean hideall_cb')
if i < 0:
    print('4. !! hideall_cb ne najdena'); ok = False
else:
    start = r.find('  if (zen_status) {', i)
    endm = r.find('\n  return TRUE;\n}', start)
    if start < 0 or endm < 0:
        print('4. !! ne udalos perepisat hideall_cb'); ok = False
    else:
        new_body = '''
  if (slider_rows > 0) {
    old_slid = slider_rows;
    zen_old_slid = slider_rows;
    slider_rows = 0;
  } else if (zen_status) {
    if (zen_old_slid <= 0) zen_old_slid = 1;
    slider_rows = zen_old_slid;
  } else {
    zen_entered = 1;
    if (old_slid <= 0) old_slid = 1;
    slider_rows = old_slid;
  }
  radio_reconfigure();
  return TRUE;
}'''
        r = r[:start] + new_body + r[endm + len('\n  return TRUE;\n}'):]
        print('4. OK: H teper pokazyvaet/pryachet polzunki v lyubom rezhime')

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False

if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi ne budet')
    raise SystemExit(1)


