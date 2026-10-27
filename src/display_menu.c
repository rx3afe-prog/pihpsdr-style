/* Copyright (C)
*  2015 - John Melton, G0ORX/N6LYT
*  2025 - Christoph van Wüllen, DL1YCF
*
*   This program is free software: you can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   This program is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU General Public License for more details.
*
*   You should have received a copy of the GNU General Public License
*   along with this program.  If not, see <https://www.gnu.org/licenses/>.
*
*/

#include <gtk/gtk.h>
#include <string.h>

#include "client_server.h"
#include "main.h"
#include "new_menu.h"
#include "radio.h"
#include "toolbar.h"

enum _containers {
  RX1_CONTAINER = 0,
  RX2_CONTAINER,
  TX_CONTAINER
};

static int which_container = RX1_CONTAINER;


static GtkWidget *rx1_container;
static GtkWidget *rx2_container;
static GtkWidget *tx_container;

static GtkWidget *dialog = NULL;

//
// Level spinners of the RX settings, kept such that they can be updated
// when the levels change (e.g. due to a band change). Indexed by receiver id.
//
static GtkWidget *pan_high_spin[2];
static GtkWidget *pan_low_spin[2];
static GtkWidget *wf_high_spin[2];
static GtkWidget *wf_low_spin[2];
static gulong pan_high_signal[2];
static gulong pan_low_signal[2];
static gulong wf_high_signal[2];
static gulong wf_low_signal[2];

//
// This guards against changing the active receiver while the
// menu is open
//
static void cleanup(void) {
  if (dialog != NULL) {
    GtkWidget *tmp = dialog;
    dialog = NULL;
    gtk_widget_destroy(tmp);
    memset(pan_high_spin, 0, sizeof(pan_high_spin));
    memset(pan_low_spin, 0, sizeof(pan_low_spin));
    memset(wf_high_spin, 0, sizeof(wf_high_spin));
    memset(wf_low_spin, 0, sizeof(wf_low_spin));
    sub_menu = NULL;
    active_menu  = NO_MENU;
    radio_save_state();
  }
}

static void set_spin(GtkWidget *spin, gulong signal_id, int value) {
  if (spin != NULL) {
    g_signal_handler_block(G_OBJECT(spin), signal_id);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(spin), (double)value);
    g_signal_handler_unblock(G_OBJECT(spin), signal_id);
  }
}

int display_menu_update_levels(gpointer data) {
  //
  // Called (via g_idle_add) whenever panadapter or waterfall levels
  // change, e.g. at a band change. Moves the spinners without
  // triggering their callbacks.
  //
  if (dialog != NULL) {
    for (int id = 0; id < receivers && id < 2; id++) {
      const RECEIVER *rx = receiver[id];
      set_spin(pan_high_spin[id], pan_high_signal[id], rx->panadapter_high);
      set_spin(pan_low_spin[id],  pan_low_signal[id],  rx->panadapter_low);
      set_spin(wf_high_spin[id],  wf_high_signal[id],  rx->waterfall_high);
      set_spin(wf_low_spin[id],   wf_low_signal[id],   rx->waterfall_low);
    }
  }

  return G_SOURCE_REMOVE;
}

static gboolean close_cb(void) {
  cleanup();
  return TRUE;
}

static void sel_cb(GtkWidget *widget, gpointer data) {
  //
  // Handle radio button in the top row, this selects
  // which sub-menu is active
  //
  int c = GPOINTER_TO_INT(data);
  GtkWidget *my_container;

  switch (c) {
  case RX1_CONTAINER:
    my_container = rx1_container;
    break;

  case RX2_CONTAINER:
    my_container = rx2_container;
    break;

  case TX_CONTAINER:
    my_container = tx_container;
    break;

  default:
    // We should never come here
    my_container = NULL;
    break;
  }

  if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget))) {
    gtk_widget_show(my_container);
    which_container = c;
  } else {
    gtk_widget_hide(my_container);
  }
}

static void detector_cb(GtkToggleButton *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  int val = gtk_combo_box_get_active (GTK_COMBO_BOX(widget));

  switch (val) {
  case 0:
    myrx->display_detector_mode = DET_PEAK;
    break;

  case 1:
    myrx->display_detector_mode = DET_ROSENFELL;
    break;

  case 2:
    myrx->display_detector_mode = DET_AVERAGE;
    break;

  case 3:
    myrx->display_detector_mode = DET_SAMPLEHOLD;
    break;
  }

  if (radio_is_remote) {
    send_display(cl_sock_tcp, myrx->id);
  } else {
    rx_set_detector(myrx);
  }
}

static void average_cb(GtkToggleButton *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  int val = gtk_combo_box_get_active (GTK_COMBO_BOX(widget));

  switch (val) {
  case 0:
    myrx->display_average_mode = AVG_NONE;
    break;

  case 1:
    myrx->display_average_mode = AVG_RECURSIVE;
    break;

  case 2:
    myrx->display_average_mode = AVG_TIMEWINDOW;
    break;

  case 3:
    myrx->display_average_mode = AVG_LOGRECURSIVE;
    break;
  }

  if (radio_is_remote) {
    send_display(cl_sock_tcp, myrx->id);
  } else {
    rx_set_average(myrx);
  }
}

extern double panadapter_line_width;

static void panadapter_line_width_value_changed_cb(GtkWidget *widget, gpointer data) {
  panadapter_line_width = gtk_range_get_value(GTK_RANGE(widget));
}

extern double pan_grid_width;
extern GdkRGBA pan_grid_custom_color;
extern int pan_grid_use_custom_color;
extern double pan_grid_brightness;
/* === PAN TEXT UI PATCH: цвет и размер подписей === */
#include <stdio.h>
extern double pan_dbm_font_size;
extern double pan_freq_font_size;
extern int pan_vgrid_use_custom_color;   /* VGRID PATCH */
extern GdkRGBA pan_vgrid_custom_color;
extern int pan_filter_use_custom_color;  /* COLORSET PATCH */
extern GdkRGBA pan_filter_custom_color;
extern double pan_filter_brightness;
extern int vfo_dial_use_custom_color;   /* DIALCSS PATCH */
extern GdkRGBA vfo_dial_custom_color;
extern double vfo_dial_size_scale;
extern int tb_use_custom;
extern GdkRGBA tb_custom_color;
extern double tb_brightness;
extern double tb_font_size;
extern int vfo_status_use_custom;    /* PSTEXT PATCH */
extern GdkRGBA vfo_status_color;
extern double vfo_status_brightness;
extern double vfo_status_size_scale;
extern GdkRGBA pan_dbm_color;
extern GdkRGBA pan_freq_color;

static void pan_text_save_conf(void) {
  FILE *f;
  char path[512];
  snprintf(path, sizeof(path), "panadapter_grid.conf");
  f = fopen(path, "w");
  if (f == NULL) { return; }
  fprintf(f, "use_custom_color=%d\n", pan_grid_use_custom_color);
  fprintf(f, "width=%.2f\n", pan_grid_width);
  fprintf(f, "brightness=%.2f\n", pan_grid_brightness);
  fprintf(f, "color_r=%.4f\n", pan_grid_custom_color.red);
  fprintf(f, "color_g=%.4f\n", pan_grid_custom_color.green);
  fprintf(f, "color_b=%.4f\n", pan_grid_custom_color.blue);
  fprintf(f, "color_a=%.4f\n", pan_grid_custom_color.alpha);
  fprintf(f, "dbm_font_size=%.2f\n", pan_dbm_font_size);
  fprintf(f, "freq_font_size=%.2f\n", pan_freq_font_size);
  fprintf(f, "dbm_color_r=%.4f\n", pan_dbm_color.red);
  fprintf(f, "dbm_color_g=%.4f\n", pan_dbm_color.green);
  fprintf(f, "dbm_color_b=%.4f\n", pan_dbm_color.blue);
  fprintf(f, "dbm_color_a=%.4f\n", pan_dbm_color.alpha);
  fprintf(f, "freq_color_r=%.4f\n", pan_freq_color.red);
  fprintf(f, "freq_color_g=%.4f\n", pan_freq_color.green);
  fprintf(f, "freq_color_b=%.4f\n", pan_freq_color.blue);
  fprintf(f, "freq_color_a=%.4f\n", pan_freq_color.alpha);
  fprintf(f, "vgrid_use_custom=%d\n", pan_vgrid_use_custom_color);
  fprintf(f, "vgrid_r=%.4f\n", pan_vgrid_custom_color.red);
  fprintf(f, "vgrid_g=%.4f\n", pan_vgrid_custom_color.green);
  fprintf(f, "vgrid_b=%.4f\n", pan_vgrid_custom_color.blue);
  fprintf(f, "vgrid_a=%.4f\n", pan_vgrid_custom_color.alpha);
  fclose(f);
}


//
// UISTYLE: restore cosmetics from panadapter_grid.conf at startup
//
void pan_text_load_conf(void) {
  char path[512], line[256];
  FILE *f;
  snprintf(path, sizeof(path), "panadapter_grid.conf");
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

static void pan_text_dbm_font_cb(GtkWidget *widget, gpointer data) {
  pan_dbm_font_size = gtk_spin_button_get_value(GTK_SPIN_BUTTON(widget));
  pan_text_save_conf();
}

static void pan_text_freq_font_cb(GtkWidget *widget, gpointer data) {
  pan_freq_font_size = gtk_spin_button_get_value(GTK_SPIN_BUTTON(widget));
  pan_text_save_conf();
}

static void pan_text_color_cb(GtkWidget *widget, gpointer data); /* PAN TEXT FWD PATCH */
static void color_filter_custom_cb(GtkWidget *widget, gpointer data) { /* COLORSET PATCH */
  pan_filter_use_custom_color = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}
static void color_filter_color_cb(GtkWidget *widget, gpointer data) {
  gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(widget), &pan_filter_custom_color);
}
static void color_filter_brightness_cb(GtkWidget *widget, gpointer data) {
  pan_filter_brightness = gtk_range_get_value(GTK_RANGE(widget));
}
static GtkCssProvider *tb_provider = NULL;   /* DIALCSS PATCH */
void tb_css_apply(void) {
  char css[256];
  if (tb_provider == NULL) {
    tb_provider = gtk_css_provider_new();
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(), GTK_STYLE_PROVIDER(tb_provider), GTK_STYLE_PROVIDER_PRIORITY_USER);
  }
  if (tb_use_custom) {
    snprintf(css, sizeof(css), ".tbbtn label { color: rgba(%d, %d, %d, %.2f); font-size: %dpx; }",
      (int)(tb_custom_color.red * 255.0), (int)(tb_custom_color.green * 255.0),
      (int)(tb_custom_color.blue * 255.0), tb_brightness, (int)tb_font_size);
  } else {
    css[0] = 0;
  }
  gtk_css_provider_load_from_data(tb_provider, css, -1, NULL);
}
static void vfo_dial_use_custom_cb(GtkWidget *widget, gpointer data) {
  vfo_dial_use_custom_color = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}
static void vfo_dial_color_cb(GtkWidget *widget, gpointer data) {
  gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(widget), &vfo_dial_custom_color);
}
static void vfo_dial_size_cb(GtkWidget *widget, gpointer data) {
  vfo_dial_size_scale = gtk_range_get_value(GTK_RANGE(widget));
}
static void tb_use_custom_cb(GtkWidget *widget, gpointer data) {
  tb_use_custom = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
  tb_css_apply();
}
static void tb_color_cb(GtkWidget *widget, gpointer data) {
  gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(widget), &tb_custom_color);
  tb_css_apply();
}
static void tb_brightness_cb(GtkWidget *widget, gpointer data) {
  tb_brightness = gtk_range_get_value(GTK_RANGE(widget));
  tb_css_apply();
}
static void tb_font_cb(GtkWidget *widget, gpointer data) {
  tb_font_size = gtk_range_get_value(GTK_RANGE(widget));
  tb_css_apply();
}
static void vfo_status_use_custom_cb(GtkWidget *widget, gpointer data) { /* PSTEXT PATCH */
  vfo_status_use_custom = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}
static void vfo_status_color_cb(GtkWidget *widget, gpointer data) {
  gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(widget), &vfo_status_color);
}
static void vfo_status_brightness_cb(GtkWidget *widget, gpointer data) {
  vfo_status_brightness = gtk_range_get_value(GTK_RANGE(widget));
}
static void vfo_status_size_cb(GtkWidget *widget, gpointer data) {
  vfo_status_size_scale = gtk_range_get_value(GTK_RANGE(widget));
}
static void color_settings_dialog_cb(GtkWidget *widget, gpointer data) {
  GtkWidget *dlg = gtk_dialog_new();
  GtkWidget *cg = gtk_grid_new();
  GtkWidget *l, *w;
  gtk_window_set_title(GTK_WINDOW(dlg), "Color Settings");
  gtk_window_set_default_size(GTK_WINDOW(dlg), 380, 220);
  gtk_grid_set_row_spacing(GTK_GRID(cg), 5);
  gtk_grid_set_column_spacing(GTK_GRID(cg), 5);
  l = gtk_label_new("Filter Custom");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 0, 1, 1);
  w = gtk_check_button_new();
  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), pan_filter_use_custom_color);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 0, 1, 1);
  g_signal_connect(w, "toggled", G_CALLBACK(color_filter_custom_cb), NULL);
  l = gtk_label_new("Filter Color");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 1, 1, 1);
  w = gtk_color_button_new();
  gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(w), &pan_filter_custom_color);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 1, 1, 1);
  g_signal_connect(w, "color-set", G_CALLBACK(color_filter_color_cb), NULL);
  l = gtk_label_new("Filter Brightness");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 2, 1, 1);
  w = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0.0, 2.0, 0.05);
  gtk_range_set_value(GTK_RANGE(w), pan_filter_brightness);
  gtk_widget_set_size_request(w, 150, -1);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 2, 1, 1);
  g_signal_connect(w, "value-changed", G_CALLBACK(color_filter_brightness_cb), NULL);
  l = gtk_label_new("Dial Custom");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 3, 1, 1);
  w = gtk_check_button_new();
  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), vfo_dial_use_custom_color);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 3, 1, 1);
  g_signal_connect(w, "toggled", G_CALLBACK(vfo_dial_use_custom_cb), NULL);
  l = gtk_label_new("Dial Color");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 4, 1, 1);
  w = gtk_color_button_new();
  gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(w), &vfo_dial_custom_color);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 4, 1, 1);
  g_signal_connect(w, "color-set", G_CALLBACK(vfo_dial_color_cb), NULL);
  l = gtk_label_new("Dial Size");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 5, 1, 1);
  w = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0.5, 2.0, 0.05);
  gtk_range_set_value(GTK_RANGE(w), vfo_dial_size_scale);
  gtk_widget_set_size_request(w, 150, -1);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 5, 1, 1);
  g_signal_connect(w, "value-changed", G_CALLBACK(vfo_dial_size_cb), NULL);
  l = gtk_label_new("TB Custom");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 6, 1, 1);
  w = gtk_check_button_new();
  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), tb_use_custom);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 6, 1, 1);
  g_signal_connect(w, "toggled", G_CALLBACK(tb_use_custom_cb), NULL);
  l = gtk_label_new("TB Color");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 7, 1, 1);
  w = gtk_color_button_new();
  gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(w), &tb_custom_color);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 7, 1, 1);
  g_signal_connect(w, "color-set", G_CALLBACK(tb_color_cb), NULL);
  l = gtk_label_new("TB Brightness");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 8, 1, 1);
  w = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0.0, 1.0, 0.05);
  gtk_range_set_value(GTK_RANGE(w), tb_brightness);
  gtk_widget_set_size_request(w, 150, -1);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 8, 1, 1);
  g_signal_connect(w, "value-changed", G_CALLBACK(tb_brightness_cb), NULL);
  l = gtk_label_new("Шрифт кнопок");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 9, 1, 1);
  w = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 8.0, 25.0, 1.0);
  gtk_range_set_value(GTK_RANGE(w), tb_font_size);
  gtk_widget_set_size_request(w, 150, -1);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 9, 1, 1);
  g_signal_connect(w, "value-changed", G_CALLBACK(tb_font_cb), NULL);
  l = gtk_label_new("Status Custom");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 10, 1, 1);
  w = gtk_check_button_new();
  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), vfo_status_use_custom);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 10, 1, 1);
  g_signal_connect(w, "toggled", G_CALLBACK(vfo_status_use_custom_cb), NULL);
  l = gtk_label_new("Status Color");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 11, 1, 1);
  w = gtk_color_button_new();
  gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(w), &vfo_status_color);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 11, 1, 1);
  g_signal_connect(w, "color-set", G_CALLBACK(vfo_status_color_cb), NULL);
  l = gtk_label_new("Status Brightness");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 12, 1, 1);
  w = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0.0, 5.0, 0.05); /* BRIGHT5 PATCH */
  gtk_range_set_value(GTK_RANGE(w), vfo_status_brightness);
  gtk_widget_set_size_request(w, 150, -1);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 12, 1, 1);
  g_signal_connect(w, "value-changed", G_CALLBACK(vfo_status_brightness_cb), NULL);
  l = gtk_label_new("Status Size");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 13, 1, 1);
  w = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0.5, 2.0, 0.05);
  gtk_range_set_value(GTK_RANGE(w), vfo_status_size_scale);
  gtk_widget_set_size_request(w, 150, -1);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 13, 1, 1);
  g_signal_connect(w, "value-changed", G_CALLBACK(vfo_status_size_cb), NULL);
  gtk_window_set_default_size(GTK_WINDOW(dlg), 420, 620);
  tb_css_apply();
  gtk_container_add(GTK_CONTAINER(gtk_dialog_get_content_area(GTK_DIALOG(dlg))), cg);
  gtk_widget_show_all(dlg);
}

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

static void pan_text_settings_dialog_cb(GtkWidget *widget, gpointer data) {
  GtkWidget *dlg = gtk_dialog_new();
  GtkWidget *cg = gtk_grid_new();
  GtkWidget *l, *w;
  gtk_window_set_title(GTK_WINDOW(dlg), "Panadapter Text");
  gtk_window_set_default_size(GTK_WINDOW(dlg), 380, 300);
  gtk_grid_set_row_spacing(GTK_GRID(cg), 5);
  gtk_grid_set_column_spacing(GTK_GRID(cg), 5);
  l = gtk_label_new("dBm Font Size");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 0, 1, 1);
  w = gtk_spin_button_new_with_range(6.0, 40.0, 1.0);
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(w), pan_dbm_font_size);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 0, 1, 1);
  g_signal_connect(w, "value_changed", G_CALLBACK(pan_text_dbm_font_cb), NULL);
  l = gtk_label_new("Freq Font Size");
  gtk_grid_attach(GTK_GRID(cg), l, 0, 1, 1, 1);
  w = gtk_spin_button_new_with_range(6.0, 40.0, 1.0);
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(w), pan_freq_font_size);
  gtk_grid_attach(GTK_GRID(cg), w, 1, 1, 1, 1);
  g_signal_connect(w, "value_changed", G_CALLBACK(pan_text_freq_font_cb), NULL);
  w = gtk_button_new_with_label("dBm Color");
  gtk_grid_attach(GTK_GRID(cg), w, 0, 2, 1, 1);
  g_signal_connect(w, "clicked", G_CALLBACK(pan_text_color_cb), GINT_TO_POINTER(0));
  w = gtk_button_new_with_label("Freq Color");
  gtk_grid_attach(GTK_GRID(cg), w, 1, 2, 1, 1);
  g_signal_connect(w, "clicked", G_CALLBACK(pan_text_color_cb), GINT_TO_POINTER(1));
  // HEADERCFG: header scale
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
  gtk_container_add(GTK_CONTAINER(gtk_dialog_get_content_area(GTK_DIALOG(dlg))), cg);
  gtk_widget_show_all(dlg);
}
static void pan_text_color_cb(GtkWidget *widget, gpointer data) {
  int which = GPOINTER_TO_INT(data);
  GdkRGBA color;
  GtkWidget *dialog;
  color = which ? pan_freq_color : pan_dbm_color;
  dialog = gtk_color_chooser_dialog_new(which ? "Freq Color" : "dBm Color", NULL);
  gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(dialog), &color);
  if (gtk_dialog_run(GTK_DIALOG(dialog)) == GTK_RESPONSE_OK) {
    gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(dialog), &color);
    if (which) { pan_freq_color = color; } else { pan_dbm_color = color; }
    pan_text_save_conf();
  }
  gtk_widget_destroy(dialog);
}
extern double pan_dbm_font_size;
extern double pan_freq_font_size;

static void pan_grid_width_value_changed_cb(GtkWidget *widget, gpointer data) {
  pan_grid_width = gtk_range_get_value(GTK_RANGE(widget));
}

static void pan_grid_thin_cb(GtkWidget *widget, gpointer data) {
  if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget))) { pan_grid_width = 1.0; }
}

static void pan_grid_medium_cb(GtkWidget *widget, gpointer data) {
  if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget))) { pan_grid_width = 2.0; }
}

static void pan_grid_thick_cb(GtkWidget *widget, gpointer data) {
  if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget))) { pan_grid_width = 3.5; }
}

static void pan_grid_color_set_cb(GtkWidget *widget, gpointer data) {
  gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(widget), &pan_grid_custom_color);
  pan_grid_use_custom_color = 1;
}

static void pan_grid_use_custom_color_cb(GtkWidget *widget, gpointer data) {
  pan_grid_use_custom_color = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget)) ? 1 : 0;
}

static void pan_vgrid_use_custom_cb(GtkWidget *widget, gpointer data) { /* VGRID PATCH */
  pan_vgrid_use_custom_color = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}
static void pan_vgrid_color_set_cb(GtkWidget *widget, gpointer data) {
  gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(widget), &pan_vgrid_custom_color);
}
static void pan_grid_brightness_value_changed_cb(GtkWidget *widget, gpointer data) {
  pan_grid_brightness = gtk_range_get_value(GTK_RANGE(widget));
}

static void pan_dbm_font_value_changed_cb(GtkWidget *widget, gpointer data) {
  pan_dbm_font_size = gtk_range_get_value(GTK_RANGE(widget));
}

static void pan_freq_font_value_changed_cb(GtkWidget *widget, gpointer data) {
  pan_freq_font_size = gtk_range_get_value(GTK_RANGE(widget));
}

static void panadapter_peaks_on_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->panadapter_peaks_on = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void time_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->display_average_time = gtk_spin_button_get_value(GTK_SPIN_BUTTON(widget));

  if (radio_is_remote) {
    send_display(cl_sock_tcp, myrx->id);
  } else {
    rx_set_average(myrx);
  }
}

static void filled_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->display_filled = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void tx_filled_cb(GtkWidget *widget, gpointer data) {
  transmitter->display_filled = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void panadapter_hide_noise_filled_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->panadapter_hide_noise_filled = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void panadapter_peaks_in_passband_filled_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->panadapter_peaks_in_passband_filled = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void gradient_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->display_gradient = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void frames_per_second_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->fps = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
  int old = myrx->display_panadapter;
  myrx->display_panadapter = (myrx->fps > 1);

  if (old != myrx->display_panadapter) { radio_reconfigure(); }

  if (radio_is_remote) {
    send_rxfps(cl_sock_tcp, myrx->id, myrx->fps);
  } else {
    rx_set_framerate(myrx);
  }
}

static void tx_frames_per_second_value_changed_cb(GtkWidget *widget, gpointer data) {
  transmitter->fps = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));

  if (radio_is_remote) {
    send_txfps(cl_sock_tcp, transmitter->fps);
  } else {
    tx_set_framerate(transmitter);
  }
}

static void panadapter_high_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  int value = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
  radio_set_panhigh(myrx->id, value);
}

static void tx_panadapter_high_value_changed_cb(GtkWidget *widget, gpointer data) {
  int value = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
  transmitter->panadapter_high = value;
}

static void panadapter_low_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  int value = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
  radio_set_panlow(myrx->id, value);
}

static void tx_panadapter_low_value_changed_cb(GtkWidget *widget, gpointer data) {
  int value = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
  transmitter->panadapter_low = value;
}

static void panadapter_step_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  int value = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
  radio_set_panstep(myrx->id, value);
}

static void tx_panadapter_step_value_changed_cb(GtkWidget *widget, gpointer data) {
  int value = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
  transmitter->panadapter_step = value;
}

static void panadapter_num_peaks_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->panadapter_num_peaks = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
}

static void panadapter_ignore_range_divider_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->panadapter_ignore_range_divider = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
}

static void panadapter_ignore_noise_percentile_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->panadapter_ignore_noise_percentile = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
}

static void waterfall_high_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  radio_set_wfhigh(myrx->id, gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget)));
}

static void waterfall_low_value_changed_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  radio_set_wflow(myrx->id, gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget)));
}

static void waterfall_automatic_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  int val = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
  myrx->waterfall_automatic = val;
}

static void display_waterfall_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->display_waterfall = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
  radio_reconfigure();
}

static void waterfall_percent_cb(GtkWidget *widget, gpointer data) {
  RECEIVER *myrx = (RECEIVER *)data;
  myrx->waterfall_percent = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
  radio_reconfigure();
}

static void tx_panadapter_peaks_in_passband_filled_cb(GtkWidget *widget, gpointer data) {
  transmitter->panadapter_peaks_in_passband_filled = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void tx_panadapter_hide_noise_filled_cb(GtkWidget *widget, gpointer data) {
  transmitter->panadapter_hide_noise_filled = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void tx_panadapter_peaks_on_cb(GtkWidget *widget, gpointer data) {
  transmitter->panadapter_peaks_on = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void tx_panadapter_num_peaks_value_changed_cb(GtkWidget *widget, gpointer data) {
  transmitter->panadapter_num_peaks = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
}

static void tx_panadapter_ignore_range_divider_value_changed_cb(GtkWidget *widget, gpointer data) {
  transmitter->panadapter_ignore_range_divider = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
}

static void tx_panadapter_ignore_noise_percentile_value_changed_cb(GtkWidget *widget, gpointer data) {
  transmitter->panadapter_ignore_noise_percentile = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(widget));
}

static void display_warnings_cb(GtkWidget *widget, gpointer data) {
  display_warnings = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void pan_updown_drag_cb(GtkWidget *widget, gpointer data) {
  pan_updown_drag = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

static void floating_toolbar_cb(GtkWidget *widget, gpointer data) {
  floating_toolbar = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
  radio_reconfigure_screen();  // VFO bar width depends on the floating toolbar
}

static void tx_display_pacurr_cb(GtkWidget *widget, gpointer data) {
  display_pacurr = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
}

void display_menu(GtkWidget *parent) {
  GtkWidget *label;
  GtkWidget *btn;
  GtkWidget *mbtn; // main button for radio buttons
  char title[64];
  dialog = gtk_dialog_new();
  gtk_window_set_transient_for(GTK_WINDOW(dialog), GTK_WINDOW(toolbar_menu_parent(parent)));
  GtkWidget *headerbar = gtk_header_bar_new();
  gtk_window_set_titlebar(GTK_WINDOW(dialog), headerbar);
  gtk_header_bar_set_show_close_button(GTK_HEADER_BAR(headerbar), TRUE);
  { /* ZSCROLL PATCH: окно не вылезает за пределы экрана */
    GdkRectangle mongeo = { 0, 0, 1024, 768 };
    GdkDisplay *gdisp = gdk_display_get_default();
    GdkMonitor *mon = gdisp ? gdk_display_get_primary_monitor(gdisp) : NULL;
    if (mon == NULL && gdisp && gdk_display_get_n_monitors(gdisp) > 0) {
      mon = gdk_display_get_monitor(gdisp, 0);
    }
    if (mon) { gdk_monitor_get_geometry(mon, &mongeo); }
    int zmaxh = mongeo.height - 120; /* запас на шапку окна и панели */
    if (zmaxh < 200) zmaxh = 200;
    int zmaxw = mongeo.width - 40;
    int zh = (460 < zmaxh) ? 460 : zmaxh;
    int zw = (1020 < zmaxw) ? 1020 : zmaxw;
    gtk_window_set_default_size(GTK_WINDOW(dialog), zw, zh);
  }
  snprintf(title, sizeof(title), "piHPSDR-Improved - Display");
  gtk_header_bar_set_title(GTK_HEADER_BAR(headerbar), title);
  g_signal_connect (dialog, "delete_event", G_CALLBACK (close_cb), NULL);
  g_signal_connect (dialog, "destroy", G_CALLBACK (close_cb), NULL);
  GtkWidget *content = gtk_dialog_get_content_area(GTK_DIALOG(dialog));
  /* ZSCROLL PATCH: прокрутка, как у веб-страницы */
  GtkWidget *zscroll = gtk_scrolled_window_new(NULL, NULL);
  gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(zscroll), GTK_POLICY_NEVER, GTK_POLICY_AUTOMATIC);
  gtk_widget_set_vexpand(zscroll, TRUE);
  gtk_container_add(GTK_CONTAINER(content), zscroll);
  GtkWidget *grid = gtk_grid_new();
  gtk_grid_set_column_spacing(GTK_GRID(grid), 10);
  gtk_grid_set_column_homogeneous(GTK_GRID(grid), TRUE);
  gtk_container_add(GTK_CONTAINER(zscroll), grid);
  int row = 0;
  int col = 0;
  btn = gtk_button_new_with_label("Закрыть");
  gtk_widget_set_name(btn, "close_button");
  g_signal_connect(btn, "button-press-event", G_CALLBACK(close_cb), NULL);
  gtk_grid_attach(GTK_GRID(grid), btn, col, row, 1, 1);
  //
  // Must init the containers here since setting the buttons emits
  // a signal leading to show/hide commands
  //
  rx1_container = gtk_fixed_new();
  rx2_container = gtk_fixed_new();
  tx_container = gtk_fixed_new();
  GtkWidget *rx1_grid = gtk_grid_new();
  GtkWidget *rx2_grid = gtk_grid_new();
  GtkWidget *tx_grid = gtk_grid_new();
  mbtn = gtk_radio_button_new_with_label_from_widget(NULL, "RX1 Settings");
  col = 3;

  if (can_transmit) {
    btn = gtk_radio_button_new_with_label_from_widget(GTK_RADIO_BUTTON(mbtn), "TX settings");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), 0);
    gtk_grid_attach(GTK_GRID(grid), btn, col, row, 1, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(sel_cb), GINT_TO_POINTER(TX_CONTAINER));
    gtk_grid_attach(GTK_GRID(grid), tx_container, 0, 1, 4, 1);
    gtk_grid_set_column_spacing(GTK_GRID(tx_grid), 10);
    gtk_grid_set_row_homogeneous(GTK_GRID(tx_grid), TRUE);
    gtk_container_add(GTK_CONTAINER(tx_container), tx_grid);
    col--;
  }

  if (receivers > 1) {
    btn = gtk_radio_button_new_with_label_from_widget(GTK_RADIO_BUTTON(mbtn), "RX2 settings");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), 0);
    gtk_grid_attach(GTK_GRID(grid), btn, col, row, 1, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(sel_cb), GINT_TO_POINTER(RX2_CONTAINER));
    gtk_grid_attach(GTK_GRID(grid), rx2_container, 0, 1, 4, 1);
    gtk_grid_set_column_spacing(GTK_GRID(rx2_grid), 10);
    gtk_grid_set_row_homogeneous(GTK_GRID(rx2_grid), TRUE);
    gtk_container_add(GTK_CONTAINER(rx2_container), rx2_grid);
    col--;
  }

  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(mbtn), 1);
  gtk_grid_attach(GTK_GRID(grid), mbtn, col, row, 1, 1);
  g_signal_connect(mbtn, "toggled", G_CALLBACK(sel_cb), GINT_TO_POINTER(RX1_CONTAINER));
  gtk_grid_attach(GTK_GRID(grid), rx1_container, 0, 1, 4, 1);
  gtk_grid_set_column_spacing(GTK_GRID(rx1_grid), 10);
  gtk_grid_set_row_homogeneous(GTK_GRID(rx1_grid), TRUE);
  gtk_container_add(GTK_CONTAINER(rx1_container), rx1_grid);

  for (int id = 0; id < receivers; id++) {
    RECEIVER *myrx = receiver[id];
    GtkWidget *mygrid = (id == 0) ? rx1_grid : rx2_grid;
    row = 0;
    col = 0;
    label = gtk_label_new("Frames/sec");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 64.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->fps);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(frames_per_second_value_changed_cb), myrx);
    row++;
    label = gtk_label_new("Panadapter High");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(-220.0, 100.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->panadapter_high);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    pan_high_spin[id] = btn;
    pan_high_signal[id] = g_signal_connect(btn, "value_changed", G_CALLBACK(panadapter_high_value_changed_cb), myrx);
    row++;
    label = gtk_label_new("Panadapter Low");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(-220.0, 100.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->panadapter_low);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    pan_low_spin[id] = btn;
    pan_low_signal[id] = g_signal_connect(btn, "value_changed", G_CALLBACK(panadapter_low_value_changed_cb), myrx);
    row++;
    label = gtk_label_new("Panadapter Step");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 20.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->panadapter_step);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(panadapter_step_value_changed_cb), myrx);
    row++;
    btn = gtk_check_button_new_with_label("Pan Filled");
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), myrx->display_filled);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 1, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(filled_cb), myrx);
    btn = gtk_check_button_new_with_label("Gradient");
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), myrx->display_gradient);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(gradient_cb), myrx);
    row++;
    label = gtk_label_new("Waterfall High");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(-220.0, 100.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->waterfall_high);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    wf_high_spin[id] = btn;
    wf_high_signal[id] = g_signal_connect(btn, "value_changed", G_CALLBACK(waterfall_high_value_changed_cb), myrx);
    row++;
    label = gtk_label_new("Waterfall Low");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(-220.0, 100.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->waterfall_low);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    wf_low_spin[id] = btn;
    wf_low_signal[id] = g_signal_connect(btn, "value_changed", G_CALLBACK(waterfall_low_value_changed_cb), myrx);
    row++;
    label = gtk_label_new("WF Height (%)");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *waterfall_percent = gtk_spin_button_new_with_range(20.0, 80.0, 5.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(waterfall_percent), (double) myrx->waterfall_percent);
    gtk_grid_attach(GTK_GRID(mygrid), waterfall_percent, col + 1, row, 1, 1);
    g_signal_connect(waterfall_percent, "value-changed", G_CALLBACK(waterfall_percent_cb), myrx);
    row++;
    btn = gtk_check_button_new_with_label("Display WF");
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), myrx->display_waterfall);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 1, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(display_waterfall_cb), myrx);
    btn = gtk_check_button_new_with_label("WF automatic");
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), myrx->waterfall_automatic);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    row++;
    g_signal_connect(btn, "toggled", G_CALLBACK(waterfall_automatic_cb), myrx);

    if (!radio_is_remote && id == 0) {
      btn = gtk_check_button_new_with_label("Display Warnings");
      gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), display_warnings);
      gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 2, 1);
      g_signal_connect(btn, "toggled", G_CALLBACK(display_warnings_cb), NULL);
      row++;
      btn = gtk_check_button_new_with_label("Panadapter Up/Down Drag");
      gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), pan_updown_drag);
      gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 2, 1);
      g_signal_connect(btn, "toggled", G_CALLBACK(pan_updown_drag_cb), NULL);
      row++;
      btn = gtk_check_button_new_with_label("Floating Toolbar");
      gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), floating_toolbar);
      gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 2, 1);
      g_signal_connect(btn, "toggled", G_CALLBACK(floating_toolbar_cb), NULL);
    }

    col = 2;
    row = 0;
    label = gtk_label_new("Detector");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *detector_combo = gtk_combo_box_text_new();
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(detector_combo), NULL, "Peak");
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(detector_combo), NULL, "Rosenfell");
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(detector_combo), NULL, "Average");
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(detector_combo), NULL, "Sample");

    switch (myrx->display_detector_mode) {
    case DET_PEAK:
      gtk_combo_box_set_active(GTK_COMBO_BOX(detector_combo), 0);
      break;

    case DET_ROSENFELL:
      gtk_combo_box_set_active(GTK_COMBO_BOX(detector_combo), 1);
      break;

    case DET_AVERAGE:
      gtk_combo_box_set_active(GTK_COMBO_BOX(detector_combo), 2);
      break;

    case DET_SAMPLEHOLD:
      gtk_combo_box_set_active(GTK_COMBO_BOX(detector_combo), 3);
      break;
    }

    my_combo_attach(GTK_GRID(mygrid), detector_combo, col + 1, row, 1, 1);
    g_signal_connect(detector_combo, "changed", G_CALLBACK(detector_cb), myrx);
    row++;
    label = gtk_label_new("Averaging: ");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *average_combo = gtk_combo_box_text_new();
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(average_combo), NULL, "None");
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(average_combo), NULL, "Recursive");
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(average_combo), NULL, "Time Window");
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(average_combo), NULL, "Log Recursive");

    switch (myrx->display_average_mode) {
    case AVG_NONE:
      gtk_combo_box_set_active(GTK_COMBO_BOX(average_combo), 0);
      break;

    case AVG_RECURSIVE:
      gtk_combo_box_set_active(GTK_COMBO_BOX(average_combo), 1);
      break;

    case AVG_TIMEWINDOW:
      gtk_combo_box_set_active(GTK_COMBO_BOX(average_combo), 2);
      break;

    case AVG_LOGRECURSIVE:
      gtk_combo_box_set_active(GTK_COMBO_BOX(average_combo), 3);
      break;
    }

    my_combo_attach(GTK_GRID(mygrid), average_combo, col + 1, row, 1, 1);
    g_signal_connect(average_combo, "changed", G_CALLBACK(average_cb), myrx);
    row++;
    label = gtk_label_new("Av. Time (ms)");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *time_r = gtk_spin_button_new_with_range(1.0, 9999.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(time_r), (double)myrx->display_average_time);
    gtk_grid_attach(GTK_GRID(mygrid), time_r, col + 1, row, 1, 1);
    g_signal_connect(time_r, "value_changed", G_CALLBACK(time_value_changed_cb), myrx);
    row++;
    row++;
    btn = gtk_check_button_new_with_label("Label Strongest Peaks");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), myrx->panadapter_peaks_on);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 2, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(panadapter_peaks_on_cb), myrx);
    row++;
    btn = gtk_check_button_new_with_label("Label in Passband Only");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), myrx->panadapter_peaks_in_passband_filled);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 2, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(panadapter_peaks_in_passband_filled_cb), myrx);
    row++;
    btn = gtk_check_button_new_with_label("No Labels Below Noise Floor");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), myrx->panadapter_hide_noise_filled);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 2, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(panadapter_hide_noise_filled_cb), myrx);
    row++;
    label = gtk_label_new("Number of Peaks");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 10.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->panadapter_num_peaks);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(panadapter_num_peaks_value_changed_cb), myrx);
    row++;
    label = gtk_label_new("Ignore Adjacent");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 150.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->panadapter_ignore_range_divider);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(panadapter_ignore_range_divider_value_changed_cb), myrx);
    row++;
    label = gtk_label_new("Floor Percentile");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 100.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)myrx->panadapter_ignore_noise_percentile);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(panadapter_ignore_noise_percentile_value_changed_cb), myrx);
    row++;
    label = gtk_label_new("Line Width");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *lw = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0.1, 3.0, 0.1);
    gtk_range_set_value(GTK_RANGE(lw), panadapter_line_width);
    gtk_widget_set_size_request(lw, 150, -1);
    gtk_grid_attach(GTK_GRID(mygrid), lw, col + 1, row, 1, 1);
    g_signal_connect(lw, "value-changed", G_CALLBACK(panadapter_line_width_value_changed_cb), NULL);
    row++;
    label = gtk_label_new("Grid Width");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *gw = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0.0, 3.0, 0.1);
    gtk_range_set_value(GTK_RANGE(gw), pan_grid_width);
    gtk_widget_set_size_request(gw, 150, -1);
    gtk_grid_attach(GTK_GRID(mygrid), gw, col + 1, row, 1, 1);
    g_signal_connect(gw, "value-changed", G_CALLBACK(pan_grid_width_value_changed_cb), NULL);
    row++;
    btn = gtk_check_button_new_with_label("Custom Grid Color");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), pan_grid_use_custom_color);
    gtk_grid_attach(GTK_GRID(mygrid), btn, col, row, 2, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(pan_grid_use_custom_color_cb), NULL);
    row++;
    label = gtk_label_new("Grid Color");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *gcolor = gtk_color_button_new();
    gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(gcolor), &pan_grid_custom_color);
    gtk_grid_attach(GTK_GRID(mygrid), gcolor, col + 1, row, 1, 1);
    g_signal_connect(gcolor, "color-set", G_CALLBACK(pan_grid_color_set_cb), NULL);
    row++;
    /* === VGRID PATCH: отдельный цвет вертикальной сетки === */
    label = gtk_label_new("V Grid Custom");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *vgt = gtk_check_button_new();
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(vgt), pan_vgrid_use_custom_color);
    gtk_grid_attach(GTK_GRID(mygrid), vgt, col + 1, row, 1, 1);
    g_signal_connect(vgt, "toggled", G_CALLBACK(pan_vgrid_use_custom_cb), NULL);
    row++;
    label = gtk_label_new("V Grid Color");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(mygrid), label, col, row, 1, 1);
    GtkWidget *vgcol = gtk_color_button_new();
    gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(vgcol), &pan_vgrid_custom_color);
    gtk_grid_attach(GTK_GRID(mygrid), vgcol, col + 1, row, 1, 1);
    g_signal_connect(vgcol, "color-set", G_CALLBACK(pan_vgrid_color_set_cb), NULL);
    row++;
    /* === PAN TEXT UI PATCH v2: одна кнопка настроек === PAN CLEAN PATCH === */
    {
      GtkWidget *pgrid_ = gcolor, *pw;
      while (pgrid_ != NULL && !GTK_IS_GRID(pgrid_)) { pgrid_ = gtk_widget_get_parent(pgrid_); }
      if (pgrid_ != NULL) {
        pw = gtk_button_new_with_label("Pan Text Settings");
        gtk_widget_set_halign(pw, GTK_ALIGN_START); /* PAN BTN SMALL PATCH */
        gtk_widget_set_size_request(pw, 110, -1);
        gtk_grid_attach(GTK_GRID(pgrid_), pw, 0, row, 1, 1);
        g_signal_connect(pw, "clicked", G_CALLBACK(pan_text_settings_dialog_cb), NULL);
        pw = gtk_button_new_with_label("Color Settings"); /* COLORSET PATCH */
        gtk_widget_set_halign(pw, GTK_ALIGN_START);
        gtk_widget_set_size_request(pw, 110, -1);
        gtk_grid_attach(GTK_GRID(pgrid_), pw, 0, row + 1, 1, 1);
        g_signal_connect(pw, "clicked", G_CALLBACK(color_settings_dialog_cb), NULL);
        row++;
      }
    }
    row++;
    row++;
    row++;
    row++;
    row++;
  }

  //
  // Since the RECEIVER and TRANSMITTER data structures are different, we have to repeat code
  // since the presets and callbacks are different
  //
    if (can_transmit) {
    row = 0;
    col = 0;
    label = gtk_label_new("Frames/sec");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(tx_grid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 64.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)transmitter->fps);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(tx_frames_per_second_value_changed_cb), NULL);
    row++;
    label = gtk_label_new("Panadapter High");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(tx_grid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(-50.0, 10.0, 5.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)transmitter->panadapter_high);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(tx_panadapter_high_value_changed_cb), NULL);
    row++;
    label = gtk_label_new("Panadapter Low");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(tx_grid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(-120.0, -40.0, 5.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)transmitter->panadapter_low);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(tx_panadapter_low_value_changed_cb), NULL);
    row++;
    label = gtk_label_new("Panadapter Step");
    gtk_widget_set_name (label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(tx_grid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(5.0, 20.0, 5.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)transmitter->panadapter_step);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(tx_panadapter_step_value_changed_cb), NULL);
    row++;
    btn = gtk_check_button_new_with_label("Pan Filled");
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), transmitter->display_filled);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col, row, 1, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(tx_filled_cb), NULL);

    if (!radio_is_remote) {
      row += 5;
      btn = gtk_check_button_new_with_label("Display PA current");
      gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (btn), display_pacurr);
      gtk_grid_attach(GTK_GRID(tx_grid), btn, col, row, 2, 1);
      g_signal_connect(btn, "toggled", G_CALLBACK(tx_display_pacurr_cb), NULL);
    }

    row = 4;
    col = 2;
    btn = gtk_check_button_new_with_label("Label Strongest Peaks");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), transmitter->panadapter_peaks_on);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col, row, 2, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(tx_panadapter_peaks_on_cb), NULL);
    row++;
    btn = gtk_check_button_new_with_label("Label in Passband Only");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), transmitter->panadapter_peaks_in_passband_filled);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col, row, 2, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(tx_panadapter_peaks_in_passband_filled_cb), NULL);
    row++;
    btn = gtk_check_button_new_with_label("No Labels Below Noise Floor");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(btn), transmitter->panadapter_hide_noise_filled);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col, row, 2, 1);
    g_signal_connect(btn, "toggled", G_CALLBACK(tx_panadapter_hide_noise_filled_cb), NULL);
    row++;
    label = gtk_label_new("Number of Peaks");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(tx_grid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 10.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)transmitter->panadapter_num_peaks);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(tx_panadapter_num_peaks_value_changed_cb), NULL);
    row++;
    label = gtk_label_new("Ignore Adjacent");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(tx_grid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 150.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)transmitter->panadapter_ignore_range_divider);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(tx_panadapter_ignore_range_divider_value_changed_cb), NULL);
    row++;
    label = gtk_label_new("Floor Percentile");
    gtk_widget_set_name(label, "boldlabel");
    gtk_widget_set_halign(label, GTK_ALIGN_END);
    gtk_grid_attach(GTK_GRID(tx_grid), label, col, row, 1, 1);
    btn = gtk_spin_button_new_with_range(1.0, 100.0, 1.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(btn), (double)transmitter->panadapter_ignore_noise_percentile);
    gtk_grid_attach(GTK_GRID(tx_grid), btn, col + 1, row, 1, 1);
    g_signal_connect(btn, "value_changed", G_CALLBACK(tx_panadapter_ignore_noise_percentile_value_changed_cb), NULL);
  }
  sub_menu = dialog;
  gtk_widget_show_all(dialog);
  gtk_widget_hide(rx2_container);
  gtk_widget_hide(tx_container);
}

