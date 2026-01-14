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
from constrict import APPLICATION_ID, VERSION, PREFIX
from typing import List, Sequence, Callable, Any
import asyncio
from gi.events import GLibEventLoopPolicy

policy = GLibEventLoopPolicy()
asyncio.set_event_loop_policy(policy)

# FIXME: occasional segmentation fault on compression completion? No idea what
# the cause is yet. It's seemingly random.

class ConstrictApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self) -> None:
        super().__init__(application_id=APPLICATION_ID,
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

        self.add_main_option(
            'new-window',
            b'n',
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            'Open a new window',
            None
        )

        self.loop = policy.get_event_loop()

        self.create_action('new-window', lambda *_: self.new_window(), ['<primary>n'])
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
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

        self.settings = Gio.Settings(schema_id=self.get_application_id())

        # TRANSLATORS: used in parentheses for the default suffix of exported
        # files.
        self.default_suffix = f" ({_('compressed')})"

    def get_settings(self) -> Gio.Settings:
        """ Get the application's settings """
        return self.settings

    def open_dir(
        self,
        widget: Gtk.Widget,
        dir_path_gvariant: GLib.Variant
    ) -> None:
        """ Open the passed file path in the user's file manager """
        dir_path = dir_path_gvariant.get_string()

        export_dir_file = Gio.File.new_for_path(dir_path)
        file_launcher = Gtk.FileLauncher.new(export_dir_file)
        file_launcher.launch()

    def focus_window(
        self,
        widget: Gtk.Widget,
        window_id_gvariant: GLib.Variant
    ) -> None:
        """ Bring a window in focus """
        window_id = window_id_gvariant.get_int32()

        window = self.get_window_by_id(window_id)

        if window:
            window.present()
        else:
            self.do_activate()

    def do_open(self, gfiles: List[Gio.File], n_files: int, hint: str) -> None:
        """ Open the application, with the list of files staged for compression
        """
        self.new_window(gfiles)

    def do_activate(self) -> None:
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        active_window = self.get_active_window()
        if active_window:
            active_window.present()
        else:
            self.new_window()

    def new_window(self, gfiles: List[Gio.File] = []) -> None:
        """ Create a new window for the application, optionally with some
        videos already staged.
        """
        active_window = self.get_active_window()
        if active_window:
            active_window.save_window_state()

        win = ConstrictWindow(application=self)
        if self.get_application_id() == "io.github.wartybix.Constrict.Devel":
            win.get_style_context().add_class("devel")

        if gfiles:
            self.loop.create_task(win.stage_videos(gfiles))

        win.present()

    def do_handle_local_options(  # pylint: disable=arguments-differ
        self, options: GLib.VariantDict
    ) -> int:
        """Handle local command line arguments."""
        self.register()
        if options.contains("new-window"):
            self.activate_action('new-window')
            return 0
        return -1

    def on_about_action(self, *args: Any) -> None:
        """Callback for the app.about action."""
        about = Adw.AboutDialog.new_from_appdata(
            f"{PREFIX}/{APPLICATION_ID}.metainfo.xml", VERSION
        )

        about.set_version(VERSION)

        about.set_developers([
            'Wartybix https://github.com/Wartybix/',
            'Philipp Kosarev https://github.com/PhilippKosarev'
        ])

        about.set_artists(['Jakub Steiner <jimmac@gmail.com>'])

        about.set_copyright('© 2025 Wartybix')

        about.add_acknowledgement_section(
            # TRANSLATORS: Braces represent the name of the repository (e.g. 8mb)
            _('‘{}’ repository by').format('8mb'),
            [
                'Matthew Baggett https://github.com/matthewbaggett/',
                'Ethan Martin https://github.com/yuckdevchan'
            ]
        )
        about.add_acknowledgement_section(
            _('Circular progress indicator design by'),
            ['Christian Hergert https://gitlab.gnome.org/chergert']
        )
        about.add_acknowledgement_section(
            _('Drag overlay design by'),
            [
                'Sophie Herold https://gitlab.gnome.org/sophie-h',
                'Sam Hewitt https://gitlab.gnome.org/snwh'
            ]
        )
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    def on_preferences_action(self, widget: Gtk.Widget, _) -> None:
        """Callback for the app.preferences action."""

        dialog = PreferencesDialog(self)
        dialog.present(self.props.active_window)

    def create_action(
        self,
        name: str,
        callback: Callable,
        shortcuts: Sequence[str] | None = None
    ) -> None:
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

    def close_window(self, *args: Any) -> None:
        """ Close the currently focused window """
        current_window = self.get_active_window()
        current_window.close()

    def quit(self) -> None:
        """ Recursively close all the application's windows. Overrides
        Gio.Application's method of quit, which immediately terminates the
        application. This allows each window to close gracefully, for example
        showing a cancel dialog for a window still compressing videos.
        """
        windows = self.get_windows()

        for window in windows:
            window.close()


def main(version: int) -> int:
    """The application's entry point."""
    app = ConstrictApplication()
    return app.run(sys.argv)

