p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
start = r.find('/* ZMHFN:')
end = r.find('/* ZMHTIMER:')
if start == -1 or end == -1 or end <= start:
    print('!! granicy funkcii ne najdeny, nichego ne menyal')
    raise SystemExit(1)

new_fn = '''/* ZMHFN: obschaya funkciya podnyatiya knopok M/H */
static void zmh_raise(void) {
  static int zrn = 0;
  zrn++;
  if (!GTK_IS_WIDGET(menu_b) || !GTK_IS_WIDGET(hide_b)) {
    if (zrn % 20 == 1) { g_print("ZMH5: ozhidanie, menu_b=%p hide_b=%p\\n", (void*)menu_b, (void*)hide_b); }
    return;
  }
  /* ZMHTB2: verhnyaya polosa - zagolovok okna */
  GtkWidget *tb = gtk_window_get_titlebar(GTK_WINDOW(top_window));
  if (!(tb && GTK_IS_HEADER_BAR(tb))) {
    if (zrn % 50 == 1) { g_print("ZMH5: titlebar=%s\\n", tb ? G_OBJECT_TYPE_NAME(tb) : "NULL"); }
    return;
  }
  GtkWidget *pm = gtk_widget_get_parent(menu_b);
  GtkWidget *ph = gtk_widget_get_parent(hide_b);
  if (zrn <= 8) {
    g_print("ZMH5: menu_b=%p pm=%p | hide_b=%p ph=%p\\n", (void*)menu_b, (void*)pm, (void*)hide_b, (void*)ph);
  }
  /* ZMH5GUARD: perenosim tolko esli tekuwij roditel - zhivoj widget */
  if (pm && GTK_IS_WIDGET(pm) && pm != tb) {
    g_object_ref(menu_b);
    gtk_container_remove(GTK_CONTAINER(pm), menu_b);
    g_object_unref(menu_b);
    gtk_header_bar_pack_start(GTK_HEADER_BAR(tb), menu_b);
    gtk_widget_set_size_request(menu_b, 70, 32);
    gtk_widget_set_name(menu_b, "zmh-btn");
    gtk_widget_show(menu_b);
  }
  if (ph && GTK_IS_WIDGET(ph) && ph != tb) {
    g_object_ref(hide_b);
    gtk_container_remove(GTK_CONTAINER(ph), hide_b);
    g_object_unref(hide_b);
    gtk_header_bar_pack_end(GTK_HEADER_BAR(tb), hide_b);
    gtk_widget_set_size_request(hide_b, 70, 32);
    gtk_widget_set_name(hide_b, "zmh-btn");
    gtk_widget_show(hide_b);
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
    print('!! v novoj funkcii neraven skobok, otkaz')
    raise SystemExit(1)
r = r[:start] + new_fn + r[end:]
open(p, 'w').write(r)
print('VSE: funkciya perpisana: sprosit, potom sdelaet, musora ne tronet')

