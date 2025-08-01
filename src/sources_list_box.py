# sources_list_box.py
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
from constrict.sources_row import SourcesRow
from constrict import PREFIX
from typing import Any, List


@Gtk.Template(resource_path=f'{PREFIX}/sources_list_box.ui')
class SourcesListBox(Gtk.ListBox):
    """ The list box that holds all rows representing videos to be compressed,
    and a button row to add more videos to it """
    __gtype_name__ = "SourcesListBox"

    add_videos_button = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.locked = False

    def remove(self, child: Gtk.Widget) -> None:
        """ Remove a child from the list box """
        super().remove(child)
        self.update_rows(False)

    def remove_all(self) -> None:
        """ Remove every child the list box, bar the add videos button """
        super().remove_all()
        self.append(self.add_videos_button)

    def set_locked(self, locked: bool, daemon: bool):
        """ Set whether or not the list box and the rows therein are
        interactable
        """
        self.locked = locked

        self.update_rows(daemon)

    def get_length(self) -> int:
        """ Return the number of rows in the list box, excluding the
        "add videos" button row
        """
        return self.add_videos_button.get_index()

    def any(self) -> bool:
        """ Return whether there are any rows (bar the 'add videos' button) in
        the list box
        """
        return self.get_length() > 0

    def add_sources(self, video_source_rows: List[SourcesRow]) -> None:
        """ Add a list of SourcesRow rows as children of the list box """
        dest_index = self.get_length()

        for row in video_source_rows:
            self.insert(row, dest_index)
            dest_index += 1

        self.update_rows(False)

    def get_all(self) -> List[SourcesRow]:
        """ Get all rows of the list box, bar the 'add videos' button row """
        length = self.get_length()
        sources = []

        for i in range(length):
            row = self.get_row_at_index(i)
            sources.append(row)

        return sources

    def move(self, source_row: SourcesRow, dest_row: SourcesRow) -> None:
        """ Move a row to a new destination """
        dest_index = dest_row.get_index()

        self.remove(source_row)
        self.insert(source_row, dest_index)

        self.update_rows(False)

    def update_row(
        self,
        row: SourcesRow,
        index: int,
        length: int,
        daemon: bool
    ) -> None:
        """ Update the interactivity of a row """
        row.set_draggable(length > 1 and not self.locked)
        update_ui(row.show_drag_handle, not self.locked, daemon)

        row.action_set_enabled(
            'row.move-up',
            index > 0 and not self.locked
        )
        row.action_set_enabled(
            'row.move-down',
            index < (length - 1) and not self.locked
        )
        row.action_set_enabled(
            'row.remove',
            not self.locked
        )

    def update_rows(self, daemon: bool) -> None:
        """ Update the interactivity of all rows """
        rows = self.get_all()

        for i in range(len(rows)):
            row = rows[i]
            self.update_row(row, i, len(rows), daemon)
