# --- 1. radio.c: sohranyaem ssylku na zen-ruchku AGC ---
p = '/home/rx3afe/piHPSDR-style/src/radio.c'
r = open(p).read()
ok = True

if 'zen_agc_scale' not in r:
    a = 'static GtkWidget *zen_r2 = NULL;'
    if a not in r:
        print('1. !! ne naydeno mesto dlya globalnoj ssylki')
        ok = False
    else:
        r = r.replace(a, a + '\nstatic GtkWidget *zen_agc_scale = NULL;', 1)
        print('1. OK: globalnaya ssylka dobavlena')
else:
    print('1. OK: globalnaya ssylka uzhe est')

# --- 2. radio.c: zapominaem ruchku pri sozdanii paneli ---
mark = '  if (active_receiver) gtk_range_set_value(GTK_RANGE(bw), (active_receiver->agc_gain + 20.0) / 1.4);'
if mark not in r:
    print('2. !! stroka sozdaniya ruchki AGC ne naydena')
    ok = False
elif 'zen_agc_scale = bw;' not in r:
    r = r.replace(mark, mark + '\n  zen_agc_scale = bw;', 1)
    print('2. OK: ruchka zapominaetsya pri sozdanii')
else:
    print('2. OK: zapominanie uzhe stoit')

# --- 3. radio.c: funkciya sinkronizacii v konce fajla ---
if 'void zen_agc_slider_sync(int id)' not in r:
    r += '''
void zen_agc_slider_sync(int id) {
  if (!zen_agc_scale || !GTK_IS_WIDGET(zen_agc_scale)) return;
  if (!receiver[id]) return;
  double v = (receiver[id]->agc_gain + 20.0) / 1.4;
  if (v < 0.0) v = 0.0;
  if (v > 100.0) v = 100.0;
  gtk_range_set_value(GTK_RANGE(zen_agc_scale), v);
}
'''
    print('3. OK: funkciya zen_agc_slider_sync dobavlena')
else:
    print('3. OK: funkciya uzhe est')

# --- 4. receiver.c: zamenyaem vyzov starogo polzunka na zen-sinkronizaciyu ---
p2 = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r2 = open(p2).read()
old = ('\n            extern int sliders_agc_gain(gpointer data);\n'
       '            sliders_agc_gain(GINT_TO_POINTER(rx->id));')
new = ('\n            extern void zen_agc_slider_sync(int id);\n'
       '            zen_agc_slider_sync(rx->id);')
if old in r2:
    r2 = r2.replace(old, new, 1)
    print('4. OK: v receiver.c teper vyzivaetsya zen-sinkronizaciya')
elif 'zen_agc_slider_sync(rx->id);' in r2:
    print('4. OK: zen-sinkronizaciya uzhe stoit')
else:
    print('4. !! staryj vyzov v receiver.c ne najden')
    ok = False

# --- 5. sliders.c: ubiraem diagnostiku ZSYNC ---
p3 = '/home/rx3afe/piHPSDR-style/src/sliders.c'
r3 = open(p3).read()
i = r3.find('  fprintf(stderr, "ZSYNC:')
if i >= 0:
    j = r3.find('receiver[id]->agc_gain);', i)
    if j > 0:
        j += len('receiver[id]->agc_gain);')
        if r3[i - 1] == '\n':
            i -= 1
        r3 = r3[:i] + r3[j:]
        open(p3, 'w').write(r3)
        print('5. OK: diagnostika ZSYNC udalena')
    else:
        print('5. !! konec diagnostiki ne najden, ne trogaju')
else:
    print('5. OK: diagnostiki ZSYNC uzhe net')

if r2.count('{') != r2.count('}'):
    print('!! balans skobok v receiver.c, nichego ne zapisano')
    ok = False

if ok:
    open(p, 'w').write(r)
    open(p2, 'w').write(r2)
    print('VSE: zapisano, mozhno sobirat')
else:
    print('!! est oshibki, zapisi ne budet')
    raise SystemExit(1)

