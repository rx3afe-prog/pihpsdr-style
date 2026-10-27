lines = open('main.c.hbar.bak', encoding='utf-8', errors='replace').read().splitlines(True)

BLOCK_A = '''//
// ZFREQ: digital scale in the title bar
//
static GtkWidget *hfreq_label = NULL;

static gboolean hfreq_update_cb(gpointer data) {
  char buf[64];
  if (hfreq_label != NULL && GTK_IS_WIDGET(hfreq_label)) {
    long long f = vfo[VFO_A].frequency;
    g_snprintf(buf, sizeof(buf), "%lld.%03lld.%03lld",
               f / 1000000LL, (f / 1000LL) % 1000LL, f % 1000LL);
    gtk_label_set_text(GTK_LABEL(hfreq_label), buf);
  }
  return G_SOURCE_CONTINUE;
}
'''

BLOCK_B = '''  //
  // ZFREQ: custom title bar with digital scale and buttons
  //
  hfreq_label = gtk_label_new("0.000.000");
  gtk_widget_set_name(hfreq_label, "hfreq_label");
  GtkCssProvider *hfreq_css = gtk_css_provider_new();
  gtk_css_provider_load_from_data(hfreq_css,
      "#hfreq_label { font-size: 22px; font-weight: bold; color: #e01010; }",
      -1, NULL);
  gtk_style_context_add_provider(gtk_widget_get_style_context(hfreq_label),
      GTK_STYLE_PROVIDER(hfreq_css), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
  GtkWidget *hbar = gtk_header_bar_new();
  gtk_header_bar_set_custom_title(GTK_HEADER_BAR(hbar), hfreq_label);
  gtk_header_bar_set_show_close_button(GTK_HEADER_BAR(hbar), TRUE);
  GtkWidget *hmin = gtk_button_new_from_icon_name("window-minimize-symbolic",
      GTK_ICON_SIZE_MENU);
  g_signal_connect_swapped(hmin, "clicked",
      G_CALLBACK(gtk_window_iconify), top_window);
  gtk_header_bar_pack_end(GTK_HEADER_BAR(hbar), hmin);
  gtk_window_set_titlebar(GTK_WINDOW(top_window), hbar);
  g_timeout_add(200, hfreq_update_cb, NULL);
'''

out, a, b = [], False, False
for ln in lines:
    out.append(ln)
    if not a and 'GtkWidget *top_window = NULL;' in ln:
        out.append(BLOCK_A + '\n')
        a = True
    elif not b and 'gtk_window_set_title (GTK_WINDOW (top_window), "piHPSDR-Improved")' in ln:
        out.append(BLOCK_B)
        b = True
open('main.c', 'w', encoding='utf-8').write(''.join(out))
print('main.c : blockA=%s blockB=%s' % (a, b))
