# window.py
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

from gi.repository import Adw, Gtk, Gio
from constrict.constrict_utils import compress, preview

@Gtk.Template(resource_path='/com/github/wartybix/Constrict/window.ui')
class ConstrictWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ConstrictWindow'

    split_view = Gtk.Template.Child()
    view_stack = Gtk.Template.Child()
    export_button = Gtk.Template.Child()
    video_queue = Gtk.Template.Child()
    add_videos_button = Gtk.Template.Child()
    target_size_input = Gtk.Template.Child()
    auto_check_button = Gtk.Template.Child()
    clear_check_button = Gtk.Template.Child()
    smooth_check_button = Gtk.Template.Child()
    codec_dropdown = Gtk.Template.Child()
    extra_quality_toggle = Gtk.Template.Child()
    tolerance_input = Gtk.Template.Child()

    staged_videos = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        toggle_sidebar_action = Gio.SimpleAction(name="toggle-sidebar")
        toggle_sidebar_action.connect("activate", self.toggle_sidebar)
        self.add_action(toggle_sidebar_action)

        open_action = Gio.SimpleAction(name="open")
        open_action.connect("activate", self.open_file_dialog)
        self.add_action(open_action)

        export_action = Gio.SimpleAction(name="export")
        export_action.connect("activate", self.export_file_dialog)
        self.add_action(export_action)

        self.target_size_input.connect("value-changed", self.refresh_previews)
        self.auto_check_button.connect("activate", self.refresh_previews)
        self.clear_check_button.connect("activate", self.refresh_previews)
        self.smooth_check_button.connect("activate", self.refresh_previews)

    def refresh_previews(self, _):
        print(f"Previews refreshed")

    def get_fps_mode(self):
        if self.auto_check_button.get_active():
            return 'auto'
        if self.clear_check_button.get_active():
            return 'prefer-clear'
        if self.smooth_check_button.get_active():
            return 'prefer-smooth'

        raise Exception('Tried to get fps mode, but none was set.')

    def open(self, action, _):
        print("Open action run")

    def export(self, action, _):
        print("Export action run")

    def toggle_sidebar(self, action, _):
        sidebar_shown = self.split_view.get_show_sidebar()
        self.split_view.set_show_sidebar(not sidebar_shown)

    def export_file_dialog(self, action, parameter):
        native = Gtk.FileDialog()
        native.select_folder(self, None, self.on_export_response)

    def on_export_response(self, dialog, result):
        folder = dialog.select_folder_finish(result)

        if not folder:
            return

        print(folder.get_path())

        codecs = ['h264', 'hevc', 'av1']

        target_size = int(self.target_size_input.get_value())
        fps_mode = self.get_fps_mode()
        codec = codecs[self.codec_dropdown.get_selected()]
        extra_quality = self.extra_quality_toggle.get_active()
        tolerance = int(self.tolerance_input.get_value())

        print(f'fps mode: {fps_mode}')
        print(f'codec: {codec}')

        for video in self.staged_videos:
            compress(
                video,
                target_size,
                fps_mode,
                extra_quality,
                codec,
                tolerance,
                None,
                lambda x: print(x)
            )

    def open_file_dialog(self, action, parameter):
        # Create new file selection dialog, using "open" mode
        native = Gtk.FileDialog()
        video_filter = Gtk.FileFilter()

        video_filter.add_mime_type('video/*')
        video_filter.set_name('Videos')

        native.set_default_filter(video_filter)
        native.set_title('Pick Videos')

        native.open_multiple(self, None, self.on_open_response)

    def on_open_response(self, dialog, result):
        files = dialog.open_multiple_finish(result)

        if not files:
            return

        self.video_queue.remove(self.add_videos_button)

        for video in files:
            # TODO: make async query?
            video_path = video.get_path()

            if video_path in self.staged_videos:
                continue

            info = video.query_info('standard::display-name', Gio.FileQueryInfoFlags.NONE)
            display_name = info.get_display_name() if info else video.get_basename()
            print(f'{video.get_basename()} - {video_path}')

            # TODO: Add thumbnail -- I think Nautilus generates one from a
            # frame 1/3 through the video

            target_size = int(self.target_size_input.get_value())
            fps_mode = self.get_fps_mode()

            action_row = Adw.ActionRow()
            action_row.set_title(display_name)

            subtitle = preview(video_path, target_size, fps_mode)
            action_row.set_subtitle(subtitle)

            self.video_queue.add(action_row)
            self.staged_videos.append(video.get_path())

        self.video_queue.add(self.add_videos_button)

        if self.staged_videos:
            self.view_stack.set_visible_child_name('queue_page')

        print(self.staged_videos)
