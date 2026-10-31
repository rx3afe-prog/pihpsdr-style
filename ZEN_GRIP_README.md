# ZEN Grip — ручной ресайз панорамы (перенос из piHPSDR-test-29)

## Что это

Ручное изменение размера панорамы приёмника «как в старой версии»:
в правом нижнем углу панорамы (rx->panel) висит небольшой захват «◢»
(zen grip). Тянешь его мышью — панорама И окно целиком едут следом,
синхронно, за каждым пикселем руки (без ступенек и таймеров).
Двойной клик по уголку — выход из режима (Un-Z), возврат к табличному
размеру.

Перенесено из `piHPSDR-test-29/piHPSDR-style` (файл `src/receiver.c`,
блок ~775–934) в рабочую версию `piHPSDR-novaya`.

## Как это работает (коротко)

1. Нажатие на уголок: запоминаются стартовые координаты мыши
   (`x_root/y_root`) и текущие размеры панорамы, а также
   `zen_overhead` — высота окна минус высота панорамы (VFO-панель,
   слайдеры, тулбар).
2. Движение мыши: `zen_w` / `zen_h` пересчитываются, вызывается
   `radio_reconfigure()`.
3. `radio_reconfigure()` при заданных `zen_w`/`zen_h` строит панораму
   RX0 по ним (см. ZENPULL ниже).
4. `zen_fit_window()` подгоняет окно: высота окна =
   `rx->height + zen_overhead` (см. ZENOVH ниже).
5. Двойной клик: `zen_w = zen_h = 0` → система возвращается к
   табличным размерам `display_width/height[display_size]`.

Механика синхронная: никаких таймеров и порций — каждое движение мыши
даёт одну перестройку. Отсюда «гладкость».

## Изменения по файлам

### 1. `src/receiver.c` — сам захват и подгонка окна

**Определения переменных** (в 29-м были `extern`, здесь — определения,
иначе линковщик не соберёт):

```c
int zen_w = 0;   // было: extern int zen_w;
int zen_h = 0;   // было: extern int zen_h;
extern void radio_reconfigure(void);

static int zen_grip_x, zen_grip_y, zen_grip_w, zen_grip_h;
static int zen_dragging = 0;
static int zen_overhead = 0;          /* ZENOVH — надбавка окна */
static int zen_in_fit = 0;
static int zen_pending_w = -1, zen_pending_h = -1;
static int zen_min_w = -1, zen_min_h = -1;
static int zen_retry_count = 0;
static guint zen_retry_source = 0;
```

**Весь дзен-блок функций** вставлен в `receiver.c` ПЕРЕД
`void rx_reconfigure(RECEIVER *rx, int height) {`:

- `zen_reset_fit()` — сброс отложенной подгонки;
- `zen_grip_press_cb()` — нажатие; двойной клик = un-zen;
- `zen_grip_motion_cb()` — пересчёт `zen_w/zen_h` и
  `radio_reconfigure()`; ограничения: min 200(+2*INSET) x 150,
  max 3840x2160;
- `zen_reposition_unzen()` — позиционирование кнопки "Un-Z";
- `zen_check_resize()` — проверка, что окно дошло до запрошенного
  размера; при невозможности сжаться запоминает фактический минимум
  (`[zen] min floor: WxH`);
- `zen_fit_window()` — ресайз окна под панораму + retries
  (g_timeout_add 120 мс);
- `zen_ensure_grip()` — создаёт GtkEventBox c меткой «◢» (28x28),
  вешает сигналы, кладёт в `rx->panel` (GtkFixed), двигает в правый
  нижний угол; перед перемещением снимает/вставляет уголок заново,
  чтобы он всегда был ВЕРХНИМ виджетом (панорама при перестройках
  иначе ложится поверх); вызывает `zen_reposition_unzen()` и
  `zen_fit_window()`.

**Вызов** в конце `rx_reconfigure()`, сразу после
`gtk_widget_show_all(rx->panel);`:

```c
  gtk_widget_show_all(rx->panel);
  zen_ensure_grip(rx);   /* ZENPULL-2 */
}
```

### 2. ZENOVH — надбавка окна над панорамой (ВАЖНО для новой версии)

В новой версии в окне, кроме панорамы, живут VFO-панель, слайдеры и
тулбар (~95 px). Если ресайзить окно в голый `rx->height`, окно
обрезается на величину надбавки и рамка «наезжает» на уголок.
Решение — при нажатии на уголок измерить фактическую разницу и
прибавлять её:

- `static int zen_overhead = 0;` — новая статика;
- в `zen_grip_press_cb()` (после сохранения `zen_grip_w/h`):

```c
  {
    GtkWidget *tl = gtk_widget_get_toplevel(GTK_WIDGET(w));
    gint ww2, wh2;
    if (tl != NULL && GTK_IS_WINDOW(tl)) {
      gtk_window_get_size(GTK_WINDOW(tl), &ww2, &wh2);
      zen_overhead = wh2 - rx->height;
      if (zen_overhead < 0) zen_overhead = 0;
      g_print("ZGRIP: overhead=%d\n", zen_overhead);
    }
  }
```

- в `zen_fit_window()`:

```c
  nw = rx->width;
  nh = rx->height + zen_overhead;                      /* ZENOVH */
  ...
  if (nh < 150 + zen_overhead) { nh = 150 + zen_overhead; zen_h = 150; clamped = 1; }
  ...
  if (zen_min_h > 0 && nh < zen_min_h) { nh = zen_min_h; zen_h = zen_min_h - zen_overhead; clamped = 1; }
```

Примечание: `zen_min_h` хранит минимальную ВЫСОТУ ОКНА (с надбавкой),
поэтому при пересчёте в `zen_h` она вычитается. При скрытии VFO/тулбара
(кнопка Hide) надбавка сама становится ~0 — поведение совпадает со
старой версией один в один.

### 3. `src/radio.c` — ZENPULL: слушаться руки

После `#include` добавить:

```c
extern int zen_w;
extern int zen_h;   /* ZENPULL */
```

В `radio_reconfigure()` в блоках раскладки (горизонтальный и
вертикальный — там, где `rx_reconfigure(rx, rx_height)`) заменить:

```c
      rx->width = my_width / receivers - 2 * RX_DISPLAY_INSET;
      rx_reconfigure(rx, rx_height);
```

на:

```c
      rx->width = (rx->id == 0 && zen_w > 0 ? zen_w : my_width / receivers) - 2 * RX_DISPLAY_INSET;  /* ZENPULL */
      rx_update_width(rx);
      rx_reconfigure(rx, (rx->id == 0 && zen_h > 0) ? zen_h : rx_height);                            /* ZENPULL */
```

Действует только на RX0 (id==0) — как в 29-м. Если `zen_w/zen_h == 0`,
работают табличные размеры, т.е. без перетаскивания поведение не
меняется.

## Как переносить на будущую новую версию (чек-лист)

Все правки помечены маркерами — по ним легко найти всё:

- `ZENPULL` — в `radio.c` (2-3 строки);
- `ZENOVH` — в `receiver.c` (4 места);
- `ZENPULL-2` — вызов `zen_ensure_grip` (1 место).

Порядок:

1. Взять блок функций `zen_*` из эталона (29-й, `receiver.c` ~775–934)
   и вставить в новый `receiver.c` ПЕРЕД `rx_reconfigure`.
   **ВНИМАНИЕ:** граница вырезки — блок должен закончиться закрывающей
   `}` функции `zen_ensure_grip`! Мы уже один раз теряли финальную
   скобку — компилятор выдаёт `expected identifier or ‘(’ before ‘}’`
   на строке ПОСЛЕ блока (на `void rx_reconfigure...`). Если увидел
   такую ошибку — ищи потерянную/лишнюю `}` на стыке.
2. Заменить `extern int zen_w; / extern int zen_h;` в блоке на
   определения `int zen_w = 0; / int zen_h = 0;` (в новой версии они
   никто другой не определяет).
3. Вставить вызов `zen_ensure_grip(rx);` после
   `gtk_widget_show_all(rx->panel);` в КОНЦЕ `rx_reconfigure`
   (в `receiver.c` может быть несколько `show_all` — нужен тот, что в
   конце этой функции).
4. Применить правки ZENOVH (см. выше).
5. В `radio.c`: `extern int zen_w; extern int zen_h;` после include'ов
   и замены ZENPULL в блоках раскладки (найти по
   `rx_reconfigure(rx, rx_height)`).
6. `make -j4` — обязательно убедиться, что пройдена ЛИНКОВКА
   (сборка может молча взять старый .o, если компиляция упала, а
   запускать будешь старый бинарник; смотри дату сборки в логе:
   `activate_pihpsdr: Build: v2.451 (Date: ...)`).
7. Проверить в логе: `ZGRIP: at X,Y panel w=W h=H` при старте и
   `ZGRIP: overhead=NN` (~95 при полном интерфейсе, 0 при Hide).
8. Тянуть «◢» в правом нижнем углу панорамы. Двойной клик — un-zen.

## Грабли, на которые мы наступили (не наступать снова)

- Потерянная закрывающая скобка блока при вставке — сборка падает,
  а старый бинарник продолжает работать (и кажется, что «правки не
  применились»). Всегда сверять дату сборки в логе.
- Уголок «под панорамой»: `zen_ensure_grip` снимает и заново кладёт
  уголок в GtkFixed, чтобы он оставался верхним виджетом — не удалять
  этот блок.
- Ресайз окна в голый `rx->height` — рамка наезжает на уголок. Нужен
  ZENOVH.
- Строчные sed-замены по номерам строк хрупкие — лучше по контексту
  (маркеры), либо python с assert'ами.

## Отладка

- `ZGRIP: at X,Y panel w=W h=H` — позиция уголка при каждой
  перестройке;
- `ZGRIP: overhead=NN` — измеренная надбавка окна при нажатии;
- `[zen] min floor: WxH` — фактический минимальный размер окна
  (обнаружен retries-механизмом);
- `[zen] ...` прочее.

Эти строки можно убрать в «тихой» сборке, но пока лучше оставить —
они сразу показывают, жив ли механизм после обновлений.

## Бэкапы

- `src/receiver.c.bak-zen` — до первого переноса;
- `src/receiver.c.bak-grip2` — до правки слоя (уголок наверху);
- `src/receiver.c.bak-ovh` — до ZENOVH;
- `src/radio.c.bak-zen` — до ZENPULL.
