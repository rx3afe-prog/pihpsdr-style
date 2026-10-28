p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

old1 = '''  // ZMHFIX: podnyaat M/H nad panaramoj (poslednij dobavlennyj widget sverhu)
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

new1 = '  zmh_raise();  /* ZMHFIXCALL: odna tochka pravki polozheniya */'

if 'ZMHFIXCALL' in r:
    print('OK: staryj blok uzhe zamenen')
elif old1 in r:
    r = r.replace(old1, new1)
    print('OK: staryj blok ZMHFIX zamenen na vyzov zmh_raise()')
else:
    print('!! blok ZMHFIX ne najden'); ok = False

old2 = '''/* ZMHFN: obschaya funkciya podnyatiya knopok M/H */
static void zmh_raise(void) {
  static int zrn = 0;
  if (!GTK_IS_WIDGET(menu_b) || !GTK_IS_WIDGET(hide_b)) { return; }'''

new2 = '''/* ZMHFN: obschaya funkciya podnyatiya knopok M/H */
static void zmh_raise(void) {
  static int zrn = 0;
  if (!GTK_IS_WIDGET(menu_b) || !GTK_IS_WIDGET(hide_b)) { return; }
  /* ZMHTB: esli verhnyaya polosa - zagolovok okna (GTK_HEADER_BAR), kladem knopki tuda */
  { GtkWidget *tb = gtk_window_get_titlebar(top_window);
    if (tb && GTK_IS_HEADER_BAR(tb)) {
      GtkWidget *pm = gtk_widget_get_parent(menu_b);
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
        gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), hide_b);
        g_object_unref(hide_b);
      } else if (!ph) {
        gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), hide_b);
      }
      gtk_widget_set_size_request(menu_b, 26, 22);
      gtk_widget_set_size_request(hide_b, 26, 22);
      gtk_widget_show(menu_b);
      gtk_widget_show(hide_b);
      g_print("ZMH2: knopki upakovany v titlebar\\n");
      return;
    } else {
      if ((zrn++) % 50 == 0) { g_print("ZMH2: titlebar=%s, ostaemsya v fixed\\n", tb ? G_OBJECT_TYPE_NAME(tb) : "NULL"); }
    }
  }'''

if 'ZMHTB' in r:
    print('OK: blok ZMHTB uzhe vstavlен'.replace('vstavlен','vstavlen'))
elif old2 in r:
    r = r.replace(old2, new2)
    print('OK: zagolovochnyj blok ZMHTB dobavlen')
else:
    print('!! funkciya zmh_raise ne najdena'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

