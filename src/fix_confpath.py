d = open('display_menu.c', encoding='utf-8').read()
old = 'snprintf(path, sizeof(path), "%s/piHPSDR-build-ru/panadapter_grid.conf", g_get_home_dir());'
assert d.count(old) == 2, 'ожидалось 2 вхождения пути, найдено %d' % d.count(old)
d = d.replace(old, 'snprintf(path, sizeof(path), "panadapter_grid.conf");')
open('display_menu.c', 'w', encoding='utf-8').write(d)
print('путь исправлен в save и load (2 места)')
