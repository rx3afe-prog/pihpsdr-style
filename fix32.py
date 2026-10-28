p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

old = '''  int vy = 0, vh = 0;
  if (GTK_IS_WIDGET(vfo_panel) && gtk_widget_get_parent(vfo_panel) == fixed) {
    int vtop = 0;
    if (gtk_widget_translate_coordinates(vfo_panel, fixed, 0, 0, NULL, &vtop)) { vy = vtop; }
    vh = gtk_widget_get_allocated_height(vfo_panel);
  }
  if (vh <= 1) { vh = VFO_HEIGHT; }
  int bym = vy + (vh - 22) / 2 - 12;
  if (bym < 0) { bym = 0; }'''

new = '''  int vy = 0, vh = 0;
  /* ZMHPAN: orientir - verh panadaptera, polosa chastotnyh cifr */
  if (receiver[0] != NULL && GTK_IS_WIDGET(receiver[0]->panel)) {
    int ptop = 0;
    if (gtk_widget_translate_coordinates(receiver[0]->panel, fixed, 0, 0, NULL, &ptop)) { vy = ptop; }
    vh = gtk_widget_get_allocated_height(receiver[0]->panel);
  }
  int bym = vy + 2;
  if (bym < 0) { bym = 0; }'''

n = r.count(old)
if 'ZMHPAN' in r:
    print('OK: uzhe sdelano')
elif n >= 1:
    r = r.replace(old, new)
    print('OK: formula zamenena')
else:
    print('!! staryj blok formuly ne najden'); ok = False

old2 = 'g_print("ZMH: raise w=%d vfo_y=%d vfo_h=%d btn_y=%d\\n", wfx, vy, vh, bym);'
new2 = 'g_print("ZMH: raise w=%d pan_y=%d pan_h=%d btn_y=%d\\n", wfx, vy, vh, bym);'
if old2 in r:
    r = r.replace(old2, new2)
    print('OK: log pereimenovan na pan_y/pan_h')
else:
    print('OK: stroka loga uzhe obnovlena ili ne najdena')

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

