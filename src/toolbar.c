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

#include "actions.h"
#include "gpio.h"
#include "main.h"
#include "message.h"
#include "property.h"
#include "radio.h"
#include "sliders.h"
#include "toolbar.h"
#include "transmitter.h"
#include "vfo.h"

int tb_function[MAX_TB_ROWS] = {0, 1, 2};
int tb_buttons = MIN_TB_BUTTONS;   // buttons per row, including FNC, set in toolbar_create()

int floating_toolbar = 0;
int floating_toolbar_x = -1;
int floating_toolbar_y = -1;

//
// Slots not listed here are initialised to NO_ACTION
//
enum ACTION tb_actions[MAX_TB_FUNCTIONS][MAX_TB_ACTIONS] = {
  { MOX,   TUNE,           ANF,            MENU_MODE,  MENU_FILTER, MENU_BAND,  MENU_FREQUENCY, CTUN,
    NR,    NB,             SNB,            RIT_PLUS,   RIT_MINUS,   XIT_PLUS,   XIT_MINUS },
  { SPLIT, MENU_BANDSTACK, CTUN,           RIT_PLUS,   RIT_MINUS,   XIT_PLUS,   XIT_MINUS   },
  { MOX,   LOCK,           DUPLEX,         A_TO_B,     B_TO_A,      A_SWAP_B,   SPLIT       },
  { MOX,   MENU_FREQUENCY, SPLIT,          DUPLEX,     SAT,         RSAT,       MENU_BAND   },
  { MOX,   MENU_FREQUENCY, MENU_MEMORY,    RIT_ENABLE, RIT_PLUS,    RIT_MINUS,  RIT_CLEAR   },
  { MOX,   MENU_FREQUENCY, MENU_MEMORY,    XIT_ENABLE, XIT_PLUS,    XIT_MINUS,  XIT_CLEAR   }
};

//
// Layout 1: 8 slots per function, the last one (index 7) being the FNC button.
// Layout 2: MAX_TB_ACTIONS configurable slots, the FNC button is not stored.
//
#define TB_LAYOUT 2

static GtkWidget *toolbar_grid = NULL;
static GtkWidget *floating_window = NULL;
static GtkWidget *floating_grid = NULL;     // grid holding buttons and sliders of the floating window
static int floating_height = 0;   // button height the floating window was built with
static GtkWidget *floating_menu_b = NULL;
static GtkWidget *floating_hide_b = NULL;

static GtkWidget *tblbl[MAX_TB_BUTTONS][MAX_TB_ROWS] = { { NULL }};
static GtkWidget *tbbtn[MAX_TB_BUTTONS][MAX_TB_ROWS] = { { NULL }};

void toolbar_save_state(void) {
  SetPropI0("toolbar.layout", TB_LAYOUT);

  for (int i = 0; i < MAX_TB_ROWS; i++) {
    SetPropI1("toolbar.row[%d]", i, tb_function[i]);
  }

  for (int f = 0; f < MAX_TB_FUNCTIONS; f++) {
    for (int i = 0; i < MAX_TB_ACTIONS; i++) {
      SetPropA2("toolbar[%d,%d].action", f, i, tb_actions[f][i]);
    }
  }

  if (floating_window != NULL) {
    gtk_window_get_position(GTK_WINDOW(floating_window), &floating_toolbar_x, &floating_toolbar_y);
  }

  SetPropI0("toolbar.floating", floating_toolbar);
  SetPropI0("toolbar.floating_x", floating_toolbar_x);
  SetPropI0("toolbar.floating_y", floating_toolbar_y);
}

void toolbar_restore_state(void) {
  int layout = 1;
  GetPropI0("toolbar.layout", layout);

  for (int i = 0; i < MAX_TB_ROWS; i++) {
    GetPropI1("toolbar.row[%d]", i, tb_function[i]);
  }

  for (int f = 0; f < MAX_TB_FUNCTIONS; f++) {
    for (int i = 0; i < MAX_TB_ACTIONS; i++) {
      GetPropA2("toolbar[%d,%d].action", f, i, tb_actions[f][i]);
    }

    if (layout < 2) {
      //
      // Old props file: slot 7 contained the FNC button, which now is
      // a normal (initially empty) slot
      //
      tb_actions[f][7] = NO_ACTION;
    }
  }

  GetPropI0("toolbar.floating", floating_toolbar);
  GetPropI0("toolbar.floating_x", floating_toolbar_x);
  GetPropI0("toolbar.floating_y", floating_toolbar_y);
  {
    extern void tb_css_apply(void); /* TBSTYLE PATCH */
    tb_css_apply();
  }
}

//
// Is the function behind a toolbar button currently "on"? Such buttons are
// shown with a red background. For RIT/XIT the "+" button is on for a positive
// offset and the "-" button for a negative offset.
//
static int toolbar_action_is_on(enum ACTION action) {
  switch (action) {
  case MOX:
    return mox;

  case TUNE:
    return can_transmit && transmitter != NULL && transmitter->tune;

  case ANF:
    return active_receiver->anf;

  case SNB:
    return active_receiver->snb;

  case CTUN:
    return vfo[active_receiver->id].ctun;

  case NR:
    return active_receiver->nr != 0;

  case NB:
    return active_receiver->nb != 0;

  case SPLIT:
    return split;

  case DUPLEX:
    return duplex;

  case SAT:
    return sat_mode == SAT_MODE;

  case RSAT:
    return sat_mode == RSAT_MODE;

  case RIT_PLUS:
    return vfo[active_receiver->id].rit > 0;

  case RIT_MINUS:
    return vfo[active_receiver->id].rit < 0;

  case XIT_PLUS:
    return vfo[vfo_get_tx_vfo()].xit > 0;

  case XIT_MINUS:
    return vfo[vfo_get_tx_vfo()].xit < 0;

  default:
    return 0;
  }
}

void toolbar_update_states(void) {
  for (int i = 0; i < MAX_TB_ROWS; i++) {
    int func = tb_function[i];

    for (int j = 0; j < tb_buttons; j++) {
      GtkWidget *w = tbbtn[j][i];

      if (w == NULL) { continue; }

      GtkStyleContext *ctx = gtk_widget_get_style_context(w);
      int on = (j != tb_buttons - 1) && toolbar_action_is_on(tb_actions[func][j]);
      int has = gtk_style_context_has_class(ctx, "toolbar_on");

      if (on && !has) {
        gtk_style_context_add_class(ctx, "toolbar_on");
      } else if (!on && has) {
        gtk_style_context_remove_class(ctx, "toolbar_on");
      }
    }
  }
}

void update_toolbar_labels(void) {
  for (int i = 0; i < MAX_TB_ROWS; i++) {
    int func = tb_function[i];

    for (int j = 0; j < tb_buttons; j++) {
      GtkWidget *lbl = tblbl[j][i];

      if (lbl) {
        if (j == tb_buttons - 1) {
          char text[16];
          snprintf(text, sizeof(text), "FNC(%d)", tb_function[i]);
          gtk_label_set_text(GTK_LABEL(lbl), text);
        } else {
          gtk_label_set_text(GTK_LABEL(lbl), ActionTable[tb_actions[func][j]].button_str);
        }
      }
    }
  }

  toolbar_update_states();
}

// cppcheck-suppress constParameterCallback
static gboolean toolbar_button_press_cb(GtkWidget *widget, GdkEventButton *event, gpointer data) {
  int val = GPOINTER_TO_INT(data);
  int btn = val % 100;
  int row = val / 100;

  //
  // Filter out any special events generated by double or triple clicks
  //
  if (event->type != GDK_BUTTON_PRESS) { return TRUE; }

  //
  // We have to implement the function key "manually" here, since the
  // "action" only refers to row zero.
  //
  if (btn == tb_buttons - 1) {
    //
    // This is our "easter egg" for the FUNC toolbar button. A secondary (right) click
    // cycles backwards.
    //
    if (event->button == GDK_BUTTON_SECONDARY) {
      tb_function[row]--;

      if (tb_function[row] < 0) { tb_function[row] = MAX_TB_FUNCTIONS - 1; }
    } else {
      tb_function[row]++;

      if (tb_function[row] >= MAX_TB_FUNCTIONS) { tb_function[row] = 0; }
    }

    update_toolbar_labels();
  } else {
    schedule_action(tb_actions[tb_function[row]][btn], PRESSED, 0);
  }

  return FALSE;
}

// cppcheck-suppress constParameterCallback
static gboolean toolbar_button_released_cb(GtkWidget *widget, GdkEventButton *event, gpointer data) {
  int val = GPOINTER_TO_INT(data);
  int btn = val % 100;

  if (btn != tb_buttons - 1) {
    int row = val / 100;
    schedule_action(tb_actions[tb_function[row]][btn], RELEASED, 0);
  }

  return FALSE;
}

void toolbar_show(int ypos) {
  if (toolbar_grid) {
    gtk_fixed_put(GTK_FIXED(fixed),  toolbar_grid, 0, ypos);
    gtk_widget_show_all(toolbar_grid);
  }
}

void toolbar_destroy(void) {
  if (toolbar_grid) {
    gtk_widget_destroy(toolbar_grid);
    toolbar_grid = NULL;

    for (int i = 0; i < MAX_TB_ROWS; i++) {
      for (int j = 0; j < MAX_TB_BUTTONS; j++) {
        tblbl[j][i] = NULL;
        tbbtn[j][i] = NULL;
      }
    }
  }
}

//
// Pick a button CSS class and target button width, scaled with the
// font size implied by the button height. Shared by the embedded
// and the floating toolbar.
//
static void toolbar_button_style(int height, const char **css_out, int *target_width_out) {
  if (height < 40) {
    *css_out = "small_button";
    *target_width_out = 71;
  } else if (height < 50) {
    *css_out = "medium_button";
    *target_width_out = 94;
  } else {
    *css_out = "large_button";
    *target_width_out = 118;
  }
}

//
// Create a single toolbar button (with an ellipsizing label) wired to
// toolbar_button_press_cb/toolbar_button_released_cb, and cache its
// label so update_toolbar_labels() can refresh it later. Shared by the
// embedded and the floating toolbar.
//
static GtkWidget *toolbar_make_button(int row, int col, int width, int height, const char *css) {
  GtkWidget *w = gtk_button_new();
  //
  // Use an ellipsizing label such that a long label cannot make
  // the toolbar wider than the screen
  //
  GtkWidget *lbl = gtk_label_new(NULL);
  gtk_label_set_ellipsize(GTK_LABEL(lbl), PANGO_ELLIPSIZE_END);
  gtk_container_add(GTK_CONTAINER(w), lbl);
  gpointer code = GINT_TO_POINTER(100 * row + col);
  gtk_widget_set_name(w, css);
  GtkStyleContext *tbctx = gtk_widget_get_style_context(w); /* TBSTYLE PATCH */
  gtk_style_context_add_class(tbctx, "tbbtn");
  gtk_widget_set_size_request (w, width, height);
  g_signal_connect(G_OBJECT(w), "button-press-event", G_CALLBACK(toolbar_button_press_cb), code);
  g_signal_connect(G_OBJECT(w), "button-release-event", G_CALLBACK(toolbar_button_released_cb), code);
  tblbl[col][row] = lbl;
  tbbtn[col][row] = w;
  return w;
}

void toolbar_create(int width, int height, int rows) {
  const char *button_css;
  int target_width;   // desired button width, scaled with the font size

  toolbar_button_style(height, &button_css, &target_width);
  tb_buttons = width / target_width;

  if (tb_buttons < MIN_TB_BUTTONS) { tb_buttons = MIN_TB_BUTTONS; }

  if (tb_buttons > MAX_TB_BUTTONS) { tb_buttons = MAX_TB_BUTTONS; }

  int button_width = width / tb_buttons;
  t_print("%s: width=%d height=%d buttons=%d button_width=%d\n", __func__, width, height, tb_buttons, button_width);
  toolbar_destroy();
  toolbar_grid = gtk_grid_new();
  gtk_widget_set_size_request (toolbar_grid, width, rows * height);
  gtk_grid_set_column_homogeneous(GTK_GRID(toolbar_grid), TRUE);
  gtk_grid_set_row_homogeneous(GTK_GRID(toolbar_grid), TRUE);

  for (int i = 0; i < rows; i++) {
    for (int j = 0; j < tb_buttons; j++) {
      GtkWidget *w = toolbar_make_button(i, j, button_width, height, button_css);
      gtk_grid_attach(GTK_GRID(toolbar_grid), w, j, rows - i - 1, 1, 1);
    }
  }

  update_toolbar_labels();
}

// cppcheck-suppress constParameterCallback
static gboolean toolbar_floating_delete_cb(GtkWidget *widget, GdkEvent *event, gpointer data) {
  floating_toolbar = 0;
  toolbar_destroy_floating();
  radio_reconfigure_screen();  // VFO bar width (and the RX2 meter position) depends on the floating toolbar
  return TRUE;
}

//
// Move a widget from one container to another, taking a temporary
// reference so it survives the removal from its old parent. Used to
// shuttle the Menu/Hide buttons between the main window and the
// floating toolbar without destroying them.
//
static void toolbar_reparent(GtkWidget *widget) {
  g_object_ref(widget);
  gtk_container_remove(GTK_CONTAINER(gtk_widget_get_parent(widget)), widget);
}

GtkWidget *toolbar_menu_parent(GtkWidget *deflt) {
  if (deflt == top_window && floating_toolbar && floating_window != NULL && gtk_widget_get_visible(floating_window)) {
    return floating_window;
  }

  return deflt;
}

//
// (Re-)create the sliders to the right of the buttons of the floating window
//
static void toolbar_floating_rebuild_sliders(int height) {
  sliders_create_floating(floating_grid, height, slider_rows);
}

void toolbar_create_floating(int height, GtkWidget *menu_button, GtkWidget *hide_button) {
  const char *button_css;
  int target_width;

  if (floating_window != NULL) {
    if (height == floating_height) {
      //
      // The number or functions of the sliders may have changed
      //
      toolbar_floating_rebuild_sliders(height);
      return;
    }

    //
    // The button height changed (e.g. display size change): rebuild,
    // keeping the window where the user put it.
    //
    gtk_window_get_position(GTK_WINDOW(floating_window), &floating_toolbar_x, &floating_toolbar_y);
    toolbar_destroy_floating();
  }

  floating_height = height;
  //
  // Floating toolbar shows toolbar row 0 only, reflowed from 1x16
  // (horizontal) to 8x2 (vertical). Force tb_buttons to the maximum
  // so the existing button callbacks' FNC-slot detection (col ==
  // tb_buttons - 1) keeps working unmodified.
  //
  tb_buttons = MAX_TB_BUTTONS;
  toolbar_button_style(height, &button_css, &target_width);
  floating_window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  gtk_window_set_title(GTK_WINDOW(floating_window), "piHPSDR-Improved - Toolbar");
  gtk_window_set_transient_for(GTK_WINDOW(floating_window), GTK_WINDOW(top_window));
  gtk_window_set_resizable(GTK_WINDOW(floating_window), FALSE);

  if (floating_toolbar_x >= 0 && floating_toolbar_y >= 0) {
    gtk_window_move(GTK_WINDOW(floating_window), floating_toolbar_x, floating_toolbar_y);
  }

  g_signal_connect(floating_window, "delete-event", G_CALLBACK(toolbar_floating_delete_cb), NULL);
  GtkWidget *grid = gtk_grid_new();
  floating_grid = grid;
  gtk_grid_set_column_homogeneous(GTK_GRID(grid), TRUE);
  gtk_grid_set_row_homogeneous(GTK_GRID(grid), TRUE);
  //
  // Move the Menu and Hide buttons out of the main window and into a
  // row of their own above the toolbar buttons, so all the controls
  // are reachable from the floating window. Their widget names
  // ("menubutton"/"hidebutton") are left untouched so they keep their
  // distinct CSS styling.
  //
  floating_menu_b = menu_button;
  floating_hide_b = hide_button;
  toolbar_reparent(floating_menu_b);
  toolbar_reparent(floating_hide_b);
  gtk_widget_set_size_request(floating_menu_b, target_width, height);
  gtk_widget_set_size_request(floating_hide_b, target_width, height);
  gtk_grid_attach(GTK_GRID(grid), floating_menu_b, 0, 0, 1, 1);
  gtk_grid_attach(GTK_GRID(grid), floating_hide_b, 1, 0, 1, 1);
  g_object_unref(floating_menu_b);
  g_object_unref(floating_hide_b);

  for (int j = 0; j < MAX_TB_BUTTONS; j++) {
    GtkWidget *w = toolbar_make_button(0, j, target_width, height, button_css);
    gtk_grid_attach(GTK_GRID(grid), w, j % 2, j / 2 + 1, 1, 1);
  }

  gtk_container_add(GTK_CONTAINER(floating_window), grid);
  toolbar_floating_rebuild_sliders(height);
  update_toolbar_labels();
  gtk_widget_show_all(floating_window);
  sliders_att_type_changed(NULL);   // show_all revealed the hidden ATT/RF/C25 widgets again
}

void toolbar_destroy_floating(void) {
  if (floating_window) {
    //
    // Move the Menu/Hide buttons back to the main window before
    // destroying the floating window, otherwise they would be
    // destroyed along with it.
    //
    if (floating_menu_b) {
      toolbar_reparent(floating_menu_b);
    }

    if (floating_hide_b) {
      toolbar_reparent(floating_hide_b);
    }

    sliders_destroy();   // the sliders live in the floating window
    gtk_widget_destroy(floating_window);
    floating_window = NULL;
    floating_grid = NULL;

    for (int j = 0; j < MAX_TB_BUTTONS; j++) {
      tblbl[j][0] = NULL;
      tbbtn[j][0] = NULL;
    }

    if (floating_menu_b) {
      gtk_widget_set_size_request(floating_menu_b, MENU_WIDTH, VFO_HEIGHT / 2);
      gtk_fixed_put(GTK_FIXED(fixed), floating_menu_b, display_width[display_size] - MENU_WIDTH, 0);
      gtk_widget_hide(floating_menu_b);
      g_object_unref(floating_menu_b);
      floating_menu_b = NULL;
    }

    if (floating_hide_b) {
      gtk_widget_set_size_request(floating_hide_b, MENU_WIDTH, VFO_HEIGHT / 2);
      gtk_fixed_put(GTK_FIXED(fixed), floating_hide_b, display_width[display_size] - MENU_WIDTH, VFO_HEIGHT / 2);
      gtk_widget_hide(floating_hide_b);
      g_object_unref(floating_hide_b);
      floating_hide_b = NULL;
    }
  }
}
