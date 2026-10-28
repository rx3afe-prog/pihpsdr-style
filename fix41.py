import re
p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

# 1: ves upakovochnyj blok (lyuboj variant) menyaem na bezopasnyj
pattern = re.compile(r'GtkWidget \*pm = gtk_widget_get_parent$menu_b$;.*?gtk_header_bar_pack_(?:start|end)$GTK_HEADER_BARtb, hide_b$;', re.S)
safe = '''/* ZMHSAFE: M sleva ryadom s ciframi, H sprava; knopki trogaem tolko esli oni polnostyu gotovy */
      if (!GTK_IS_WIDGET(menu_b) || !GTK_IS_WIDGET(hide_b)) { return; }
      GtkWidget *pm = gtk_widget_get_parent(menu_b);
      GtkWidget *ph = gtk_widget_get_parent(hide_b);
      if (pm != tb) {
        if (pm) {
          g_object_ref(menu_b);
          gtk_container_remove(GTK_CONTAINER(pm), menu_b);
          g_object_unref(menu_b);
        }
        gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), menu_b);
      }
      if (ph != tb) {
        if (ph) {
          g_object_ref(hide_b);
          gtk_container_remove(GTK_CONTAINER(ph), hide_b);
          g_object_unref(hide_b);
        }
        gtk_header_bar_pack_end(GTK_HEADER_BAR(tb), hide_b);
      }'''
if 'ZMHSAFE' in r:
    print('OK: bezopasnaya versiya uzhe stoit')
elif pattern.search(r):
    r = pattern.sub(safe, r, count=1)
    print('OK: upakovka zamenena na bezopasnuyu (ris Kovannyj fokus udalen)')
else:
    print('!! upakovochnyj blok ne najden'); ok = False

# 2: krupnye knopki, esli eshyo ne sdelany
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
if 'zmh-btn' in r:
    print('OK: krupnye knopki uzhe est')
elif old2 in r:
    r = r.replace(old2, new2, 1)
    print('OK: knopki 70x32, shrift 15px')
else:
    print('!! blok razmera ne najden (ne strashno, proverim)')

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

