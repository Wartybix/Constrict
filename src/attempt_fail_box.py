# attempt_fail_box.py
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


@Gtk.Template(resource_path='/io/github/wartybix/Constrict/attempt_fail_box.ui')
class AttemptFailBox(Gtk.Box):
    __gtype_name__ = "AttemptFailBox"

    attempt_label = Gtk.Template.Child()
    target_label = Gtk.Template.Child()
    failure_icon = Gtk.Template.Child()
    failure_details_label = Gtk.Template.Child()

    def __init__(
        self,
        attempt_no,
        vid_bitrate,
        is_hq_audio,
        vid_height,
        vid_fps,
        compressed_size_bytes,
        target_size_bytes,
        **kwargs
    ):
        super().__init__(**kwargs)

        # TRANSLATORS: {} represents the attempt number.
        self.attempt_label.set_label(_("Attempt {}").format(str(attempt_no)))

        # TRANSLATORS: this is an abbreviation of 'High Quality'
        hq_label = _('HQ')

        # TRANSLATORS: this is an abbreviation of 'Low Quality'
        lq_label = _('LQ')

        # TRANSLATORS: {vid_br} represents a bitrate value.
        # {res_fps} represents a resolution + framerate (e.g. '1080p@30').
        # {audio_quality} represents audio quality (i.e. 'HQ' or 'LQ')
        target_str = _("{vid_br} ({res_fps}, {audio_quality} audio)").format(
            vid_br = f'{str(vid_bitrate // 1000)} Kbps',
            res_fps = f'{vid_height}p@{vid_fps}',
            audio_quality = hq_label if is_hq_audio else lq_label
        )
        self.target_label.set_label(target_str)

        compressed_size_mb = round(compressed_size_bytes / 1024 / 1024, 1)
        compressed_size_str = f"{str(compressed_size_mb)} MB"

        if compressed_size_bytes >= target_size_bytes:
            self.failure_icon.set_from_icon_name('arrow2-up-symbolic')
            # TRANSLATORS: the {} represents the file size.
            fail_msg = _('Compressed file size was too large ({})').format(
                compressed_size_str
            )
            self.failure_details_label.set_label(fail_msg)
        else:
            self.failure_icon.set_from_icon_name('arrow2-down-symbolic')
            # TRANSLATORS: the {} represents the file size.
            fail_msg = _('Compressed file size was too small ({})').format(
                compressed_size_str
            )
            self.failure_details_label.set_label(fail_msg)
