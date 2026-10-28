p = '/home/rx3afe/piHPSDR-style/src/receiver.c'
r = open(p).read()

if 'void rx_set_active(' in r:
    print('rx_set_active uzhe na meste, nichego ne delayu')
else:
    anchor = '// cppcheck-suppress constParameterPointer\ngboolean rx_button_release_event('
    i = r.find(anchor)
    if i < 0:
        print('!! yakor rx_button_release_event ne nayden')
        raise SystemExit(1)

    func = '''void rx_set_active(RECEIVER *rx) {
  if (radio_is_remote) {
    send_rx_select(cl_sock_tcp, rx->id);
  }

  //
  // Abort any frequency entering in the current receiver
  //
  vfo_num_pad(-1, active_receiver->id);
  //
  // Make rx the new active receiver
  //
  active_receiver = rx;

  rx_redraw_panels();
  g_idle_add(menu_active_receiver_changed, NULL);
  g_idle_add(ext_vfo_update, NULL);
  g_idle_add(sliders_active_receiver_changed, NULL);

  //
  // Changing the active receiver flips the TX vfo
  // and possibly the TX band
  //
  if (!radio_is_remote) {
    radio_tx_vfo_changed();
    radio_apply_band_settings(0, 0);
  }
}

'''

    r = r[:i] + func + r[i:]
    open(p, 'w').write(r)
    print('OK: rx_set_active vernula na mesto')

