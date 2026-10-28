p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

old = '''  int vy = 0, vh = 0;
  /* ZMHPAN: orientir - verh panadaptera, polosa chastotnyh cifr */
  if (receiver[0] != NULL && GTK_IS_WIDGET(receiver[0]->panel)) {
    int ptop = 0;
    if (gtk_widget_translate_coordinates(receiver[0]->panel, fixed, 0, 0, NULL, &ptop)) { vy = ptop; }
    vh = gtk_widget_get_allocated_height(receiver[0]->panel);
  }
  /* ZMHVFO: centriruem v Verhnej polose (stroka s krupnoj cifroj chastoty) */
  int bym = (vy - 22) / 2;
  if (bym < 4) { bym = 4; }'''

new = '''  int vy = 0, vh = 0;
  /* ZMHFIXED: verh polosa - polosVFO vysotoj VFO_HEIGHT, centerim v nej */
  vy = 0;
  vh = VFO_HEIGHT;
  int bym = vy + (vh - 22) / 2;
  if (bym < 4) { bym = 4; }'''

n = r.count(old)
if 'ZMHFIXED' in r:
    print('OK: uzhe sdelano')
elif n >= 1:
    r = r.replace(old, new)
    print('OK: blok zamenen na konstantu VFO_HEIGHT')
else:
    print('!! staryj blok ne najden'); ok = False

if r.count('{') != r.count('}'):
    print('!! balans skobok narushen, zapisi ne budet'); ok = False
if ok:
    open(p, 'w').write(r)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi NE sdelana')
    raise SystemExit(1)

