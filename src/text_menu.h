#ifndef TEXT_MENU_H
#define TEXT_MENU_H
#include <gtk/gtk.h>

extern GdkRGBA toolbar_text_color;
extern double toolbar_text_size;

void apply_toolbar_text_style(void);
void text_menu(GtkWidget *parent);

#endif
