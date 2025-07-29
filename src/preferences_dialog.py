# preferences_dialog.py
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

from gi.repository import Adw, Gtk, GLib, Gio
from constrict.shared import update_ui
from constrict import PREFIX
from typing import Any


@Gtk.Template(resource_path=f'{PREFIX}/preferences_dialog.ui')
class PreferencesDialog(Adw.PreferencesDialog):
    """ The application's preferences dialog """
    __gtype_name__ = "PreferencesDialog"

    suffix_info_label = Gtk.Template.Child()
    suffix_entry_row = Gtk.Template.Child()
    gpu_encoding_row = Gtk.Template.Child()

    # TODO: Maybe do add a megabyte/mebibyte preference.

    def __init__(self, application: Adw.Application, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.suffix_info_label.set_label(
            # TRANSLATORS: {} represents the value of the default suffix.
            _('Used in file names for exported videos, between the base name and extension. If the custom suffix is left empty, the default suffix of “{}” will be used.')
                .format(application.default_suffix)
        )

        self.settings = application.get_settings()

        self.settings.bind(
            'use-gpu-encoding',
            self.gpu_encoding_row,
            'active',
            Gio.SettingsBindFlags.DEFAULT
        )

        export_suffix_value = self.settings.get_string('custom-export-suffix')
        self.suffix_entry_row.set_text(export_suffix_value)

        self.suffix_entry_row.connect('apply', self.update_custom_suffix)

    def update_custom_suffix(self, widget: Gtk.Widget) -> None:
        """ Set a new exported file suffix to the application's settings """
        self.settings.set_string('custom-export-suffix', widget.get_text())

        toast = Adw.Toast.new(_('Changes applied'))
        self.add_toast(toast)
