lines = open('rx_panadapter.c.bak', encoding='utf-8', errors='replace').read().splitlines(True)
block = (
    '\n'
    '  // ZFREQ: compact frequency readout in the top-left corner\n'
    '  {\n'
    '    char zbuf[32];\n'
    '    long long zmhz = frequency / 1000000LL;\n'
    '    long long zkhz = (frequency % 1000000LL) / 1000LL;\n'
    '    long long zhz  = frequency % 1000LL;\n'
    '    snprintf(zbuf, sizeof(zbuf), "%lld.%03lld.%03lld", zmhz, zkhz, zhz);\n'
    '    cairo_select_font_face(cr, DISPLAY_FONT_FACE, CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);\n'
    '    cairo_set_font_size(cr, 10.0 * scalfac);\n'
    '    cairo_set_source_rgba(cr, 0.72, 0.0, 0.0, 1.0);\n'
    '    cairo_move_to(cr, 4.0, 4.0 + 10.0 * scalfac);\n'
    '    cairo_show_text(cr, zbuf);\n'
    '  }\n'
)
out, ok = [], False
for ln in lines:
    out.append(ln)
    if not ok and 'dxcluster_draw_spots(' in ln:
        out.append(block)
        ok = True
open('rx_panadapter.c', 'w', encoding='utf-8').write(''.join(out))
print('rx_panadapter.c : block placed before cairo_destroy, dark red=%s' % ok)
