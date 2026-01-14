# error_dialog.py
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

from gi.repository import Adw, Gtk, Gdk, GLib
from constrict import PREFIX
from typing import Any

@Gtk.Template(resource_path=f'{PREFIX}/error_dialog.ui')
class ErrorDialog(Adw.Dialog):
    """ An dialog showing the details of a video's compression error """
    __gtype_name__ = "ErrorDialog"

    preference_page = Gtk.Template.Child()
    text_view = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(
        self,
        video_name: str,
        error_details: str,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)

        safe_video_name = GLib.markup_escape_text(video_name)

        self.preference_page.set_description(
            # TRANSLATORS: {} represents the filename of the video with the
            # error.
            _('There was a problem compressing “{}”').format(safe_video_name)
        )
        buffer = self.text_view.get_buffer()
        buffer.set_text(error_details)

        self.install_action('dialog.copy-details', None, self.copy_details)

    def copy_details(
        self,
        widget: Gtk.Widget,
        action_name: str,
        parameter: GLib.Variant
    ) -> None:
        """ Copy the text in the 'details' text box to the clipboard """
        text_buffer = widget.text_view.get_buffer()

        start, end = text_buffer.get_bounds()

        text_str = text_buffer.get_text(start, end, False)

        widget.get_clipboard().set(text_str)

        toast = Adw.Toast.new(_("Details copied to clipboard"))
        widget.toast_overlay.add_toast(toast)
