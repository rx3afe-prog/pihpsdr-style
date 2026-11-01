#include <gtk/gtk.h>
#include <stdio.h>

#include "text_menu.h"

GdkRGBA toolbar_text_color = { 1.0, 1.0, 1.0, 0.35 };
double toolbar_text_size = 1.0;

static GtkWidget *text_window = NULL;
static GtkCssProvider *text_provider = NULL;

void apply_toolbar_text_style(void) {
  char css[512];
  GError *error = NULL;

  if (text_provider == NULL) {
    GdkScreen *screen = gdk_display_get_default_screen(gdk_display_get_default());
    text_provider = gtk_css_provider_new();
    gtk_style_context_add_provider_for_screen(screen,
        GTK_STYLE_PROVIDER(text_provider), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION + 100);
  }

  const char *color = gdk_rgba_to_string(&toolbar_text_color);
  int small = (int)(15.0 * toolbar_text_size + 0.5);
  int medium = (int)(20.0 * toolbar_text_size + 0.5);
  int large = (int)(25.0 * toolbar_text_size + 0.5);

  snprintf(css, sizeof(css),
    "#small_button label { color: %s; font-size: %dpx; }\n"
    "#medium_button label { color: %s; font-size: %dpx; }\n"
    "#large_button label { color: %s; font-size: %dpx; }\n",
    color, small, color, medium, color, large);

  if (!gtk_css_provider_load_from_data(text_provider, css, -1, &error)) {
    fprintf(stderr, "%s: %s\n", __func__, error->message);
    g_clear_error(&error);
  }
}

static void toolbar_text_color_set_cb(GtkWidget *widget, gpointer data) {
  gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(widget), &toolbar_text_color);
  apply_toolbar_text_style();
}

static void toolbar_text_size_value_changed_cb(GtkWidget *widget, gpointer data) {
  toolbar_text_size = gtk_range_get_value(GTK_RANGE(widget));
  apply_toolbar_text_style();
}

static void toolbar_text_reset_cb(GtkWidget *widget, gpointer data) {
  toolbar_text_color.red = 1.0;
  toolbar_text_color.green = 1.0;
  toolbar_text_color.blue = 1.0;
  toolbar_text_color.alpha = 0.35;
  toolbar_text_size = 1.0;
  apply_toolbar_text_style();
}

void text_menu(GtkWidget *parent) {
  if (text_window != NULL) {
    gtk_window_present(GTK_WINDOW(text_window));
    return;
  }

  text_window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  gtk_window_set_title(GTK_WINDOW(text_window), "piHPSDR - Text");
  gtk_window_set_position(GTK_WINDOW(text_window), GTK_WIN_POS_CENTER);
  gtk_window_set_transient_for(GTK_WINDOW(text_window), GTK_WINDOW(parent));
  g_signal_connect(text_window, "destroy", G_CALLBACK(gtk_widget_destroyed), &text_window);

  GtkWidget *grid = gtk_grid_new();
  gtk_grid_set_row_spacing(GTK_GRID(grid), 6);
  gtk_grid_set_column_spacing(GTK_GRID(grid), 6);
  gtk_container_set_border_width(GTK_CONTAINER(grid), 10);
  gtk_container_add(GTK_CONTAINER(text_window), grid);

  int row = 0;
  GtkWidget *label = gtk_label_new("Toolbar Text Color");
  gtk_widget_set_halign(label, GTK_ALIGN_END);
  gtk_grid_attach(GTK_GRID(grid), label, 0, row, 1, 1);
  GtkWidget *color = gtk_color_button_new();
  gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(color), &toolbar_text_color);
  gtk_grid_attach(GTK_GRID(grid), color, 1, row, 1, 1);
  g_signal_connect(color, "color-set", G_CALLBACK(toolbar_text_color_set_cb), NULL);
  row++;

  label = gtk_label_new("Font Size");
  gtk_widget_set_halign(label, GTK_ALIGN_END);
  gtk_grid_attach(GTK_GRID(grid), label, 0, row, 1, 1);
  GtkWidget *scale = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0.5, 2.5, 0.05);
  gtk_range_set_value(GTK_RANGE(scale), toolbar_text_size);
  gtk_widget_set_size_request(scale, 200, -1);
  gtk_grid_attach(GTK_GRID(grid), scale, 1, row, 1, 1);
  g_signal_connect(scale, "value-changed", G_CALLBACK(toolbar_text_size_value_changed_cb), NULL);
  row++;

  GtkWidget *reset = gtk_button_new_with_label("Reset");
  gtk_grid_attach(GTK_GRID(grid), reset, 1, row, 1, 1);
  g_signal_connect(reset, "clicked", G_CALLBACK(toolbar_text_reset_cb), NULL);

  gtk_widget_show_all(text_window);
  apply_toolbar_text_style();
}
