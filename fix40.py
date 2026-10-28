p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

# 1: H - na pravyj kraj polosy
a = 'gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), hide_b);'
b = 'gtk_header_bar_pack_end(GTK_HEADER_BAR(tb), hide_b);'
if b in r:
    print('OK: H uzhe na pravom krayu')
elif a in r:
    r = r.replace(a, b)
    print('OK: H perenesena na pravyj kraj')
else:
    print('!! pack dlya H ne najden'); ok = False

# 2: krupnyj shrift i razmer
if 'zmh-btn' not in r:
    old2 = '      gtk_widget_set_size_request(menu_b, 26, 22);\n      gtk_widget_set_size_request(hide_b, 26, 22);'
    new2 = ('      gtk_widget_set_size_request(menu_b, 70, 32);\n'
            '      gtk_widget_set_size_request(hide_b, 70, 32);\n'
            '      gtk_widget_set_name(menu_b, "zmh-btn");\n'
            '      gtk_widget_set_name(hide_b, "zmh-btn");\n'
            '      { static GtkCssProvider *zcss = NULL;\n'
            '        if (!zcss) {\n'
            '          zcss = gtk_css_provider_new();\n'
            '          gtk_css_provider_load_from_data(zcss,\n'
            '            ".zmh-btn { font-size: 15px; min-width: 66px; min-height: 26px; }", -1, NULL);\n'
            '          gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),\n'
            '            GTK_STYLE_PROVIDER(zcss), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);\n'
            '        }\n'
            '      }')
    if old2 in r:
        r = r.replace(old2, new2, 1)
        print('OK: knopki 70x32, shrift 15px')
    else:
        print('!! blok razmera ne najden'); ok = False
else:
    print('OK: krupnyj shrift uzhe est')

# 3: M - v odin ryad s ciframi, H - sprava
old3 = '''      GtkWidget *pm = gtk_widget_get_parent(menu_b);
      GtkWidget *ph = gtk_widget_get_parent(hide_b);
      if (pm && pm != tb) {
        g_object_ref(menu_b);
        gtk_container_remove(GTK_CONTAINER(pm), menu_b);
        gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), menu_b);
        g_object_unref(menu_b);
      } else if (!pm) {
        gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), menu_b);
      }
      if (ph && ph != tb) {
        g_object_ref(hide_b);
        gtk_container_remove(GTK_CONTAINER(ph), hide_b);
        gtk_header_bar_pack_end(GTK_HEADER_BAR(tb), hide_b);
        g_object_unref(hide_b);
      } else if (!ph) {
        gtk_header_bar_pack_end(GTK_HEADER_BAR(tb), hide_b);
      }'''
new3 = '''      /* ZMHBOX: cifry i M v odnom ryadu, H u pravogo kraya */
      GtkWidget *pm = gtk_widget_get_parent(menu_b);
      GtkWidget *ph = gtk_widget_get_parent(hide_b);
      GtkWidget *zx = gtk_header_bar_get_custom_title(GTK_HEADER_BAR(tb));
      if (zx && GTK_IS_LABEL(zx)) {
        GtkWidget *zbx = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
        g_object_ref(zx);
        gtk_header_bar_set_custom_title(GTK_HEADER_BAR(tb), zbx);
        gtk_box_pack_start(GTK_BOX(zbx), zx, FALSE, FALSE, 0);
        g_object_unref(zx);
        zx = zbx;
        g_print("ZMH3: cifry perelozheny v box vmeste s M\\n");
      }
      if (!GTK_IS_BOX(zx)) { zx = NULL; }
      if (pm) { g_object_ref(menu_b); gtk_container_remove(GTK_CONTAINER(pm), menu_b); g_object_unref(menu_b); }
      if (zx) { gtk_box_pack_start(GTK_BOX(zx), menu_b, FALSE, FALSE, 0); }
      else { gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), menu_b); }
      if (ph) { g_object_ref(hide_b); gtk_container_remove(GTK_CONTAINER(ph), hide_b); g_object_unref(hide_b); }
      gtk_header_bar_pack_end(GTK_HEADER_BAR(tb), hide_b);'''

if 'ZMHBOX' in r:
    print('OK: blok ZMHBOX uzhe est')
elif old3 in r:
    r = r.replace(old3, new3)
    print('OK: M teper v ryadu s ciframi, H sprava')
else:
    print('!! blok upakovki ne najden'); ok = False

# 4: starye otstupy obnulyaem
import re
r = re.sub(r'gtk_widget_set_margin_start$menu_b, \d+$;', 'gtk_widget_set_margin_start(menu_b, 0);', r)
r = re.sub(r'gtk_widget_set_margin_start$hide_b, \d+$;', 'gtk_widget_set_margin_start(hide_b, 0);', r)
print('OK: dopolnitelnye otstupy obnuleny')

# 5: diagnostika realnyh poziciy
if 'ZMH3POS' not in r:
    old5 = '      g_print("ZMH2: knopki upakovany v titlebar\\n");'
    new5 = ('      { int ax1 = 0, ay1 = 0, ax2 = 0, ay2 = 0;\n'
            '        if (GTK_IS_WIDGET(menu_b)) { gtk_widget_translate_coordinates(menu_b, top_window, 0, 0, &ax1, &ay1); }\n'
            '        if (GTK_IS_WIDGET(hide_b)) { gtk_widget_translate_coordinates(hide_b, top_window, 0, 0, &ax2, &ay2); }\n'
            '        g_print("ZMH3POS: M real=(%d,%d)  H real=(%d,%d)\\n", ax1, ay1, ax2, ay2);\n'
            '      }\n'
            '      g_print("ZMH2: knopki upakovany v titlebar\\n");')
    if old5 in r:
        r = r.replace(old5, new5, 1)
        print('OK: diagnostika pozicii dobavlena')
    else:
        print('!! tochka diagnostiki ne najdena')

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

