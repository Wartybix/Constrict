# current_attempt_box.py
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
from gettext import ngettext

@Gtk.Template(resource_path=f'{PREFIX}/current_attempt_box.ui')
class CurrentAttemptBox(Gtk.Box):
    __gtype_name__ = "CurrentAttemptBox"

    progress_bar = Gtk.Template.Child()
    attempt_label = Gtk.Template.Child()
    target_details_label = Gtk.Template.Child()
    progress_details_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # TRANSLATORS: {} represents the attempt number.
        self.attempt_label.set_label(_('Attempt {}').format('1'))

    def set_progress_text(self, label, daemon):
        update_ui(self.progress_details_label.set_text, label, daemon)

    def get_progress_text(self):
        return self.progress_bar.get_text()

    def pulse_progress(self, daemon):
        update_ui(self.progress_bar.pulse, None, False)

    def set_attempt_details(
        self,
        attempt_no,
        vid_bitrate,
        is_hq_audio,
        vid_height,
        vid_fps,
        daemon
    ):
        # TRANSLATORS: {} represents the attempt number.
        attempt_no_label = _('Attempt {}').format(str(attempt_no))
        update_ui(self.attempt_label.set_label, attempt_no_label, daemon)

        # TRANSLATORS: this is an abbreviation of 'High Quality'
        hq_label = _('HQ')

        # TRANSLATORS: this is an abbreviation of 'Low Quality'
        lq_label = _('LQ')

        # TRANSLATORS: {vid_br} represents a bitrate value.
        # {res_fps} represents a resolution + framerate (e.g. '1080p@30').
        # {audio_quality} represents audio quality (i.e. 'HQ' or 'LQ')
        target_details_label = _('Compressing to {vid_br} ({res_fps}, {audio_quality} audio)').format(
            vid_br = f'{vid_bitrate // 1000} Kbps',
            res_fps = f'{vid_height}p@{vid_fps}',
            audio_quality = hq_label if is_hq_audio else lq_label
        )
        update_ui(
            self.target_details_label.set_label,
            target_details_label,
            daemon
        )

    def set_progress(self, fraction, seconds_left, daemon):
        update_ui(self.progress_bar.set_fraction, fraction, daemon)

        progress_percent = int(round(fraction * 100, 0))
        progress_text = ''

        # TODO: add hours + minutes

        if seconds_left is not None:
            time_left = seconds_left
            unit_label = ngettext('second', 'seconds', time_left)

            if time_left >= 60:
                time_left = time_left // 60
                unit_label = ngettext('minute', 'minutes', time_left)

            if time_left >= 60:
                time_left = time_left // 60
                unit_label = ngettext('hour', 'hours', time_left)


            # TRANSLATORS: {percent} represents the progress percentage value.
            # {time} represents an integer.
            # {unit} represents a unit of time (e.g. 'second/seconds').
            # Please use U+202F Narrow no-break space (' ') between {percent}
            # and '%'.
            # Please use U+2014 em dash ('—'), if applicable to your language.
            progress_text = _('{percent} % — About {time} {unit} left').format(
                percent = progress_percent,
                time = time_left,
                unit = unit_label
            )
        else:
            progress_text = f'{progress_percent} %'

        update_ui(self.progress_details_label.set_label, progress_text, daemon)
