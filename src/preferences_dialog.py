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

from gi.repository import Adw, Gtk, GLib
from constrict.shared import update_ui


@Gtk.Template(resource_path='/io/github/wartybix/Constrict/preferences_dialog.ui')
class PreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "PreferencesDialog"

    # TODO: adjust dialog size?

    suffix_preferences_group = Gtk.Template.Child()
    suffix_entry_row = Gtk.Template.Child()

    def __init__(self, application, **kwargs):
        super().__init__(**kwargs)

        self.suffix_preferences_group.set_description(
            # TRANSLATORS: {} represents the value of the default suffix.
            _('Used in file names for exported videos, between the base name and extension. If the custom suffix is left empty, the default suffix of “{}” will be used.')
                .format(application.default_suffix)
        )

        self.settings = application.get_settings()

        export_suffix_value = self.settings.get_string('custom-export-suffix')
        self.suffix_entry_row.set_text(export_suffix_value)

        self.suffix_entry_row.connect('apply', self.update_custom_suffix)

    def update_custom_suffix(self, widget):
        self.settings.set_string('custom-export-suffix', widget.get_text())

        toast = Adw.Toast.new(_('Changes applied'))
        self.add_toast(toast)
