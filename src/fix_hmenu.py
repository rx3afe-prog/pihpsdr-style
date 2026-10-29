# --- main.c ---
s = open('main.c', encoding='utf-8').read()

anchor = 'static GtkWidget *hfreq_label = NULL;'
block = '''
//
// HEADERCFG: tunable header scale appearance
//
double hfreq_font_size = 22.0;
char hfreq_color_hex[16] = "#e01010";
char hfreq_tail_hex[16] = "#006400";

static GtkCssProvider *hfreq_css = NULL;

void hfreq_css_apply(void) {
  char css[256];
  if (hfreq_label == NULL) return;
  if (hfreq_css != NULL) {
    gtk_style_context_remove_provider(gtk_widget_get_style_context(hfreq_label),
        GTK_STYLE_PROVIDER(hfreq_css));
    g_object_unref(hfreq_css);
  }
  hfreq_css = gtk_css_provider_new();
  g_snprintf(css, sizeof(css),
      "#hfreq_label { font-size: %.0fpx; font-weight: bold; color: %s; }",
      hfreq_font_size, hfreq_color_hex);
  gtk_css_provider_load_from_data(hfreq_css, css, -1, NULL);
  gtk_style_context_add_provider(gtk_widget_get_style_context(hfreq_label),
      GTK_STYLE_PROVIDER(hfreq_css), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
}

void hfreq_conf_save(void) {
  FILE *f = fopen("header_style.props", "w");
  if (f == NULL) return;
  fprintf(f, "size=%g\\n", hfreq_font_size);
  fprintf(f, "freq=%s\\n", hfreq_color_hex);
  fprintf(f, "tail=%s\\n", hfreq_tail_hex);
  fclose(f);
}

void hfreq_conf_load(void) {
  char line[128];
  FILE *f = fopen("header_style.props", "r");
  if (f == NULL) return;
  while (fgets(line, sizeof(line), f) != NULL) {
    if (strncmp(line, "size=", 5) == 0) {
      double v = atof(line + 5);
      if (v >= 12.0 && v <= 48.0) hfreq_font_size = v;
    } else if (strncmp(line, "freq=", 5) == 0) {
      g_strlcpy(hfreq_color_hex, line + 5, sizeof(hfreq_color_hex));
      g_strchomp(hfreq_color_hex);
    } else if (strncmp(line, "tail=", 5) == 0) {
      g_strlcpy(hfreq_tail_hex, line + 5, sizeof(hfreq_tail_hex));
      g_strchomp(hfreq_tail_hex);
    }
  }
  fclose(f);
}
'''
assert anchor in s, 'anchor A not found'
s = s.replace(anchor, anchor + block, 1)
print('main.c: globals+helpers OK')

old1 = '''    g_snprintf(buf, sizeof(buf), "%lld.%03lld<span foreground=\\"#006400\\">.%03lld</span>",
               f / 1000000LL, (f / 1000LL) % 1000LL, f % 1000LL);'''
new1 = '''    g_snprintf(buf, sizeof(buf), "%lld.%03lld<span foreground=\\"%s\\">.%03lld</span>",
               f / 1000000LL, (f / 1000LL) % 1000LL, f % 1000LL, hfreq_tail_hex);'''
assert old1 in s, 'anchor B not found'
s = s.replace(old1, new1, 1)
print('main.c: markup tail color OK')

old2 = '''  GtkCssProvider *hfreq_css = gtk_css_provider_new();
  gtk_css_provider_load_from_data(hfreq_css,
      "#hfreq_label { font-size: 22px; font-weight: bold; color: #e01010; }",
      -1, NULL);
  gtk_style_context_add_provider(gtk_widget_get_style_context(hfreq_label),
      GTK_STYLE_PROVIDER(hfreq_css), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);'''
assert old2 in s, 'anchor C not found'
s = s.replace(old2, '  hfreq_css_apply();', 1)
print('main.c: dynamic CSS OK')

old3 = '  hfreq_label = gtk_label_new("0.000.000");'
assert old3 in s, 'anchor D not found'
s = s.replace(old3, '  hfreq_conf_load();\n' + old3, 1)
print('main.c: conf load OK')
open('main.c', 'w', encoding='utf-8').write(s)

# --- display_menu.c ---
d = open('display_menu.c', encoding='utf-8').read()

m_anchor = 'static void pan_text_settings_dialog_cb(GtkWidget *widget, gpointer data) {'
cb = '''
//
// HEADERCFG PATCH: header scale settings
//
extern double hfreq_font_size;
extern char hfreq_color_hex[];
extern char hfreq_tail_hex[];
extern void hfreq_css_apply(void);
extern void hfreq_conf_save(void);

static void hfreq_size_cb(GtkWidget *widget, gpointer data) {
  hfreq_font_size = gtk_range_get_value(GTK_RANGE(widget));
  hfreq_css_apply();
  hfreq_conf_save();
}

static void hfreq_color_pick_cb(GtkWidget *widget, gpointer data) {
  int which = GPOINTER_TO_INT(data);
  GdkRGBA color;
  GtkWidget *dialog;
  gboolean ok;
  if (which) {
    ok = gdk_rgba_parse(&color, hfreq_tail_hex);
  } else {
    ok = gdk_rgba_parse(&color, hfreq_color_hex);
  }
  if (!ok) {
    color.red = which ? 0.0 : 0.88;
    color.green = which ? 0.4 : 0.06;
    color.blue = which ? 0.0 : 0.06;
    color.alpha = 1.0;
  }
  dialog = gtk_color_chooser_dialog_new(which ? "Header Tail Color" : "Header Freq Color", NULL);
  gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(dialog), &color);
  if (gtk_dialog_run(GTK_DIALOG(dialog)) == GTK_RESPONSE_OK) {
    gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(dialog), &color);
    g_snprintf(which ? hfreq_tail_hex : hfreq_color_hex, 16, "#%02x%02x%02x",
        (int)(color.red * 255.0 + 0.5),
        (int)(color.green * 255.0 + 0.5),
        (int)(color.blue * 255.0 + 0.5));
    hfreq_css_apply();
    hfreq_conf_save();
  }
  gtk_widget_destroy(dialog);
}

'''
assert m_anchor in d, 'menu anchor not found'
d = d.replace(m_anchor, cb + m_anchor, 1)
print('display_menu.c: callbacks OK')

i = d.index(m_anchor)
j = d.index('  gtk_container_add(GTK_CONTAINER(gtk_dialog_get_content_area(GTK_DIALOG(dlg))), cg);', i)
rows = '''  // HEADERCFG: header scale
  l = gtk_label_new("Header Size");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 3, 1, 1);
  w = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 12.0, 48.0, 1.0);
  gtk_range_set_value(GTK_RANGE(w), hfreq_font_size);
  gtk_widget_set_size_request(w, 150, -1);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 3, 1, 1);
  g_signal_connect(w, "value-changed", G_CALLBACK(hfreq_size_cb), NULL);
  w = gtk_button_new_with_label("Header Freq Color");
  gtk_grid_attach(GTK_GRID(cg), w, 0, 4, 1, 1);
  g_signal_connect(w, "clicked", G_CALLBACK(hfreq_color_pick_cb), GINT_TO_POINTER(0));
  w = gtk_button_new_with_label("Header Tail Color");
  gtk_grid_attach(GTK_GRID(cg), w, 1, 4, 1, 1);
  g_signal_connect(w, "clicked", G_CALLBACK(hfreq_color_pick_cb), GINT_TO_POINTER(1));
'''
d = d[:j] + rows + d[j:]
print('display_menu.c: rows OK')
d = d.replace('gtk_window_set_default_size(GTK_WINDOW(dlg), 380, 240);',
              'gtk_window_set_default_size(GTK_WINDOW(dlg), 380, 300);', 1)
print('display_menu.c: dialog size OK')
open('display_menu.c', 'w', encoding='utf-8').write(d)

for f in ('main.c', 'display_menu.c'):
    t = open(f, encoding='utf-8').read()
    print(f, 'brace balance:', t.count('{'), t.count('}'))
print('ALL PATCHES APPLIED')
