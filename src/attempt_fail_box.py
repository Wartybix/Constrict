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
from constrict import PREFIX
from typing import Optional


@Gtk.Template(resource_path=f'{PREFIX}/attempt_fail_box.ui')
class AttemptFailBox(Gtk.Box):
    """ A box showing details of a compression attempt failure, shown in the
    compression details popover
    """
    __gtype_name__ = "AttemptFailBox"

    attempt_label = Gtk.Template.Child()
    target_label = Gtk.Template.Child()
    failure_icon = Gtk.Template.Child()
    failure_details_label = Gtk.Template.Child()

    def __init__(
        self,
        attempt_no: int,
        vid_bitrate: int,
        is_hq_audio: Optional[bool],
        vid_height: int,
        vid_fps: float,
        compressed_size_bytes: int,
        target_size_bytes: int,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        # TRANSLATORS: {} represents the attempt number.
        self.attempt_label.set_label(_("Attempt {}").format(str(attempt_no)))

        # TRANSLATORS: this is an abbreviation of 'High Quality'
        hq_label = _('HQ')

        # TRANSLATORS: this is an abbreviation of 'Low Quality'
        lq_label = _('LQ')

        res_fps = f'{vid_height}p@{int(round(vid_fps, 0))}'

        if is_hq_audio is None:
            extra_details = res_fps
        else:
            # TRANSLATORS:
            # {res_fps} represents a resolution + framerate (e.g. '1080p@30').
            # {audio_quality} represents audio quality (i.e. 'HQ' or 'LQ').
            extra_details = _("{res_fps}, {audio_quality} audio").format(
                res_fps = res_fps,
                audio_quality = hq_label if is_hq_audio else lq_label
            )


        # TRANSLATORS: {vid_br} represents an integer.
        # {vid_br_unit} represents a bitrate unit, like 'kbps'.
        # {extra_details} will either display resolution/FPS and audio quality
        # details, or just resolution/FPS if the video has no audio streams.
        # Please use U+202F Narrow no-break space (' ') between video bitrate
        # and unit.
        target_str = _("{vid_br} {vid_br_unit} ({extra_details})").format(
            vid_br = f'{str(vid_bitrate // 1000)}',
            vid_br_unit = 'kbps',
            extra_details = extra_details
        )
        self.target_label.set_label(target_str)

        compressed_size_mb = round(compressed_size_bytes / 1024 / 1024, 1)

        if compressed_size_bytes >= target_size_bytes:
            self.failure_icon.set_from_icon_name('arrow2-up-symbolic')
            # TRANSLATORS: {size} represents an integer. {unit} represents a
            # file size unit like 'MB'. Please use U+202F Narrow no-break space
            # (' ') between size and unit.
            fail_msg = _('Compressed file size was too large ({size} {unit})').format(
                size = f'{compressed_size_mb}',
                unit = 'MiB'
            )
            self.failure_details_label.set_label(fail_msg)
        else:
            self.failure_icon.set_from_icon_name('arrow2-down-symbolic')
            # TRANSLATORS: {size} represents an integer. {unit} represents a
            # file size unit like 'MB'. Please use U+202F Narrow no-break space
            # (' ') between size and unit.
            fail_msg = _('Compressed file size was too small ({size} {unit})').format(
                size = f'{compressed_size_mb}',
                unit = 'MiB'
            )
            self.failure_details_label.set_label(fail_msg)
