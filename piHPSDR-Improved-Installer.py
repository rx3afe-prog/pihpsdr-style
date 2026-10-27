#!/usr/bin/env python3
#
# GUI installer for piHPSDR-Improved (Linux only).
#
# Runs LINUX/libinstall.sh (unmodified) as root, then writes the GPIO/SOAPYSDR
# choices the user made into make.config.pihpsdr, then does a "make clean" and
# a "make" to build piHPSDR - all from a single window, with no terminal or
# hand-edited files required. Finally creates the Desktop icon and the
# desktop-menu entry (as the real user, not root).
#

import os
import sys
import subprocess
import threading

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
except ImportError:
    print("This installer needs GTK3 Python bindings, which are not installed.")
    print("Please run this command in a terminal, then try again:")
    print()
    print("    sudo apt install python3-gi gir1.2-gtk-3.0")
    print()
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(SCRIPT_DIR, "installer.jpeg")
MAKE_CONFIG_PATH = os.path.join(SCRIPT_DIR, "make.config.pihpsdr")


def is_raspberry_pi():
    for path in ("/proc/device-tree/model", "/proc/cpuinfo"):
        try:
            with open(path, "r", errors="ignore") as f:
                if "Raspberry Pi" in f.read():
                    return True
        except OSError:
            pass
    return False


def desktop_entry_text():
    icon = os.path.join(SCRIPT_DIR, "release", "pihpsdr", "piHPSDR_logo.png")
    if not os.path.exists(icon):
        icon = os.path.join(SCRIPT_DIR, "release", "pihpsdr", "hpsdr.png")
    exe = os.path.join(SCRIPT_DIR, "pihpsdr")
    if " " in exe:
        exe = '"%s"' % exe
    return (
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        "Name=piHPSDR-Improved\n"
        "Comment=SDR transceiver software\n"
        "Exec=%s\n"
        "Path=%s\n"
        "Icon=%s\n"
        "Terminal=false\n"
        "Categories=HamRadio;AudioVideo;Audio;\n"
        "StartupNotify=true\n" % (exe, SCRIPT_DIR, icon)
    )


def run_quiet(cmd):
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return r.returncode, r.stdout.strip()
    except OSError:
        return -1, ""


def create_desktop_entries(log):
    home = os.path.expanduser("~")
    apps_dir = os.path.join(home, ".local", "share", "applications")
    rc, out = run_quiet(["xdg-user-dir", "DESKTOP"])
    desktop_dir = out if rc == 0 and out else os.path.join(home, "Desktop")

    text = desktop_entry_text()
    name = "pihpsdr-improved.desktop"
    stale = ("pihpsdr.desktop", "pihpsdr-Improved.desktop", name)

    targets = [apps_dir]
    if os.path.isdir(desktop_dir):
        targets.append(desktop_dir)
    else:
        log("Desktop directory %s not found - skipping Desktop icon.\n" % desktop_dir)

    for d in targets:
        try:
            os.makedirs(d, exist_ok=True)
        except OSError as e:
            log("WARNING: cannot create %s: %s\n" % (d, e))
            continue
        for old in stale:
            try:
                os.remove(os.path.join(d, old))
            except FileNotFoundError:
                pass
            except OSError as e:
                log("WARNING: cannot remove old %s: %s\n" % (os.path.join(d, old), e))
        path = os.path.join(d, name)
        try:
            with open(path, "w") as f:
                f.write(text)
            os.chmod(path, 0o750)
        except OSError as e:
            log("WARNING: cannot write %s: %s\n" % (path, e))
            continue
        run_quiet(["gio", "set", path, "metadata::trusted", "true"])
        rc, out = run_quiet(["desktop-file-validate", path])
        log("Created %s%s\n" % (path, "" if rc in (0, -1) else " (validation: %s)" % out))

    run_quiet(["update-desktop-database", apps_dir])


def update_make_config(gpio_on, soapy_on):
    settings = {
        "GPIO": "ON" if gpio_on else "OFF",
        "SOAPYSDR": "ON" if soapy_on else "OFF",
    }

    lines = []
    if os.path.exists(MAKE_CONFIG_PATH):
        with open(MAKE_CONFIG_PATH, "r") as f:
            lines = f.readlines()

    seen = set()
    new_lines = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in settings:
            new_lines.append("%s=%s\n" % (key, settings[key]))
            seen.add(key)
        else:
            new_lines.append(line)

    for key, value in settings.items():
        if key not in seen:
            new_lines.append("%s=%s\n" % (key, value))

    with open(MAKE_CONFIG_PATH, "w") as f:
        f.writelines(new_lines)


class InstallerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="piHPSDR-Improved Installer")
        self.set_border_width(12)
        screen_w, screen_h = self._screen_size()
        win_w = min(640, screen_w - 20)
        win_h = min(520, screen_h - 40)
        self.set_default_size(win_w, win_h)
        self.connect("destroy", Gtk.main_quit)

        self.password = None

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(outer)

        # Reserve room for the rest of the UI; shrink (or drop) the banner on small screens.
        image = self._load_image(min(480, win_w - 24), min(320, win_h - 260))
        if image is not None:
            outer.pack_start(image, False, False, 0)

        intro = Gtk.Label(
            label="This will install the system packages piHPSDR-Improved needs, then "
                  "build it from source.\nChoose your options and click Install."
        )
        intro.set_line_wrap(True)
        outer.pack_start(intro, False, False, 0)

        self.gpio_check = Gtk.CheckButton(
            label="Enable GPIO support (Raspberry Pi front-panel controllers)"
        )
        self.gpio_check.set_active(is_raspberry_pi())
        outer.pack_start(self.gpio_check, False, False, 0)

        self.soapy_check = Gtk.CheckButton(
            label="Enable SoapySDR support (RTL-SDR, HackRF, PlutoSDR, etc. over USB)"
        )
        self.soapy_check.set_active(False)
        outer.pack_start(self.soapy_check, False, False, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        outer.pack_start(button_box, False, False, 0)

        self.install_button = Gtk.Button(label="Install")
        self.install_button.connect("clicked", self.on_install_clicked)
        button_box.pack_start(self.install_button, False, False, 0)

        self.launch_button = Gtk.Button(label="Launch piHPSDR-Improved now")
        self.launch_button.connect("clicked", self.on_launch_clicked)
        self.launch_button.set_sensitive(False)
        button_box.pack_start(self.launch_button, False, False, 0)

        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda *_: Gtk.main_quit())
        button_box.pack_start(close_button, False, False, 0)

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        outer.pack_start(status_box, False, False, 0)

        self.spinner = Gtk.Spinner()
        status_box.pack_start(self.spinner, False, False, 0)

        self.status_label = Gtk.Label(label="Ready.")
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_min_content_height(60)
        outer.pack_start(scroller, True, True, 0)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_monospace(True)
        self.log_buffer = self.log_view.get_buffer()
        scroller.add(self.log_view)

    def _screen_size(self):
        # Usable size of the primary monitor; default to a 7in 800x480 panel if unknown.
        try:
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor() or display.get_monitor(0)
            area = monitor.get_workarea()
            return area.width, area.height
        except (AttributeError, TypeError):
            return 800, 480

    def _load_image(self, max_w, max_h):
        if max_w < 60 or max_h < 60:
            return None
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                IMAGE_PATH, max_w, max_h, True
            )
        except GLib.Error:
            return None
        return Gtk.Image.new_from_pixbuf(pixbuf)

    def append_log(self, text):
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, text)
        end_iter = self.log_buffer.get_end_iter()
        self.log_view.scroll_to_iter(end_iter, 0.0, False, 0, 0)
        return False

    def set_status(self, text):
        self.status_label.set_text(text)
        return False

    def on_install_clicked(self, _button):
        password = self.prompt_for_password()
        if password is None:
            return

        self.password = password
        self.gpio_check.set_sensitive(False)
        self.soapy_check.set_sensitive(False)
        self.install_button.set_sensitive(False)
        self.spinner.start()

        gpio_on = self.gpio_check.get_active()
        soapy_on = self.soapy_check.get_active()

        thread = threading.Thread(
            target=self.run_install, args=(password, gpio_on, soapy_on), daemon=True
        )
        thread.start()

    def prompt_for_password(self):
        dialog = Gtk.Dialog(
            title="Administrator password required",
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK,
        )

        content = dialog.get_content_area()
        content.set_border_width(10)
        content.set_spacing(6)

        label = Gtk.Label(
            label="piHPSDR-Improved needs administrator rights to install packages.\n"
                  "Please enter your password:"
        )
        content.add(label)

        entry = Gtk.Entry()
        entry.set_visibility(False)
        entry.set_activates_default(True)
        content.add(entry)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()
        response = dialog.run()
        password = entry.get_text() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        return password

    def run_install(self, password, gpio_on, soapy_on):
        GLib.idle_add(self.set_status, "Installing system packages...")
        GLib.idle_add(self.append_log, "=== Running LINUX/libinstall.sh ===\n")

        ok = self.run_command(
            ["sudo", "-S", "-p", "", "stdbuf", "-oL", "-eL", "bash", "LINUX/libinstall.sh"],
            cwd=SCRIPT_DIR,
            stdin_text=password + "\n",
        )
        if not ok:
            GLib.idle_add(self.finish, False, "Package installation failed - see log above.")
            return

        GLib.idle_add(self.set_status, "Configuring build options...")
        GLib.idle_add(
            self.append_log,
            "\n=== Writing make.config.pihpsdr (GPIO=%s, SOAPYSDR=%s) ===\n"
            % ("ON" if gpio_on else "OFF", "ON" if soapy_on else "OFF"),
        )
        try:
            update_make_config(gpio_on, soapy_on)
        except OSError as e:
            GLib.idle_add(self.append_log, "ERROR writing make.config.pihpsdr: %s\n" % e)
            GLib.idle_add(self.finish, False, "Could not write build configuration.")
            return

        GLib.idle_add(self.set_status, "Building piHPSDR...")
        GLib.idle_add(self.append_log, "\n=== Running make clean ===\n")
        if not self.run_command(["stdbuf", "-oL", "-eL", "make", "clean"], cwd=SCRIPT_DIR):
            GLib.idle_add(self.finish, False, "\"make clean\" failed - see log above.")
            return

        GLib.idle_add(self.append_log, "\n=== Running make ===\n")
        if not self.run_command(["stdbuf", "-oL", "-eL", "make"], cwd=SCRIPT_DIR):
            GLib.idle_add(self.finish, False, "Build failed - see log above.")
            return

        GLib.idle_add(self.set_status, "Creating Desktop icon and menu entry...")
        GLib.idle_add(self.append_log, "\n=== Creating Desktop icon and menu entry ===\n")
        try:
            create_desktop_entries(lambda t: GLib.idle_add(self.append_log, t))
        except Exception as e:
            GLib.idle_add(self.append_log, "WARNING: desktop entry creation failed: %s\n" % e)

        GLib.idle_add(self.finish, True, "Installation complete!")

    def run_command(self, cmd, cwd, stdin_text=None):
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as e:
            GLib.idle_add(self.append_log, "ERROR: could not run %s: %s\n" % (cmd[0], e))
            return False

        if stdin_text is not None:
            process.stdin.write(stdin_text)
        process.stdin.close()

        for line in process.stdout:
            GLib.idle_add(self.append_log, line)
        process.stdout.close()

        return process.wait() == 0

    def finish(self, success, message):
        self.spinner.stop()
        self.set_status(message)
        if success:
            self.launch_button.set_sensitive(True)
        return False

    def on_launch_clicked(self, _button):
        binary = os.path.join(SCRIPT_DIR, "pihpsdr")
        try:
            subprocess.Popen([binary], cwd=SCRIPT_DIR)
        except OSError as e:
            self.append_log("ERROR launching piHPSDR-Improved: %s\n" % e)


def main():
    win = InstallerWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
