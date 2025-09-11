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
from typing import Any

@Gtk.Template(resource_path=f'{PREFIX}/current_attempt_box.ui')
class CurrentAttemptBox(Gtk.Box):
    """ A box showing the details of a currently running compression, shown in
    a compression details popover.
    """
    __gtype_name__ = "CurrentAttemptBox"

    progress_bar = Gtk.Template.Child()
    attempt_label = Gtk.Template.Child()
    target_details_label = Gtk.Template.Child()
    progress_details_label = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # TRANSLATORS: {} represents the attempt number.
        self.attempt_label.set_label(_('Attempt {}').format('1'))

    def set_progress_text(self, label: str, daemon: bool) -> None:
        """ Sets the text above the progress bar to the string passed """
        update_ui(self.progress_details_label.set_text, label, daemon)

    def pulse_progress(self, daemon: bool) -> None:
        """ Pulse the progress bar in activity mode """
        update_ui(self.progress_bar.pulse, None, False)

    def set_attempt_details(
        self,
        attempt_no: int,
        vid_bitrate: int,
        is_hq_audio: bool,
        vid_height: int,
        vid_fps: float,
        daemon: bool
    ) -> None:
        """ Set the text above the progress bar based on details of a
        compression attempt.
        """

        # TRANSLATORS: {} represents the attempt number.
        attempt_no_label = _('Attempt {}').format(str(attempt_no))
        update_ui(self.attempt_label.set_label, attempt_no_label, daemon)

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
        target_str = _('Compressing to {vid_br} {vid_br_unit} ({extra_details})').format(
            vid_br = f'{vid_bitrate // 1000}',
            # TRANSLATORS: This is the SI unit for 'kilobits per second'.
            vid_br_unit = _('kbps'),
            extra_details = extra_details
        )
        update_ui(
            self.target_details_label.set_label,
            target_str,
            daemon
        )

    def set_progress(
        self,
        fraction: float,
        seconds_left: int,
        daemon: bool
    ) -> None:
        """ Set details of current progress and estimated time left """
        update_ui(self.progress_bar.set_fraction, fraction, daemon)

        progress_percent = int(round(fraction * 100, 0))
        progress_text = ''

        # Acknowledgements: thank you to Nautilus for the ideas on where to set
        # different thresholds for which time unit(s) to display. Particularly
        # the 4 hour mark where minutes should no longer be displayed.
        # https://gitlab.gnome.org/GNOME/nautilus/-/blob/af7e419eaa7e167ecbc059d51e06e72e11a2f1c8/src/nautilus-file-operations.c

        # TRANSLATORS: {} represents the progress percentage value.
        # Please use U+202F Narrow no-break space (' ') between {} and %, if
        # applicable to your language.
        percentage_text = _('{} %').format(progress_percent)

        if seconds_left is None:
            progress_text = percentage_text
        elif seconds_left == -1:
            # TRANSLATORS: {} represents the progress percentage.
            # Please use U+2014 em dash ('—'), if applicable to your language.
            progress_text = _('{} — Almost done').format(percentage_text)
        else:
            time_shown = ''

            if seconds_left < 60:
                # TRANSLATORS: {} represents an integer.
                # Used as part of a larger string, like:
                # '5% -- About 30 seconds left'
                time_shown = ngettext('{} second', '{} seconds', seconds_left).format(seconds_left)
                # time_shown.format(seconds_left)
            elif seconds_left < (60 * 60):
                minutes = seconds_left // 60

                # TRANSLATORS: {} represents an integer.
                # Used as part of a larger string, like:
                # '10% -- About 30 minutes left'
                time_shown = ngettext('{} minute', '{} minutes', minutes).format(minutes)
            elif seconds_left < (60 * 60 * 4):
                hours = seconds_left // (60 * 60)
                minutes = (seconds_left // 60) % 60

                # TRANSLATORS: {} represents an integer. Used as part of a
                # larger string, like:
                # '10% -- About 2 hours, 30 minutes left'
                hours_shown = ngettext('{} hour', '{} hours', hours).format(hours)

                # TRANSLATORS: {} represents an integer. Used as part of a
                # larger string, like:
                # '10% -- About 2 hours, 30 minutes left'
                minutes_shown = ngettext('{} minute', '{} minutes', minutes).format(minutes)

                time_shown = f'{hours_shown}, {minutes_shown}'
            else:
                hours = seconds_left // (60 * 60)

                # TRANSLATORS: {} represents an integer. Used as part of a
                # larger string, like:
                # '10% -- About 2 hours, 30 minutes left'
                time_shown = ngettext('{} hour', '{} hours', hours).format(hours)


            # TRANSLATORS: {percentage} represents the progress percentage.
            # {time_shown} represents a string showing the estimated time to
            # completion (like '50 minutes').
            # Please use U+2014 em dash ('—'), if applicable to your language.
            progress_text = _('{percentage} — About {time_shown} left').format(
                percentage = percentage_text,
                time_shown = time_shown
            )

        update_ui(self.progress_details_label.set_label, progress_text, daemon)
