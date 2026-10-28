p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

# Добавляем синхронизацию с Gain при изменении порога
M = '''        if (agc_drag == 1) {
          SetRXAAGCThresh(rx->id, rx->agc_thresh, (double)rx->afft_size, (double)rx->sample_rate);
        } else {
          SetRXAAGCHangLevel(rx->id, rx->agc_hang);
        }
        last_y = y;'''

G = '''        if (agc_drag == 1) {
          SetRXAAGCThresh(rx->id, rx->agc_thresh, (double)rx->afft_size, (double)rx->sample_rate);
          // Обновляем Gain в соответствии с новым порогом
          rx_set_agc(rx);  // Пересчитываем все параметры AGC
        } else {
          SetRXAAGCHangLevel(rx->id, rx->agc_hang);
        }
        last_y = y;'''

if M in r:
    r = r.replace(M, G, 1)
    print('OK: добавлена синхронизация с Gain')
else:
    print('!! не найдено место для вставки синхронизации')

open(p, 'w').write(r)

