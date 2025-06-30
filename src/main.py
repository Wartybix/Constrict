# main.py
#
# Copyright 2025 Wartybix
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, GLib
from .window import ConstrictWindow
from constrict.preferences_dialog import PreferencesDialog

# FIXME: icon doesn't show in all contexts on the flatpak version.
# TODO: improve code documentation.

class ConstrictApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='com.github.wartybix.Constrict',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

        self.add_main_option(
            'new-window',
            b'n',
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            'Open a new window',
            None
        )

        self.create_action('new-window', lambda *_: self.do_activate(), ['<primary>n'])
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        # self.create_action('close-window', self.close_window, ['<primary>w'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action, ['<primary>comma'])

        self.open_dir_action = Gio.SimpleAction(
            name="open-dir",
            parameter_type=GLib.VariantType.new('s')
        )
        self.open_dir_action.connect("activate", self.open_dir)
        self.add_action(self.open_dir_action)

        self.focus_window_action = Gio.SimpleAction(
            name="focus-window",
            parameter_type=GLib.VariantType.new('i')
        )
        self.focus_window_action.connect("activate", self.focus_window)
        self.add_action(self.focus_window_action)

        self.set_accels_for_action('app.new-window', ['<primary>n'])
        self.set_accels_for_action('win.toggle-sidebar', ['F9'])
        self.set_accels_for_action('win.open', ['<Ctrl>o'])
        self.set_accels_for_action('win.export', ['<Ctrl>e'])
        self.set_accels_for_action('win.close', ['<Ctrl>w'])

    def open_dir(self, widget, dir_path_gvariant):
        dir_path = dir_path_gvariant.get_string()

        export_dir_file = Gio.File.new_for_path(dir_path)
        file_launcher = Gtk.FileLauncher.new(export_dir_file)
        file_launcher.launch()

    def focus_window(self, widget, window_id_gvariant):
        window_id = window_id_gvariant.get_int32()

        window = self.get_window_by_id(window_id)

        if window:
            window.present()

    def do_open(self, gfiles, n_files, hint):
        self.do_activate(gfiles)

    def do_activate(self, gfiles=[]):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        active_window = self.get_active_window()
        if active_window:
            active_window.save_window_state()

        win = ConstrictWindow(application=self)

        if gfiles:
            win.stage_videos(gfiles)

        win.present()

    # do_handle_local_options is taken from kramo's Showtime project and has
    # been modified slightly:
    # https://gitlab.gnome.org/GNOME/Incubator/showtime/-/blob/main/showtime/main.py
    def do_handle_local_options(  # pylint: disable=arguments-differ
        self, options: GLib.VariantDict
    ) -> int:
        """Handle local command line arguments."""
        self.register()  # This is so get_is_remote works
        if self.get_is_remote():
            if options.contains("new-window"):
                return -1

            logging.warning(
                "Constrict is already running. "
                "To open a new window, run the app with --new-window."
            )
            return 0

        return -1

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name=_('Constrict'),
                                application_icon='com.github.wartybix.Constrict',
                                developer_name='Wartybix',
                                version='0.1.0',
                                developers=['Wartybix https://github.com/Wartybix/'],
                                website='https://github.com/Wartybix/Constrict',
                                issue_url='https://github.com/Wartybix/Constrict/issues',
                                license_type='GTK_LICENSE_GPL_3_0',
                                copyright='© 2025 Wartybix')
        about.add_acknowledgement_section(
            # TRANSLATORS: Braces represent the name of the repository (e.g. 8mb)
            # Please use ‘’ characters instead of '', if applicable to your language.
            _('‘{}’ repository by').format('8mb'),
            [
                'Matthew Baggett https://github.com/matthewbaggett/',
                'Ethan Martin https://github.com/yuckdevchan'
            ]
        )
        about.add_acknowledgement_section(
            _('Circular progress indicator (C version) by'),
            ['Christian Hergert https://gitlab.gnome.org/chergert']
        )
        about.add_acknowledgement_section(
            _('GApplication local option handling by'),
            ['kramo https://kramo.page']
        )
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    #TODO: preference ideas
    # target size unit (e.g., MB, MiB, GB, etc.)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""

        dialog = PreferencesDialog()
        dialog.present(self.props.active_window)

        print('app.preferences action activated')

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def close_window(self, *args):
        current_window = self.get_active_window()
        current_window.close()

    # override
    def quit(self):
        windows = self.get_windows()

        for window in windows:
            window.close()


def main(version):
    """The application's entry point."""
    app = ConstrictApplication()
    return app.run(sys.argv)

