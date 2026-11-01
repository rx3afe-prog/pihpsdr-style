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
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "toolbar.h"
#include "band.h"
#include "bandstack.h"
#include "ext.h"
#include "filter.h"
#include "message.h"
#include "mode.h"
#include "new_menu.h"
#include "radio.h"
#include "receiver.h"
#include "vfo.h"

static GtkWidget *dialog = NULL;

struct _CHOICE {
  int info;
  GtkWidget      *button;
  gulong          signal;
  struct _CHOICE *next;
};

typedef struct _CHOICE CHOICE;

static RECEIVER *myrx;
static int mymode;

static struct _CHOICE *first = NULL;
static struct _CHOICE *current = NULL;

static GtkWidget *var1_spin_low;
static GtkWidget *var1_spin_high;
static GtkWidget *var2_spin_low;
static GtkWidget *var2_spin_high;
static GtkWidget *mn_center[3];
static GtkWidget *mn_width[3];

static void cleanup(void) {
  if (dialog != NULL) {
    GtkWidget *tmp = dialog;
    dialog = NULL;

    while (first != NULL) {
      CHOICE *choice = first;
      first = first->next;
      g_free(choice);
    }

    current = NULL;
    gtk_widget_destroy(tmp);
    sub_menu = NULL;
    active_menu = NO_MENU;
    radio_save_state();
  }
}

static void mn_enable_cb(GtkWidget *widget, gpointer data) {
  int n = GPOINTER_TO_INT(data);
  int v = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
  //
  // When a notch is (freshly) switched on and it has not yet been positioned
  // (its centre is still at the default 0 Hz, i.e. at the carrier and thus
  // normally outside the current RX pass-band), move it to the centre of the
  // current pass-band. Setting the spin button value triggers mn_center_cb
  // which stores the value and updates the running receiver.
  //
  if (v && myrx->multi_notch_center[n] == 0.0) {
    double c = 0.5 * (myrx->filter_low + myrx->filter_high) + vfo[myrx->id].offset;
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(mn_center[n]), c);
  }
  myrx->multi_notch_enable[n] = v;
  rx_set_notch(myrx);
}

static void cw_apf_cb(GtkWidget *widget, gpointer data) {
  int id = myrx->id;
  int val = gtk_combo_box_get_active(GTK_COMBO_BOX(widget));
  vfo_id_cwpeak_changed(id, val);
}

static gboolean mn_default_cb (GtkWidget *widget, GdkEventButton *event, gpointer data) {
  int n = GPOINTER_TO_INT(data);
  double c;
  double w;
  //
  // This is to restore the notch filter to some default value:
  // place notch in the center of the current pass-band, and
  // set its width to the minimum
  //
  w = myrx->notch_min_width;
  c = 0.5 * (myrx->filter_low + myrx->filter_high) + vfo[myrx->id].offset;
  //
  // setting the spin buttons activates the call backs
  //
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(mn_center[n]), c);
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(mn_width[n]), w);
  return FALSE;
}

//
// Var1/Var2 work like a PBT: the width spin changes both edges symmetrically,
// the shift spin moves the whole pass-band. Shift 0 is the centre of the
// default filter of the mode. For lower-sideband modes the shift is shown with
// reversed sign such that positive always means "towards higher audio pitch".
//
#define VAR_MAX_WIDTH 16000

static int var_ref_centre(int mode) {
  return (var_default_low[mode] + var_default_high[mode]) / 2;
}

static int var_sign(int mode) {
  return (mode == modeLSB || mode == modeDIGL || mode == modeCWL) ? -1 : 1;
}

static GtkWidget *var_width_spin(int f) {
  return f == filterVar1 ? var1_spin_low : var2_spin_low;
}

static GtkWidget *var_shift_spin(int f) {
  return f == filterVar1 ? var1_spin_high : var2_spin_high;
}

static int var_width_of(int mode, const FILTER *filter) {
  (void) mode;
  return filter->high - filter->low;
}

static int var_shift_of(int mode, const FILTER *filter) {
  return var_sign(mode) * ((filter->low + filter->high) / 2 - var_ref_centre(mode));
}

static void var_apply(int f) {
  FILTER *filter = &filters[mymode][f];
  int width = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(var_width_spin(f)));
  int shift = gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(var_shift_spin(f)));
  int centre = var_ref_centre(mymode) + var_sign(mymode) * shift;
  int low = centre - width / 2;
  int high = centre + width / 2;

  //
  // SSB-type pass-bands must not cross the carrier
  //
  if (mymode == modeUSB || mymode == modeDIGU) {
    if (low < 0) {
      low = 0;
    }
  } else if (mymode == modeLSB || mymode == modeDIGL) {
    if (high > 0) {
      high = 0;
    }
  }

  //
  // WDSP does not accept an empty pass-band
  //
  if (high <= low) {
    if (mymode == modeLSB || mymode == modeDIGL) {
      low = high - 1;
    } else {
      high = low + 1;
    }
  }

  filter->low = low;
  filter->high = high;

  if (radio_is_remote) {
    send_filter_var(cl_sock_tcp, mymode, f);
  }

  //
  // Perform a "filter changed" operation on all receivers which
  // use THIS filter.
  //
  for (int v = 0; v < receivers; v++) {
    if ((vfo[v].mode == mymode) && (vfo[v].filter == f)) {
      vfo_id_filter_changed(v, f);
    }
  }

  // also redraw if no running receiver uses this filter (the VFO bar shows the filter edges of both VFOs)
  g_idle_add(ext_vfo_update, NULL);
}

static gboolean var_default_cb (GtkWidget *widget, GdkEventButton *event, gpointer data) {
  int f = GPOINTER_TO_INT(data);

  if (f != filterVar1 && f != filterVar2) {
    t_print("%s: illegal data = %p (%d)\n", __func__, data, f);
    return FALSE;
  }

  //
  // setting the spin buttons activates the call backs
  //
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(var_width_spin(f)),
                            (double)(var_default_high[mymode] - var_default_low[mymode]));
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(var_shift_spin(f)), 0.0);
  return FALSE;
}

static gboolean close_cb(void) {
  cleanup();
  return TRUE;
}

static gboolean filter_select_cb (GtkWidget *widget, gpointer data) {
  CHOICE *choice = (CHOICE *) data;

  if (current) {
    g_signal_handler_block(G_OBJECT(current->button), current->signal);
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(current->button), current == choice);
    g_signal_handler_unblock(G_OBJECT(current->button), current->signal);
  }

  //
  // if current == choice, the filter will not be changed but the RX filter edges
  // will be restored to their default values
  //
  current = choice;
  vfo_filter_changed(current->info);
  return FALSE;
}

static gboolean deviation_select_cb (GtkWidget *widget, gpointer data) {
  CHOICE *choice = (CHOICE *) data;

  if (current) {
    g_signal_handler_block(G_OBJECT(current->button), current->signal);
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(current->button), current == choice);
    g_signal_handler_unblock(G_OBJECT(current->button), current->signal);
  }

  if (current != choice) {
    int id = myrx->id;
    current = choice;

    if (radio_is_remote) {
      send_deviation(cl_sock_tcp, id, choice->info);
    } else {
      vfo[id].deviation = choice->info;
      rx_set_filter(myrx);

      if (can_transmit) {
        tx_set_filter(transmitter);
      }

      g_idle_add(ext_vfo_update, NULL);
    }
  }

  return FALSE;
}

static void mn_center_cb (GtkWidget *widget, gpointer data) {
  int n = GPOINTER_TO_INT(data);
  double val = gtk_spin_button_get_value(GTK_SPIN_BUTTON(widget));
  myrx->multi_notch_center[n] = val;
  rx_set_notch(myrx);
}

static void mn_width_cb (GtkWidget *widget, gpointer data) {
  int n = GPOINTER_TO_INT(data);
  double val = gtk_spin_button_get_value(GTK_SPIN_BUTTON(widget));
  myrx->multi_notch_width[n] = val;
  rx_set_notch(myrx);
}

//
// var_spin_low controls the width, var_spin_high the shift
//
static void var_spin_low_cb (GtkWidget *widget, gpointer data) {
  int f = GPOINTER_TO_INT(data);
  double width = gtk_spin_button_get_value(GTK_SPIN_BUTTON(widget));
  //
  // the shift is limited to +/- the width. Changing the range may change the
  // shift value, which in turn calls var_apply() via the shift call back.
  //
  gtk_spin_button_set_range(GTK_SPIN_BUTTON(var_shift_spin(f)), -width, width);
  var_apply(f);
}

static void var_spin_high_cb (GtkWidget *widget, gpointer data) {
  var_apply(GPOINTER_TO_INT(data));
}

void filter_menu(GtkWidget *parent, int id) {
  GtkWidget *w;
  dialog = gtk_dialog_new();
  gtk_window_set_transient_for(GTK_WINDOW(dialog), GTK_WINDOW(toolbar_menu_parent(parent)));
  char title[64];

  //
  // This guards against changing the active receiver while the menu is open
  //
  if (id >= receivers) {
    //
    // If this is VFO-B and only one RX running, we cannot update filters
    //
    return;
  }

  myrx = receiver[id];
  mymode = vfo[myrx->id].mode;
  int f = vfo[myrx->id].filter;
  snprintf(title, sizeof(title), "piHPSDR-Improved - Filter (RX%d VFO-%s)", myrx->id + 1, myrx->id == 0 ? "A" : "B");
  GtkWidget *headerbar = gtk_header_bar_new();
  gtk_window_set_titlebar(GTK_WINDOW(dialog), headerbar);
  gtk_header_bar_set_show_close_button(GTK_HEADER_BAR(headerbar), TRUE);
  gtk_header_bar_set_title(GTK_HEADER_BAR(headerbar), title);
  g_signal_connect (dialog, "delete_event", G_CALLBACK (close_cb), NULL);
  g_signal_connect (dialog, "destroy", G_CALLBACK(close_cb), NULL);
  GtkWidget *content = gtk_dialog_get_content_area(GTK_DIALOG(dialog));
  GtkWidget *grid = gtk_grid_new();
  gtk_grid_set_column_homogeneous(GTK_GRID(grid), TRUE);
  gtk_grid_set_row_homogeneous(GTK_GRID(grid), FALSE);
  gtk_grid_set_column_spacing (GTK_GRID(grid), 5);
  gtk_grid_set_row_spacing (GTK_GRID(grid), 5);
  w = gtk_button_new_with_label("Close");
  gtk_widget_set_name(w, "close_button");
  g_signal_connect (w, "button-press-event", G_CALLBACK(close_cb), NULL);
  gtk_grid_attach(GTK_GRID(grid), w, 0, 0, 4, 1);
  FILTER* band_filters = filters[mymode];
  int row = 1;

  if (mymode == modeFMN) {
    CHOICE *choice;
    w = gtk_toggle_button_new_with_label("11k");
    gtk_widget_set_name(w, "small_toggle_button");
    choice = g_new(CHOICE, 1);
    choice->next = first;
    first = choice;
    choice->info = 2500;
    choice->button = w;

    if (myrx->deviation == 2500) {
      current = choice;
      gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), TRUE);
    }

    choice->signal = g_signal_connect(w, "toggled", G_CALLBACK(deviation_select_cb), choice);
    gtk_grid_attach(GTK_GRID(grid), w, 0, row, 1, 1);
    w = gtk_label_new(" (Deviation=2.5k, use for 12.5 kHz raster)");
    gtk_widget_set_name(w, "boldlabel");
    gtk_widget_set_halign(w, GTK_ALIGN_START);
    gtk_grid_attach(GTK_GRID(grid), w, 1, row, 6, 1);
    w = gtk_toggle_button_new_with_label("16k");
    gtk_widget_set_name(w, "small_toggle_button");
    choice = g_new(CHOICE, 1);
    choice->next = first;
    first = choice;
    choice->info = 5000;
    choice->button = w;

    if (myrx->deviation == 5000) {
      current = choice;
      gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), TRUE);
    }

    row++;
    choice->signal = g_signal_connect(w, "toggled", G_CALLBACK(deviation_select_cb), choice);
    gtk_grid_attach(GTK_GRID(grid), w, 0, row, 1, 1);
    w = gtk_label_new(" (Deviation=5.0k, use for 25.0 kHz raster)");
    gtk_widget_set_name(w, "boldlabel");
    gtk_widget_set_halign(w, GTK_ALIGN_START);
    gtk_grid_attach(GTK_GRID(grid), w, 1, row, 6, 1);
    row++;
  } else {
    int col = 0;
    CHOICE *choice;

    for (int i = 0; i < filterVar1; i++) {
      if (col > 9) {
        col = 0;
        row++;
      }

      w = gtk_toggle_button_new_with_label(band_filters[i].title);
      gtk_widget_set_name(w, "small_toggle_button");
      choice = g_new(CHOICE, 1);
      choice->next = first;
      first = choice;
      choice->info = i;
      choice->button = w;

      if (i == f) {
        current = choice;
        gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), TRUE);
      }

      choice->signal = g_signal_connect(w, "toggled", G_CALLBACK(filter_select_cb), choice);
      gtk_grid_attach(GTK_GRID(grid), w, col, row, 2, 1);
      col += 2;
    }

    row++;
    //
    // PBT1 and PBT2 separated by a small horizontal line
    //
    w = gtk_separator_new(GTK_ORIENTATION_HORIZONTAL);
    gtk_widget_set_size_request(w, -1, 3);
    gtk_grid_attach(GTK_GRID(grid), w, 0, row++, 10, 1);
    //
    // Place PBT1 and PBT2 buttons in row+1, row+2
    //
    const FILTER* filter1 = &band_filters[filterVar1];
    const FILTER* filter2 = &band_filters[filterVar2];
    w = gtk_toggle_button_new_with_label(band_filters[filterVar1].title);
    gtk_widget_set_name(w, "small_toggle_button");
    gtk_grid_attach(GTK_GRID(grid), w, 0, row + 1, 2, 1);
    choice = g_new(CHOICE, 1);
    choice->next = first;
    first = choice;
    choice->info = filterVar1;
    choice->button = w;

    if (f == filterVar1) {
      current = choice;
      gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), TRUE);
    }

    choice->signal = g_signal_connect(w, "toggled", G_CALLBACK(filter_select_cb), choice);
    w = gtk_toggle_button_new_with_label(band_filters[filterVar2].title);
    gtk_widget_set_name(w, "small_toggle_button");
    gtk_grid_attach(GTK_GRID(grid), w, 0, row + 2, 2, 1);
    choice = g_new(CHOICE, 1);
    choice->next = first;
    first = choice;
    choice->info = filterVar2;
    choice->button = w;

    if (f == filterVar2) {
      current = choice;
      gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(w), TRUE);
    }

    choice->signal = g_signal_connect(w, "toggled", G_CALLBACK(filter_select_cb), choice);

    //
    // The spin buttons control width and shift (PBT style)
    //
    w = gtk_label_new("Filter Width");
    gtk_widget_set_name(w, "boldlabel");
    gtk_widget_set_halign(w, GTK_ALIGN_START);
    gtk_grid_attach(GTK_GRID(grid), w, 2, row, 3, 1);
    w = gtk_label_new("Filter Shift");
    gtk_widget_set_name(w, "boldlabel");
    gtk_widget_set_halign(w, GTK_ALIGN_START);
    gtk_grid_attach(GTK_GRID(grid), w, 5, row, 3, 1);
    var1_spin_low = gtk_spin_button_new_with_range(0.0, VAR_MAX_WIDTH, 5.0);
    var2_spin_low = gtk_spin_button_new_with_range(0.0, VAR_MAX_WIDTH, 5.0);
    var1_spin_high = gtk_spin_button_new_with_range(-VAR_MAX_WIDTH, VAR_MAX_WIDTH, 5.0);
    var2_spin_high = gtk_spin_button_new_with_range(-VAR_MAX_WIDTH, VAR_MAX_WIDTH, 5.0);
    int width1 = var_width_of(mymode, filter1);
    int width2 = var_width_of(mymode, filter2);
    gtk_spin_button_set_range(GTK_SPIN_BUTTON(var1_spin_high), -width1, width1);
    gtk_spin_button_set_range(GTK_SPIN_BUTTON(var2_spin_high), -width2, width2);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(var1_spin_low), width1);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(var2_spin_low), width2);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(var1_spin_high), var_shift_of(mymode, filter1));
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(var2_spin_high), var_shift_of(mymode, filter2));

    gtk_grid_attach(GTK_GRID(grid), var1_spin_low, 2, row + 1, 3, 1);
    gtk_grid_attach(GTK_GRID(grid), var2_spin_low, 2, row + 2, 3, 1);
    gtk_grid_attach(GTK_GRID(grid), var1_spin_high, 5, row + 1, 3, 1);
    gtk_grid_attach(GTK_GRID(grid), var2_spin_high, 5, row + 2, 3, 1);
    g_signal_connect(var1_spin_low, "value-changed", G_CALLBACK(var_spin_low_cb), GINT_TO_POINTER(filterVar1));
    g_signal_connect(var2_spin_low, "value-changed", G_CALLBACK(var_spin_low_cb), GINT_TO_POINTER(filterVar2));
    g_signal_connect(var1_spin_high, "value-changed", G_CALLBACK(var_spin_high_cb), GINT_TO_POINTER(filterVar1));
    g_signal_connect(var2_spin_high, "value-changed", G_CALLBACK(var_spin_high_cb), GINT_TO_POINTER(filterVar2));
    GtkWidget *var1_default_b = gtk_button_new_with_label("Default");
    gtk_widget_set_name(var1_default_b, "small_button");
    g_signal_connect (var1_default_b, "button-press-event", G_CALLBACK(var_default_cb), GINT_TO_POINTER(filterVar1));
    gtk_grid_attach(GTK_GRID(grid), var1_default_b, 8, row + 1, 2, 1);
    GtkWidget *var2_default_b = gtk_button_new_with_label("Default");
    gtk_widget_set_name(var2_default_b, "small_button");
    g_signal_connect (var2_default_b, "button-press-event", G_CALLBACK(var_default_cb), GINT_TO_POINTER(filterVar2));
    gtk_grid_attach(GTK_GRID(grid), var2_default_b, 8, row + 2, 2, 1);
    row += 3;

    //
    // Add a checkbox for the CW audio peak filter, if the mode is CWU/CWL
    //
    if (mymode == modeCWU || mymode == modeCWL) {
      w = gtk_separator_new(GTK_ORIENTATION_HORIZONTAL);
      gtk_widget_set_size_request(w, -1, 3);
      gtk_grid_attach(GTK_GRID(grid), w, 0, row++, 10, 1);
      w = gtk_label_new("CW Audio peak filter:");
      gtk_widget_set_name(w, "boldlabel");
      gtk_widget_set_halign(w, GTK_ALIGN_END);
      gtk_grid_attach(GTK_GRID(grid), w, 0, row, 4, 1);
      w = gtk_combo_box_text_new();
      gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(w), NULL, "None");
      gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(w), NULL, "Double Pole");
      gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(w), NULL, "Gaussian");
      gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(w), NULL, "Matched");
      gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(w), NULL, "Bi-Quad");
      gtk_combo_box_set_active(GTK_COMBO_BOX(w), vfo[myrx->id].cwAudioPeakFilter);
      g_signal_connect(w, "changed", G_CALLBACK(cw_apf_cb), NULL);
      my_combo_attach(GTK_GRID(grid), w, 4, row, 4, 1);
      row++;
    }
  }

  //
  // Add manual multi notch area
  //
  w = gtk_separator_new(GTK_ORIENTATION_HORIZONTAL);
  gtk_widget_set_size_request(w, -1, 3);
  gtk_grid_attach(GTK_GRID(grid), w, 0, row++, 10, 1);
  w = gtk_label_new("Enable");
  gtk_widget_set_name(w, "boldlabel");
  gtk_widget_set_halign(w, GTK_ALIGN_CENTER);
  gtk_grid_attach(GTK_GRID(grid), w, 0, row, 2, 1);
  w = gtk_label_new("Notch Center");
  gtk_widget_set_name(w, "boldlabel");
  gtk_widget_set_halign(w, GTK_ALIGN_START);
  gtk_grid_attach(GTK_GRID(grid), w, 2, row, 3, 1);
  w = gtk_label_new("Notch Width");
  gtk_widget_set_name(w, "boldlabel");
  gtk_widget_set_halign(w, GTK_ALIGN_START);
  gtk_grid_attach(GTK_GRID(grid), w, 5, row, 3, 1);
  row++;
  //
  // It is not meant to "spin" until the maxoffset, but the
  // "Default" button should allow this
  //
  double maxoffset = 0.5 * (double)myrx->sample_rate;

  for (int i = 0; i < 3; i++) {
    w = gtk_check_button_new();
    gtk_widget_set_halign(w, GTK_ALIGN_CENTER);
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (w), myrx->multi_notch_enable[i]);
    gtk_grid_attach(GTK_GRID(grid), w, 0, row, 2, 1);
    g_signal_connect(w, "toggled", G_CALLBACK(mn_enable_cb), GINT_TO_POINTER(i));
    w = gtk_spin_button_new_with_range(-maxoffset, maxoffset, 25.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(w), myrx->multi_notch_center[i]);
    gtk_grid_attach(GTK_GRID(grid), w, 2, row, 3, 1);
    g_signal_connect(w, "value-changed", G_CALLBACK(mn_center_cb), GINT_TO_POINTER(i));
    mn_center[i] = w;
    w = gtk_spin_button_new_with_range(myrx->notch_min_width, 1000.0, 25.0);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(w), myrx->multi_notch_width[i]);
    gtk_grid_attach(GTK_GRID(grid), w, 5, row, 3, 1);
    g_signal_connect(w, "value-changed", G_CALLBACK(mn_width_cb), GINT_TO_POINTER(i));
    mn_width[i] = w;
    w = gtk_button_new_with_label("Centre");
    gtk_widget_set_name(w, "small_button");
    g_signal_connect (w, "button-press-event", G_CALLBACK(mn_default_cb), GINT_TO_POINTER(i));
    gtk_grid_attach(GTK_GRID(grid), w, 8, row, 2, 1);
    row++;
  }

  gtk_container_add(GTK_CONTAINER(content), grid);
  sub_menu = dialog;
  gtk_widget_show_all(dialog);
}
