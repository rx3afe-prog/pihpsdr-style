p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

old1 = '''  int bym = 2;  /* ZMHLIFT */
  if (bym < 4) { bym = 4; }
  if (bym < 0) { bym = 0; }'''
new1 = '''  int bym = 2;  /* ZMHLIFT: samyj verh, bez zashchity */'''

if old1 in r:
    r = r.replace(old1, new1)
    print('OK: zashchita udalena, bym=2 chistyj')
elif new1 in r:
    print('OK: bym uzhe chistyj')
else:
    print('!! blok bym ne najden'); ok = False

old2 = '''  if ((zrn++) % 50 == 0) {
    g_print("ZMH: raise w=%d pan_y=%d pan_h=%d btn_y=%d\\n", wfx, vy, vh, bym);
  }'''
new2 = '''  zrn++;
  /* ZMHREAL: realnye koordinaty knopki i polosy cifr ot verha okna */
  { int axx = 0, ayy = 0, vxx = 0, vyy = 0, vhh = 0;
    if (GTK_IS_WIDGET(menu_b)) { gtk_widget_translate_coordinates(menu_b, top_window, 0, 0, &axx, &ayy); }
    if (GTK_IS_WIDGET(vfo_panel)) {
      gtk_widget_translate_coordinates(vfo_panel, top_window, 0, 0, &vxx, &vyy);
      vhh = gtk_widget_get_allocated_height(vfo_panel);
    }
    g_print("ZMH: btn_y=%d real_x=%d real_y=%d | vfo_y=%d vfo_h=%d\\n", bym, axx, ayy, vyy, vhh);
  }'''

if 'ZMHREAL' in r:
    print('OK: log uzhe obnovlen')
elif old2 in r:
    r = r.replace(old2, new2)
    print('OK: log zamenen na realnye koordinaty')
else:
    print('!! blok loga ne najden'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

