p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

raise_code = '''  if (GTK_IS_WIDGET(menu_b) && GTK_IS_WIDGET(hide_b)) {
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

# 1. Konec radio_reconfigure: podnyaat posle kazhdoj peresborki
old = '\n  radio_reconfiguring = 0;\n'
cnt = r.count(old)
if cnt == 1:
    r = r.replace(old, '\n  /* ZMHPROC1: knopki M/H vsegda sverhu, v pravom verhnem uglu */\n' + raise_code + '\n  radio_reconfiguring = 0;\n', 1)
    print('1. OK: podnyatie dobavleno v radio_reconfigure')
else:
    print('1. !! "radio_reconfiguring = 0" vstrechaetsya %d raz, stavit ne budu' % cnt); ok = False

# 2. Startup: podnyaat posle show_all
old2 = '  gtk_widget_show_all (top_window);             // ... this shows both the HPSDR and C25 preamp/att sliders'
if 'ZMHPROC2' in r:
    print('2. OK: startup uzhe peredelan')
elif old2 in r:
    r = r.replace(old2, old2 + '\n  /* ZMHPROC2: posle show_all podnyaat knopki M/H */' + raise_code, 1)
    print('2. OK: podnyatie dobavleno v startup posle show_all')
else:
    print('2. !! stroka show_all ne najdena'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

