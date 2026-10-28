p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

funcs = '''/* ZMHFN: obschaya funkciya podnyatiya knopok M/H */
static void zmh_raise(void) {
  static int zrn = 0;
  if (!GTK_IS_WIDGET(menu_b) || !GTK_IS_WIDGET(hide_b)) { return; }
  int wfx = gtk_widget_get_allocated_width(fixed);
  int vy = 0, vh = 0;
  if (GTK_IS_WIDGET(vfo_panel) && gtk_widget_get_parent(vfo_panel) == fixed) {
    int vtop = 0;
    if (gtk_widget_translate_coordinates(vfo_panel, fixed, 0, 0, NULL, &vtop)) { vy = vtop; }
    vh = gtk_widget_get_allocated_height(vfo_panel);
  }
  if (vh <= 1) { vh = VFO_HEIGHT; }
  int bym = vy + (vh - 22) / 2 - 12;
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
  if ((zrn++) % 50 == 0) {
    g_print("ZMH: raise w=%d vfo_y=%d vfo_h=%d btn_y=%d\\n", wfx, vy, vh, bym);
  }
}

/* ZMHTIMER: pervye 5 sekund posle starta podnimaem knopki povtorno */
static gboolean zmh_startup_raise(gpointer data) {
  static int n = 0;
  (void)data;
  zmh_raise();
  n++;
  if (n >= 50) { n = 0; return G_SOURCE_REMOVE; }
  return G_SOURCE_CONTINUE;
}

'''

protos = '''/* ZMHPROTO: obyavleniya funkciy podnyatiya knopok M/H */
static void zmh_raise(void);
static gboolean zmh_startup_raise(gpointer data);

'''

pa = 'static int zen_dock_retry(gpointer data) {'
if 'ZMHPROTO' in r:
    print('0. OK: prototipy uzhe stoyat')
elif pa in r:
    r = r.replace(pa, protos + pa, 1)
    print('0. OK: prototipy dobavleny')
else:
    print('0. !! anchor dlya prototypov ne najden'); ok = False

i = r.find('/* ZMHPROC1:')
if i == -1:
    print('1. !! blok ZMHPROC1 ne najden'); ok = False
else:
    j = r.find('radio_reconfiguring = 0;', i)
    if j == -1:
        print('1. !! konec bloka ZMHPROC1 ne najden'); ok = False
    else:
        r = r[:i] + '/* ZMHPROC1: knopki podnimaet zmh_raise() */\n  zmh_raise();\n  ' + r[j:]
        print('1. OK: ZMHPROC1 -> vyzov zmh_raise()')

i2 = r.find('/* ZMHPROC2:')
if i2 == -1:
    print('2. !! blok ZMHPROC2 ne najden'); ok = False
else:
    j2 = r.find('radio_update_meter_b_visibility', i2)
    if j2 == -1:
        print('2. !! konec bloka ZMHPROC2 ne najden'); ok = False
    else:
        r = r[:i2] + '/* ZMHPROC2: zmh_raise() + startovyj tajmer */\n  zmh_raise();\n  g_timeout_add(100, zmh_startup_raise, NULL);\n  ' + r[j2:]
        print('2. OK: ZMHPROC2 -> vyzov + tajmer')

if 'ZMHFN' not in r:
    da = 'void radio_stop_program(void) {'
    if da in r:
        r = r.replace(da, funcs + da, 1)
        print('3. OK: funkciya zmh_raise dobavlena')
    else:
        print('3. !! anchor radio_stop_program ne najden'); ok = False
else:
    print('3. OK: funkciya uzhe est')

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

