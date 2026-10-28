p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
start = r.find('/* ZMHFN:')
end = r.find('/* ZMHTIMER:')
if start == -1 or end == -1 or end <= start:
    print('!! granicy funkcii ne najdeny, nichego ne menyal')
    raise SystemExit(1)

new_fn = '''/* ZMHFN: svoi knopki M/H v titlebar, nichego ne perenosim */
static GtkWidget *zmh_mb = NULL;
static GtkWidget *zmh_hb = NULL;
static GtkWidget *zmh_tb = NULL;

static void zmh_raise(void) {
  static int zrn = 0;
  zrn++;
  GtkWidget *tb = gtk_window_get_titlebar(GTK_WINDOW(top_window));
  if (!(tb && GTK_IS_HEADER_BAR(tb))) {
    if (zrn % 50 == 1) { g_print("ZMH6: titlebar=%s\\n", tb ? G_OBJECT_TYPE_NAME(tb) : "NULL"); }
    return;
  }
  if (zmh_tb != tb) {
    zmh_tb = tb;
    zmh_mb = NULL;
    zmh_hb = NULL;
  }
  if (!zmh_mb) {
    zmh_mb = gtk_button_new_with_label("M");
    gtk_widget_set_name(zmh_mb, "zmh-btn");
    gtk_widget_set_size_request(zmh_mb, 70, 32);
    g_signal_connect(zmh_mb, "button-press-event", G_CALLBACK(menu_cb), NULL);
    gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), zmh_mb);
    gtk_widget_show(zmh_mb);
    g_print("ZMH6: M sozdana v titlebar\\n");
  }
  if (!zmh_hb) {
    zmh_hb = gtk_button_new_with_label("H");
    gtk_widget_set_name(zmh_hb, "zmh-btn");
    gtk_widget_set_size_request(zmh_hb, 70, 32);
    g_signal_connect(zmh_hb, "button-press-event", G_CALLBACK(hideall_cb), NULL);
    gtk_header_bar_pack_end(GTK_HEADER_BAR(tb), zmh_hb);
    gtk_widget_show(zmh_hb);
    g_print("ZMH6: H sozdana v titlebar\\n");
  }
  { static GtkCssProvider *zcss = NULL;
    if (!zcss) {
      zcss = gtk_css_provider_new();
      gtk_css_provider_load_from_data(zcss,
        ".zmh-btn { font-size: 15px; min-width: 66px; min-height: 26px; }", -1, NULL);
      gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),
        GTK_STYLE_PROVIDER(zcss), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    }
  }
}

'''
if new_fn.count('{') != new_fn.count('}'):
    print('!! skobki v novoj funkcii ne ravny, otkaz')
    raise SystemExit(1)
r = r[:start] + new_fn + r[end:]

# starye knopki: vsegda pryachem vmesto pokaza, chtoby ne bylo dublej
n1 = r.count('gtk_widget_show(menu_b)')
n2 = r.count('gtk_widget_show(hide_b)')
r = r.replace('gtk_widget_show(menu_b)', 'gtk_widget_hide(menu_b)')
r = r.replace('gtk_widget_show(hide_b)', 'gtk_widget_hide(hide_b)')
print('OK: starye knopki pereklyucheny na skrytie (%d i %d mest)' % (n1, n2))

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet')
    raise SystemExit(1)
open(p, 'w').write(r)
print('VSE: zapisano, mozhno sobirat')

