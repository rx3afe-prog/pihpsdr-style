p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

# --- 1. Nizhnij bar v zene: ne tregaem knopki bolshe ---
old = '''    if (zen_mode >= 3 || zen_state == 3) {
      gtk_fixed_move(GTK_FIXED(fixed), menu_b, bx + rx0b->width - MENU_WIDTH, by - VFO_HEIGHT / 2 - 2);
      gtk_fixed_move(GTK_FIXED(fixed), hide_b, bx + rx0b->width - MENU_WIDTH, by - VFO_HEIGHT - 4);
      gtk_widget_show(menu_b); gtk_widget_show(hide_b);
    } else {
      gtk_widget_hide(menu_b);
      gtk_widget_hide(hide_b);
    }'''
new = '''    /* ZMHFIX2: postoyannye knopki, nichego ne peremeshchaem i ne pryachem */'''
if 'ZMHFIX2: postoyannye knopki, nichego ne peremeshchaem' in r:
    print('1. OK: nizhnij bar uzhe ne tregaet knopki')
elif old in r:
    r = r.replace(old, new, 1)
    print('1. OK: nizhnij bar bolshe ne tregaet knopki')
else:
    print('1. !! blok nizhnego bara ne najden'); ok = False

# --- 2. Vhod v zen: ne sohranyaem i ne pryachem knopki ---
old = '''    gtk_container_child_get(GTK_CONTAINER(fixed), menu_b, "x", &zen_menu_x, "y", &zen_menu_y, NULL);
    gtk_container_child_get(GTK_CONTAINER(fixed), hide_b, "x", &zen_hide_x, "y", &zen_hide_y, NULL);
    gtk_widget_hide(menu_b); gtk_widget_hide(hide_b);'''
new = '''    /* ZMHFIX2: knopki postoyannye, ne sohranyaem i ne pryachem */'''
if 'knopki postoyannye, ne sohranyaem i ne pryachem' in r:
    print('2. OK: vhod v zen uzhe ne pryachet knopki')
elif old in r:
    r = r.replace(old, new, 1)
    print('2. OK: vhod v zen bolshe ne pryachet knopki')
else:
    print('2. !! blok vhoda v zen ne najden'); ok = False

# --- 3. Z3: ubiraem vyzen_show_menuhide i peresadku k zen_zbtn ---
old = '''    if (zen_mode == 3 && GTK_IS_WIDGET(zen_zbtn)) {
      int zx = 0, zy = 0, zw = 0;
      if (!gtk_widget_translate_coordinates(zen_zbtn, fixed, 0, 0, &zx, &zy)) { zx = 0; zy = 0; }
      zw = gtk_widget_get_allocated_width(zen_zbtn);
      zen_show_menuhide(zx + zw + 6, zy, zx + zw + 34, zy);
    }'''
new = '''    /* ZMHFIX2: vyzen_show_menuhide bolshe ne nuzhen */'''
if 'vyzen_show_menuhide bolshe ne nuzhen' in r:
    print('3. OK: vyzen_show_menuhide uzhe ubran')
elif old in r:
    r = r.replace(old, new, 1)
    print('3. OK: vyzen_show_menuhide ubran iz Z3')
else:
    print('3. !! blok zen_zbtn ne najden'); ok = False

# --- 4. Vyvod iz zena: ne vozvrashaem starye pozicii, razmery i podpisi ---
old = '''    gtk_fixed_move(GTK_FIXED(fixed), menu_b, zen_menu_x, zen_menu_y);
    gtk_fixed_move(GTK_FIXED(fixed), hide_b, zen_hide_x, zen_hide_y);
    gtk_button_set_label(GTK_BUTTON(menu_b), "Menu");
    gtk_button_set_label(GTK_BUTTON(hide_b), hide_status ? "Show" : "Hide");
    gtk_widget_set_name(menu_b, "");
    gtk_widget_set_name(hide_b, "");
    gtk_widget_set_size_request(menu_b, MENU_WIDTH, VFO_HEIGHT / 2);
    gtk_widget_set_size_request(hide_b, MENU_WIDTH, VFO_HEIGHT / 2);
    gtk_widget_show(menu_b); gtk_widget_show(hide_b);'''
new = '''    /* ZMHFIX2: knopki postoyannye, vozvrashaem tolko stil i pokaz */
    gtk_widget_set_name(menu_b, "tb-btn");
    gtk_widget_set_name(hide_b, "tb-btn");
    gtk_widget_set_size_request(menu_b, 26, 22);
    gtk_widget_set_size_request(hide_b, 26, 22);
    gtk_widget_show(menu_b); gtk_widget_show(hide_b);'''
if 'vozvrashaem tolko stil i pokaz' in r:
    print('4. OK: vyvod iz zena uzhe peredelan')
elif old in r:
    r = r.replace(old, new, 1)
    print('4. OK: vyvod iz zena bolshe ne taskaet knopki')
else:
    print('4. !! blok vyvoda iz zena ne najden'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False

if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi ne budet')
    raise SystemExit(1)

