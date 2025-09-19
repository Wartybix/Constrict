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

from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject
from constrict.constrict_utils import compress
from constrict.shared import get_tmp_dir, update_ui
from constrict.enums import FpsMode, VideoCodec, SourceState
from constrict.sources_row import SourcesRow
from constrict.sources_list_box import SourcesListBox
from constrict.error_dialog import ErrorDialog
from constrict.current_attempt_box import CurrentAttemptBox
from constrict import PREFIX
import threading
import subprocess
from pathlib import Path
import os
from typing import Any, List

# TODO: future feature -- add pause button?


@Gtk.Template(resource_path=f'{PREFIX}/window.ui')
class ConstrictWindow(Adw.ApplicationWindow):
    """A window for the application."""
    __gtype_name__ = 'ConstrictWindow'

    split_view = Gtk.Template.Child()
    view_stack = Gtk.Template.Child()
    export_bar = Gtk.Template.Child()
    export_button = Gtk.Template.Child()
    cancel_bar = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()
    sources_list_box = Gtk.Template.Child()
    target_size_row = Gtk.Template.Child()
    target_size_input = Gtk.Template.Child()
    auto_row = Gtk.Template.Child()
    auto_check_button = Gtk.Template.Child()
    clear_row = Gtk.Template.Child()
    clear_check_button = Gtk.Template.Child()
    smooth_row = Gtk.Template.Child()
    smooth_check_button = Gtk.Template.Child()
    codec_dropdown = Gtk.Template.Child()
    extra_quality_toggle = Gtk.Template.Child()
    tolerance_row = Gtk.Template.Child()
    tolerance_input = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    warning_banner = Gtk.Template.Child()
    main_view_title = Gtk.Template.Child()
    adv_options_help_label = Gtk.Template.Child()
    adv_options_help_popover = Gtk.Template.Child()
    fps_help_label = Gtk.Template.Child()
    fps_help_popover = Gtk.Template.Child()
    window_breakpoint = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.compressing = False
        self.currently_processed = ''
        self.main_view_title.set_title(self.get_title())

        self.toggle_sidebar_action = Gio.SimpleAction(name="toggle-sidebar")
        self.toggle_sidebar_action.connect("activate", self.toggle_sidebar)
        self.toggle_sidebar_action.set_enabled(False)
        self.add_action(self.toggle_sidebar_action)

        self.window_breakpoint.add_setter(
            self.toggle_sidebar_action,
            "enabled",
            True
        )

        self.open_action = Gio.SimpleAction(name="open")
        self.open_action.connect("activate", self.open_file_dialog)
        self.add_action(self.open_action)

        self.export_action = Gio.SimpleAction(name="export")
        self.export_action.connect("activate", self.export_file_dialog)
        self.export_action.set_enabled(bool(self.sources_list_box.any()))
        self.add_action(self.export_action)

        self.cancel_action = Gio.SimpleAction(name="cancel")
        self.cancel_action.connect("activate", self.on_cancel)
        self.add_action(self.cancel_action)

        self.clear_all_action = Gio.SimpleAction(name="clear_all")
        self.clear_all_action.connect("activate", self.delist_all)
        self.add_action(self.clear_all_action)

        self.close_action = Gio.SimpleAction(name="close")
        self.close_action.connect("activate", lambda *_: self.close())
        self.add_action(self.close_action)

        self.target_size_input.connect("value-changed", self.refresh_previews)
        self.auto_check_button.connect("toggled", self.refresh_previews)
        self.clear_check_button.connect("toggled", self.refresh_previews)
        self.smooth_check_button.connect("toggled", self.refresh_previews)

        self.codec_dropdown.connect("notify::selected", self.refresh_previews)
        self.extra_quality_toggle.connect(
            "notify::active",
            self.refresh_previews
        )
        self.tolerance_input.connect("value-changed", self.refresh_previews)

        self.fps_help_popover.connect("show", self.read_fps_popover)
        self.adv_options_help_popover.connect(
            "show",
            self.read_adv_options_popover
        )

        self.settings = self.get_application().get_settings()
        self.settings.bind(
            'window-width',
            self,
            'default-width',
            Gio.SettingsBindFlags.GET | Gio.SettingsBindFlags.GET_NO_CHANGES
        )
        self.settings.bind(
            'window-height',
            self,
            'default-height',
            Gio.SettingsBindFlags.GET | Gio.SettingsBindFlags.GET_NO_CHANGES
        )
        self.settings.bind(
            'window-maximized',
            self,
            'maximized',
            Gio.SettingsBindFlags.GET | Gio.SettingsBindFlags.GET_NO_CHANGES
        )
        self.settings.bind(
            'target-size',
            self.target_size_input,
            'value',
            Gio.SettingsBindFlags.GET | Gio.SettingsBindFlags.GET_NO_CHANGES
        )
        self.settings.bind(
            'extra-quality',
            self.extra_quality_toggle,
            'active',
            Gio.SettingsBindFlags.GET | Gio.SettingsBindFlags.GET_NO_CHANGES
        )
        self.settings.bind(
            'tolerance',
            self.tolerance_input,
            'value',
            Gio.SettingsBindFlags.GET | Gio.SettingsBindFlags.GET_NO_CHANGES
        )

        fps_mode = self.settings.get_enum('fps-mode')
        video_codec = self.settings.get_enum('video-codec')

        self.set_fps_mode(fps_mode)
        self.set_video_codec(video_codec)

        content = Gdk.ContentFormats.new_for_gtype(Gdk.FileList)
        target = Gtk.DropTarget(formats=content, actions=Gdk.DragAction.COPY)
        target.connect('drop', self.on_drop)
        target.connect('enter', self.on_enter)

        self.view_stack.add_controller(target)

        # TRANSLATORS: 'FPS' meaning 'frames per second'.
        # {} represents the FPS value, for example 30 or 60.
        # Please use U+202F Narrow no-break space (' ') between value and unit.
        fps_label = _('{} FPS')

        self.clear_row.set_title(fps_label.format('_30'))
        self.smooth_row.set_title(fps_label.format('_60'))

        self.fps_help_label.set_label(
            # TRANSLATORS: FPS meaning 'frames per second'. {} represents an
            # integer. Please use U+202F narrow no-break space (' ') between
            # the {} and translated equivalent of 'FPS'.
            _('Videos compressed to low bitrates may be capped to {} FPS, regardless of the option set.')
                .format('24')
        )

        default_tolerance = self.settings.get_default_value('tolerance')

        self.adv_options_help_label.set_label(
            # TRANSLATORS: {} represents an integer. Please use U+202F Narrow
            # no-break space (' ') between {} and '%'.
            _('Decreasing the tolerance maximizes image quality by reducing how much compressed file sizes can be under target. However, this can increase the number of attempts needed to meet the target, increasing compression time. A tolerance of {} % or more is recommended.')
                .format(default_tolerance)
        )

        # TRANSLATORS: this is the SI unit for 'mebibyte'.
        unit = _('MiB')

        # TRANSLATORS: {} represents a file size unit (e.g. 'MiB')
        self.target_size_row.set_title(_('Target _Size ({})').format(unit))

    def read_fps_popover(self, widget: Gtk.Widget, *args: Any):
        """ Use the screen reader to announce the contents of the
        'FPS limit help' popover.
        """
        message = self.fps_help_label.get_text()

        self.announce(message, Gtk.AccessibleAnnouncementPriority.MEDIUM)

    def read_adv_options_popover(self, widget: Gtk.Widget, *args: Any):
        """ Use the screen reader to announce the contents of the
        'advanced options help' popover.
        """
        message = self.adv_options_help_label.get_text()

        self.announce(message, Gtk.AccessibleAnnouncementPriority.MEDIUM)

    def on_drop(
        self,
        drop_target: Gtk.DropTarget,
        value: Gdk.FileList,
        x: int,
        y: int,
        user_data: Any = None
    ) -> None:
        """ Stage video files that have been dragged and dropped onto the
        window
        """
        files: List[Gio.File] = value.get_files()

        self.stage_videos(files)

    def on_enter(
        self,
        drop_target: Gtk.DropTarget,
        x: int,
        y: int
    ) -> int:
        # Custom code...
        # Tell the callee to continue
        return Gdk.DragAction.COPY

    def set_controls_lock(self, is_locked: bool, daemon: bool) -> None:
        """ Set whether to make most of the window's controls like compression
        settings and source video management interactable or not """
        update_ui(self.target_size_row.set_sensitive, not is_locked, daemon)
        update_ui(self.auto_row.set_sensitive, not is_locked, daemon)
        update_ui(self.clear_row.set_sensitive, not is_locked, daemon)
        update_ui(self.smooth_row.set_sensitive, not is_locked, daemon)
        update_ui(self.codec_dropdown.set_sensitive, not is_locked, daemon)
        update_ui(
            self.extra_quality_toggle.set_sensitive,
            not is_locked,
            daemon
        )
        update_ui(self.tolerance_row.set_sensitive, not is_locked, daemon)

        update_ui(self.clear_all_action.set_enabled, not is_locked, daemon)
        self.clear_all_action.set_enabled(not is_locked)
        self.open_action.set_enabled(not is_locked)
        self.export_action.set_enabled(not is_locked)

        self.sources_list_box.set_locked(is_locked, daemon)

    def is_unchecked_checkbox(self, widget: Gtk.Widget) -> bool:
        """ Return whether the passed widget is an unchecked GtkCheckButton """
        return type(widget) is Gtk.CheckButton and not widget.get_active()

    def set_warning_state(self, is_error: bool, daemon: bool) -> None:
        """ Set whether to put the window in a warning state, disabling export
        and showing a banner communicating this.
        """
        update_ui(self.export_action.set_enabled, not is_error, daemon)
        update_ui(self.warning_banner.set_revealed, is_error, daemon)

        if is_error:
            message = self.warning_banner.get_title()
            self.announce(message, Gtk.AccessibleAnnouncementPriority.MEDIUM)

    def refresh_can_export(self, daemon: bool) -> None:
        """ Set whether the export action is enabled or not based on the states
        of the video sources
        """
        sources = self.sources_list_box.get_all()

        if not sources:
            update_ui(self.export_action.set_enabled, False, daemon)
            update_ui(self.warning_banner.set_revealed, False, daemon)
            update_ui(
                self.view_stack.set_visible_child_name,
                'status_page',
                daemon
            )
            return

        complete_count = 0

        for video in sources:
            if video.state in [SourceState.BROKEN, SourceState.INCOMPATIBLE]:
                self.set_warning_state(True, daemon)
                return
            elif video.state == SourceState.COMPLETE:
                complete_count += 1

        self.set_warning_state(False, daemon)

        if complete_count == len(sources):
            update_ui(self.export_action.set_enabled, False, daemon)

    def set_compressing_title(self, current_index: int, export_dir: str):
        """ Set the text in the window's title bar when compression is taking
        place
        """
        sources = self.sources_list_box.get_all()

        if len(sources) == 1:
            file_name = sources[0].display_name
            # TRANSLATORS: {} represents the filename of the video currently
            # being processed. Please use “” instead of "", if applicable to
            # your language.
            self.set_title(_('Processing “{}”').format(file_name))
        else:
            self.set_title(
                # TRANSLATORS: {index} represents the index of the video
                # currently being processed. {total} represents the total
                # number of videos being processed.
                _('{index}/{total} Videos Processed').format(
                    index = current_index,
                    total = len(sources)
                )
            )

        self.main_view_title.set_title(self.get_title())
        self.main_view_title.set_subtitle(
            # TRANSLATORS: {} represents the path of the directory being
            # exported to. Please use “” instead of "", if applicable to your
            # language.
            _('Exporting to “{}”').format(export_dir)
        )

    def set_queued_title(self, daemon: bool) -> None:
        """ Set the text in the window's title bar when no compression is
        taking place.
        """
        sources = self.sources_list_box.get_all()

        if len(sources) == 0:
            self.set_title(_('Constrict'))
        elif len(sources) == 1:
            vid_name = sources[0].display_name
            # TRANSLATORS: {} represents the filename of the video currently
            # queued. Please use “” instead of '', if applicable to your
            # language.
            self.set_title(_('“{}” Queued').format(vid_name))
        else:
            vid_count = len(sources)
            # TRANSLATORS: {} represents the number of files queued.
            self.set_title(_('{} Videos Queued').format(vid_count))

        update_ui(self.main_view_title.set_title, self.get_title(), daemon)
        update_ui(self.main_view_title.set_subtitle, '', daemon)

    def refresh_previews(self, widget: Gtk.Widget, *args: Any) -> None:
        """ Refresh the previews of all source rows in the sources list box.
        Disable the export action if there are any errors with the sources
        (for example, broken or incompatible videos).
        """

        # Return if called from a check button being 'unchecked'
        if self.is_unchecked_checkbox(widget):
            return

        sources = self.sources_list_box.get_all()

        for video in sources:
            video.set_preview(self.get_target_size, self.get_fps_mode, False)

        self.refresh_can_export(False)
        self.withdraw_complete_notification()

    def get_target_size(self) -> int:
        """ Get the target size set in the window's compression settings """
        return int(self.target_size_input.get_value())

    def get_fps_mode(self) -> int:
        """ Get the framerate limit set in the windows's compression settings
        """
        if self.auto_check_button.get_active():
            return FpsMode.AUTO
        if self.clear_check_button.get_active():
            return FpsMode.PREFER_CLEAR
        if self.smooth_check_button.get_active():
            return FpsMode.PREFER_SMOOTH

        raise Exception('Tried to get fps mode, but none was set.')

    def set_fps_mode(self, mode: int) -> None:
        """ Set the framerate limit in the window's compression settings """
        match mode:
            case FpsMode.AUTO:
                self.auto_check_button.set_active(True)
            case FpsMode.PREFER_CLEAR:
                self.clear_check_button.set_active(True)
            case FpsMode.PREFER_SMOOTH:
                self.smooth_check_button.set_active(True)
            case _:
                self.auto_check_button.set_active(True)

    def get_video_codec(self) -> int:
        """ Get the video codec set in the windows's compression settings """
        return self.codec_dropdown.get_selected()

    def set_video_codec(self, codec_index: int) -> None:
        """ Set the video codec in the windows's compression settings """
        self.codec_dropdown.set_selected(codec_index)

    def get_extra_quality(self) -> bool:
        """ Get the 'extra quality' mode set in the window's compression
        settings
        """
        return self.extra_quality_toggle.get_active()

    def get_tolerance(self) -> int:
        """ Get the tolerance value set in the window's compression settings
        """
        return int(self.tolerance_input.get_value())

    def toggle_sidebar(self, action: Gio.Action, _) -> None:
        """ Toggle whether the compression settings sidebar is shown """
        sidebar_shown = self.split_view.get_show_sidebar()
        self.split_view.set_show_sidebar(not sidebar_shown)

    def delist_all(self, action: Gio.Action, _) -> None:
        """ Remove all source rows from the window's source list box. Disable
        the export function and refresh the window title
        """
        self.sources_list_box.remove_all()
        self.refresh_can_export(False)
        self.set_queued_title(False)

    def show_cancel_button(self, is_compressing: bool, daemon: bool) -> None:
        """ Change whether to show the 'cancel' button or the 'export' button
        in the window
        """
        update_ui(self.cancel_bar.set_visible, is_compressing, daemon)
        update_ui(self.export_bar.set_visible, not is_compressing, daemon)

    def export_file_dialog(self, action: Gio.Action, parameter: GLib.Variant) -> None:
        """ Show a file chooser for the folder to export videos to """
        native = Gtk.FileDialog()

        initial_folder_path = self.settings.get_string('export-initial-folder')

        if initial_folder_path:
            initial_folder = Gio.File.new_for_path(initial_folder_path)
            native.set_initial_folder(initial_folder)

        native.select_folder(self, None, self.on_export_response)

    def on_export_response(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult
    ) -> None:
        """ Start compressing videos in a new thread, exporting to the folder
        path passed """
        folder = dialog.select_folder_finish(result)

        if not folder:
            return

        folder_path = folder.get_path()
        self.settings.set_string('export-initial-folder', folder_path)

        thread = threading.Thread(
            target=self.bulk_compress,
            args=[folder_path, True]
        )
        thread.daemon = True
        thread.start()

    def on_cancel(self, action: Gio.Action, parameter: GLib.Variant) -> None:
        """ Show the window's cancel dialog """
        self.show_cancel_dialog(False)

    def show_cancel_dialog(self, quit_on_stop: bool) -> None:
        """ Display a cancel dialog to stop the current compression """
        dialog = Adw.AlertDialog.new(
            _('Stop Compression?'),
            # TRANSLATORS: {} represents the filename of the video currently
            # being compressed. Please use “” instead of "", if applicable to
            # your language.
            _('Progress made compressing “{}” will be permanently lost')
                .format(self.currently_processed)
        )

        dialog.quit_on_stop = quit_on_stop

        dialog.add_response('cancel', _('_Cancel'))
        dialog.add_response('stop', _('_Stop'))

        dialog.set_response_appearance(
            'stop',
            Adw.ResponseAppearance.DESTRUCTIVE
        )

        dialog.choose(self, None, self.on_cancel_response)

    def on_cancel_response(
        self,
        dialog: Adw.AlertDialog,
        result: Gio.AsyncResult
    ) -> None:
        """ Act on a cancel dialog's response """
        choice = dialog.choose_finish(result)

        if choice == 'stop':
            self.compressing = False
            if dialog.quit_on_stop:
                self.close()

    def error_dialog(self, file_name: str, error_details: str) -> None:
        """ Show an error dialog for a video's compression error """
        dialog = ErrorDialog(file_name, error_details)

        dialog.present(self)

    def show_error_from_toast(self, toast: Adw.Toast) -> None:
        """ Show an error dialog from clicking a toast's "Show Error Details"
         button
         """
        self.error_dialog(toast.video.display_name, toast.video.error_details)

    def get_complete_notification_id(self) -> str:
        """ Get a unique notification ID for communicating compression is
        complete, for this window
        """
        return f'compress-complete-{self.get_id()}'

    def withdraw_complete_notification(self) -> None:
        """ Withdraw a 'compression complete' notification for this window """
        notification_id = self.get_complete_notification_id()
        self.get_application().withdraw_notification(notification_id)

    def send_complete_notification(
        self,
        sources_list: List[SourcesRow],
        export_dir: str
    ) -> None:
        """ Send a notification communicating that compression is complete to
        the user's desktop environment. Include a button to open the export
        directory of the compressed videos.
        """
        notification = Gio.Notification.new(_('Compression Complete'))
        notification.set_category('transfer.complete')

        if len(sources_list) == 1:
            video_name = sources_list[0].display_name
            # TRANSLATORS: {} represents the filename of the video that has
            # been processed.
            # Please use “” instead of "", if applicable to your language.
            notification.set_body(_('“{}” processed').format(video_name))
        else:
            notification.set_body(
                # TRANSLATORS: {} represents the number of files that have been
                # processed.
                _('{} files processed').format(len(sources_list))
            )

        window_id_gvariant = GLib.Variant.new_int32(self.get_id())
        notification.set_default_action_and_target(
            'app.focus-window',
            window_id_gvariant
        )

        export_string_gvariant = GLib.Variant.new_string(export_dir)
        notification.add_button_with_target(
            _('Open Export Directory'),
            'app.open-dir',
            export_string_gvariant
        )

        self.get_application().send_notification(
            self.get_complete_notification_id(),
            notification
        )

    def get_unique_path(self, file_path: str) -> str:
        """
        Returns a unique file path for the file path given. Ensures that no
        file is overwritten, as if the input file path already exists, the file
        path output will be in the form of '{file_root}-{n}{file_ext}' where n
        incremented with every existing file in the directory.

        Do not use if you *want* to overwrite something.
        """

        final_path = file_path
        root_ext = os.path.splitext(file_path)

        counter = 0
        while os.path.exists(final_path):
            counter += 1
            final_path = f'{root_ext[0]}-{counter}{root_ext[1]}'

        return final_path

    def bulk_compress(self, destination_dir: str, daemon: bool) -> None:
        """ Compress all videos in the sources list box, exporting to the
        passed destination directory
        """
        self.set_controls_lock(True, daemon)
        self.show_cancel_button(True, daemon)
        self.compressing = True

        target_size = self.get_target_size()
        fps_mode = self.get_fps_mode()
        codec = self.get_video_codec()
        extra_quality = self.get_extra_quality()
        tolerance = self.get_tolerance()

        dest_file = Gio.File.new_for_path(destination_dir)
        dest_info = dest_file.query_info(
            'standard::display-name',
            Gio.FileQueryInfoFlags.NONE,
            None
        )
        dest_display_name = dest_info.get_display_name()

        source_list = self.sources_list_box.get_all()

        inhibit_cookie = self.get_application().inhibit(
            self,
            Gtk.ApplicationInhibitFlags.SUSPEND | Gtk.ApplicationInhibitFlags.LOGOUT,
            _('Videos are being compressed')
        )

        for i in range(len(source_list)):
            self.set_compressing_title(i, dest_display_name)

            video = source_list[i]

            if video.state == SourceState.COMPLETE:
                continue

            self.currently_processed = video.display_name

            progress_box = CurrentAttemptBox()
            video.initiate_popover_box(progress_box, daemon)

            use_ha = self.settings.get_boolean('use-gpu-encoding')

            def update_progress(fraction, seconds_left):
                if fraction == 0.0 and codec == VideoCodec.VP9:
                    # TRANSLATORS: please use U+2026 Horizontal ellipsis (…)
                    # instead of '...', if applicable to your language
                    progress_box.set_progress_text(_('Analyzing…'), daemon)
                    video.enable_spinner(True, daemon)
                    progress_box.pulse_progress(daemon)
                else:
                    video.enable_spinner(False, daemon)
                    progress_box.set_progress(fraction, seconds_left, daemon)
                    update_ui(video.progress_pie.set_fraction, fraction, daemon)

            def set_attempt_details(
                attempt,
                target_vid_bitrate,
                hq_audio,
                target_height,
                target_fps
            ):
                progress_box.set_attempt_details(
                    attempt,
                    target_vid_bitrate,
                    hq_audio,
                    target_height,
                    target_fps,
                    daemon
                )

            def add_attempt_fail(
                attempt,
                target_vid_bitrate,
                hq_audio,
                target_height,
                target_fps,
                after_size_bytes,
                target_size_bytes
            ):
                video.add_attempt_fail(
                    attempt,
                    target_vid_bitrate,
                    hq_audio,
                    target_height,
                    target_fps,
                    after_size_bytes,
                    target_size_bytes,
                    daemon
                )

            video.set_state(SourceState.COMPRESSING, daemon)

            tmp_dir = get_tmp_dir()
            log_filename = f'constrict2pass-{self.get_id()}'

            log_path = str(tmp_dir / log_filename) if (
                tmp_dir
            ) else str(Path(destination_dir) / log_filename)

            input_basename = os.path.basename(video.video_path)
            merged = os.path.join(destination_dir, input_basename)
            root_ext = os.path.splitext(merged)

            custom_suffix = self.settings.get_string('custom-export-suffix')
            suffix = custom_suffix or self.get_application().default_suffix

            output_path = f'{root_ext[0]}{suffix}.mp4'
            output_path_unique = self.get_unique_path(output_path)

            compression_result = compress(
                video.video_path,
                video.mime_type,
                output_path_unique,
                target_size,
                fps_mode,
                extra_quality,
                codec,
                use_ha,
                tolerance,
                update_progress,
                log_path,
                lambda: not self.compressing,
                set_attempt_details,
                add_attempt_fail
            )

            def trash_video():
                # Move video to wastebasket. This is a compromise in case the
                # user wants to keep their semi-processed file for any reason.
                # But also doesn't clutter their export folder automatically
                # with junk files.

                output_file = Gio.File.new_for_path(output_path_unique)
                output_file.trash_async(GLib.PRIORITY_LOW, None, None, None)

            if type(compression_result) is str:
                video.set_error(compression_result, daemon)

                toast = Adw.Toast.new(
                    # TRANSLATORS: {} represents the filename of the video with
                    # the error. Please use “” instead of "", if applicable to
                    # your language.
                    _('Error compressing “{}”').format(video.display_name)
                )
                toast.set_use_markup(False)
                toast.set_button_label(_('View _Details'))
                toast.video = video

                toast.connect('button-clicked', self.show_error_from_toast)

                update_ui(self.toast_overlay.add_toast, toast, daemon)

                trash_video()

                continue

            if not self.compressing:
                video.set_state(SourceState.PENDING, daemon)

                trash_video()

                break


            if type(compression_result) is int:
                end_size_bytes = compression_result
                end_size_mb = round(end_size_bytes / 1024 / 1024, 1)
                video.set_complete(output_path_unique, end_size_mb, daemon)

        self.set_controls_lock(False, daemon)
        self.show_cancel_button(False, daemon)
        self.refresh_can_export(daemon)

        if inhibit_cookie != 0:
            self.get_application().uninhibit(inhibit_cookie)

        self.set_queued_title(daemon)

        if not self.compressing:
            toast = Adw.Toast.new(_('Compression Canceled'))
            toast.set_priority(Adw.ToastPriority.HIGH)
            update_ui(self.toast_overlay.add_toast, toast, daemon)
        else:
            toast = Adw.Toast.new(_('Compression Complete'))
            update_ui(self.toast_overlay.add_toast, toast, daemon)

            self.send_complete_notification(source_list, destination_dir)

        self.compressing = False

    def remove_row(self, row: SourcesRow) -> None:
        """ Remove a row from the window's sources list box. Refresh the
        window's title, and whether the export action is enabled
        """
        self.sources_list_box.remove(row)
        self.refresh_can_export(False)
        self.set_queued_title(False)

    def stage_videos(self, video_list: List[Gio.File]) -> None:
        """ Add passed video files to the window's sources list box as
        sources rows.
        """
        existing_paths = list(map(
            lambda x: x.video_path,
            self.sources_list_box.get_all()
        ))

        staged_rows = []

        for video in video_list:
            video_path = video.get_path()

            if video_path in existing_paths:
                continue

            info = video.query_info(
                'standard::display-name,standard::content-type',
                Gio.FileQueryInfoFlags.NONE
            )
            content_type = info.get_content_type()

            if not content_type:
                continue

            is_video = content_type.startswith('video/') or content_type == 'image/gif'

            if not is_video:
                continue

            display_name = info.get_display_name() if info else video.get_basename()

            staged_row = SourcesRow(
                video.get_path(),
                display_name,
                content_type,
                video.hash(),
                self.get_target_size,
                self.get_fps_mode,
                self.error_dialog,
                self.set_warning_state,
                self.remove_row
            )

            staged_rows.append(staged_row)

        self.sources_list_box.add_sources(staged_rows)

        if self.sources_list_box.any():
            self.view_stack.set_visible_child_name('queue_page')
            self.refresh_can_export(False)
            self.export_button.grab_focus()
            self.set_queued_title(False)

    def open_file_dialog(
        self,
        action: Gio.Action,
        parameter: GLib.Variant
    ) -> None:
        """ Show a file dialog to add videos to the window's video sources list
        """

        # Create new file selection dialog, using "open" mode
        native = Gtk.FileDialog()
        video_filter = Gtk.FileFilter()

        video_filter.add_mime_type('video/*')
        video_filter.add_mime_type('image/gif')

        video_filter.set_name(_('Videos'))

        native.set_default_filter(video_filter)
        native.set_title(_('Pick Videos'))

        initial_folder_path = self.settings.get_string('open-initial-folder')

        if initial_folder_path:
            initial_folder = Gio.File.new_for_path(initial_folder_path)
            native.set_initial_folder(initial_folder)

        native.open_multiple(self, None, self.on_open_response)

    def on_open_response(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult
    ) -> None:
        """ Stage the videos passed to the window's video sources list """
        files = dialog.open_multiple_finish(result)

        if not files:
            return

        new_initial_folder_path = files[0].get_parent().get_path()
        self.settings.set_string(
            'open-initial-folder',
            new_initial_folder_path
        )

        self.stage_videos(files)

    def save_window_state(self) -> None:
        """ Write the window's various states and compression settings to the
        application's settings. This is so that new windows can be loaded
        with these same settings.
        """
        self.settings.set_boolean('window-maximized', self.is_maximized())

        width, height = self.get_default_size()
        self.settings.set_int('window-width', width)
        self.settings.set_int('window-height', height)
        self.settings.set_int('target-size', self.get_target_size())
        self.settings.set_enum('fps-mode', self.get_fps_mode())
        self.settings.set_enum('video-codec', self.get_video_codec())
        self.settings.set_boolean('extra-quality', self.get_extra_quality())
        self.settings.set_int('tolerance', self.get_tolerance())

    def do_close_request(self, force: bool = False) -> bool:
        """ Gracefully close the window, showing a cancel dialog if a close
        request was made while compression was taking place
        """
        if self.compressing:
            self.show_cancel_dialog(True)
            return True

        self.withdraw_complete_notification()
        self.save_window_state()

        return False


