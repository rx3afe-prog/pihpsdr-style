/* Copyright (C)
* 2015 - John Melton, G0ORX/N6LYT
* 2025 - Christoph van Wüllen, DL1YCF
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

#define MAX_TB_FUNCTIONS 6
#define MAX_TB_ROWS 3

//
// Each toolbar row has tb_buttons buttons (MIN_TB_BUTTONS ... MAX_TB_BUTTONS),
// depending on the screen width. The rightmost button is always the
// FNC button, the others show the first tb_buttons-1 configurable actions.
// Actions beyond the visible ones are kept (and stored in the props file).
//
#define MIN_TB_BUTTONS 8
#define MAX_TB_BUTTONS 16
#define MAX_TB_ACTIONS (MAX_TB_BUTTONS - 1)

extern int tb_function[MAX_TB_ROWS];
extern int tb_buttons;
extern enum ACTION tb_actions[MAX_TB_FUNCTIONS][MAX_TB_ACTIONS];

//
// When floating_toolbar is set, toolbar row 0 is shown in its own
// top-level window (8 rows x 2 columns) instead of being embedded
// in the main window. floating_toolbar_x/y remember its position.
//
extern int floating_toolbar;
extern int floating_toolbar_x;
extern int floating_toolbar_y;

extern void toolbar_save_state(void);
extern void toolbar_restore_state(void);

extern void toolbar_create(int width, int height, int rows);
extern void toolbar_destroy(void);
extern void toolbar_show(int ypos);
extern void update_toolbar_labels(void);
extern void toolbar_update_states(void);

extern void toolbar_create_floating(int height, GtkWidget *menu_button, GtkWidget *hide_button);
extern void toolbar_destroy_floating(void);

// Window a menu dialog should be transient for: the floating toolbar if it
// is shown and "deflt" is the main window, otherwise "deflt" unchanged.
extern GtkWidget *toolbar_menu_parent(GtkWidget *deflt);
