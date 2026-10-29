# --- display_menu.c ---
d = open('display_menu.c', encoding='utf-8').read()

# 1. добавить vgrid в сохранение
old_save_tail = '''  fprintf(f, "freq_color_a=%.4f\\n", pan_freq_color.alpha);
  fclose(f);'''
new_save_tail = '''  fprintf(f, "freq_color_a=%.4f\\n", pan_freq_color.alpha);
  fprintf(f, "vgrid_use_custom=%d\\n", pan_vgrid_use_custom_color);
  fprintf(f, "vgrid_r=%.4f\\n", pan_vgrid_custom_color.red);
  fprintf(f, "vgrid_g=%.4f\\n", pan_vgrid_custom_color.green);
  fprintf(f, "vgrid_b=%.4f\\n", pan_vgrid_custom_color.blue);
  fprintf(f, "vgrid_a=%.4f\\n", pan_vgrid_custom_color.alpha);
  fclose(f);'''
assert old_save_tail in d, 'якорь сохранения не найден'
d = d.replace(old_save_tail, new_save_tail, 1)
print('display_menu.c: vgrid в save OK')

# 2. добавить загрузчик перед pan_text_dbm_font_cb
loader = '''
//
// UISTYLE: restore cosmetics from panadapter_grid.conf at startup
//
void pan_text_load_conf(void) {
  char path[512], line[256];
  FILE *f;
  snprintf(path, sizeof(path), "%s/piHPSDR-build-ru/panadapter_grid.conf", g_get_home_dir());
  f = fopen(path, "r");
  if (f == NULL) { return; }
  while (fgets(line, sizeof(line), f) != NULL) {
    if (sscanf(line, "use_custom_color=%d", &pan_grid_use_custom_color) == 1) {
    } else if (sscanf(line, "width=%lf", &pan_grid_width) == 1) {
      if (pan_grid_width < 0.5) pan_grid_width = 0.5;
      if (pan_grid_width > 10.0) pan_grid_width = 10.0;
    } else if (sscanf(line, "brightness=%lf", &pan_grid_brightness) == 1) {
      if (pan_grid_brightness < 0.1) pan_grid_brightness = 0.1;
      if (pan_grid_brightness > 2.0) pan_grid_brightness = 2.0;
    } else if (sscanf(line, "color_r=%lf", &pan_grid_custom_color.red) == 1) {
    } else if (sscanf(line, "color_g=%lf", &pan_grid_custom_color.green) == 1) {
    } else if (sscanf(line, "color_b=%lf", &pan_grid_custom_color.blue) == 1) {
    } else if (sscanf(line, "color_a=%lf", &pan_grid_custom_color.alpha) == 1) {
    } else if (sscanf(line, "dbm_font_size=%lf", &pan_dbm_font_size) == 1) {
      if (pan_dbm_font_size < 6.0) pan_dbm_font_size = 6.0;
      if (pan_dbm_font_size > 40.0) pan_dbm_font_size = 40.0;
    } else if (sscanf(line, "freq_font_size=%lf", &pan_freq_font_size) == 1) {
      if (pan_freq_font_size < 6.0) pan_freq_font_size = 6.0;
      if (pan_freq_font_size > 40.0) pan_freq_font_size = 40.0;
    } else if (sscanf(line, "dbm_color_r=%lf", &pan_dbm_color.red) == 1) {
    } else if (sscanf(line, "dbm_color_g=%lf", &pan_dbm_color.green) == 1) {
    } else if (sscanf(line, "dbm_color_b=%lf", &pan_dbm_color.blue) == 1) {
    } else if (sscanf(line, "dbm_color_a=%lf", &pan_dbm_color.alpha) == 1) {
    } else if (sscanf(line, "freq_color_r=%lf", &pan_freq_color.red) == 1) {
    } else if (sscanf(line, "freq_color_g=%lf", &pan_freq_color.green) == 1) {
    } else if (sscanf(line, "freq_color_b=%lf", &pan_freq_color.blue) == 1) {
    } else if (sscanf(line, "freq_color_a=%lf", &pan_freq_color.alpha) == 1) {
    } else if (sscanf(line, "vgrid_use_custom=%d", &pan_vgrid_use_custom_color) == 1) {
    } else if (sscanf(line, "vgrid_r=%lf", &pan_vgrid_custom_color.red) == 1) {
    } else if (sscanf(line, "vgrid_g=%lf", &pan_vgrid_custom_color.green) == 1) {
    } else if (sscanf(line, "vgrid_b=%lf", &pan_vgrid_custom_color.blue) == 1) {
    } else if (sscanf(line, "vgrid_a=%lf", &pan_vgrid_custom_color.alpha) == 1) {
    }
  }
  fclose(f);
}

'''
anchor_load = 'static void pan_text_dbm_font_cb(GtkWidget *widget, gpointer data) {'
assert anchor_load in d, 'якорь загрузчика не найден'
d = d.replace(anchor_load, loader + anchor_load, 1)
print('display_menu.c: load_conf OK')
open('display_menu.c', 'w', encoding='utf-8').write(d)

# --- main.c ---
m = open('main.c', encoding='utf-8').read()

old_hdr = 'void hfreq_conf_load(void) {'
assert old_hdr in m, 'якорь extern не найден'
m = m.replace(old_hdr, 'extern void pan_text_load_conf(void);\n\n' + old_hdr, 1)
print('main.c: extern OK')

old_call = '  hfreq_conf_load();'
assert old_call in m, 'якорь вызова не найден'
m = m.replace(old_call, '  hfreq_conf_load();\n  pan_text_load_conf();', 1)
print('main.c: вызов при старте OK')
open('main.c', 'w', encoding='utf-8').write(m)

for f in ('main.c', 'display_menu.c'):
    t = open(f, encoding='utf-8').read()
    print(f, 'баланс скобок:', t.count('{'), t.count('}'))
print('ALL PATCHES APPLIED')
