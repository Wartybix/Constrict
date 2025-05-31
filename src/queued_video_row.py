from gi.repository import Adw, Gtk, Gio, GLib
from pathlib import Path
from constrict.shared import get_tmp_dir
from constrict.constrict_utils import get_encode_settings, get_resolution, get_framerate, get_duration
from constrict.enums import QueuedVideoState
import threading
import subprocess

# FIXME: video row won't remove with multi windows
# TODO: refactor name to VideoSourceRow

@Gtk.Template(resource_path='/com/github/wartybix/Constrict/queued_video_row.ui')
class QueuedVideoRow(Adw.ActionRow):
    __gtype_name__ = 'QueuedVideoRow'

    thumbnail = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    status_label = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()

    # TODO: investigate window becoming blank?
    # TODO: input validation against adding corrupt videos
    # TODO: check for source video file being updated/removed post-queue?

    def __init__(
        self,
        video_path,
        display_name,
        file_hash,
        target_size_getter,
        fps_mode_getter,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.video_path = video_path
        self.display_name = display_name

        self.height = None
        self.width = None
        self.fps = None
        self.duration = None
        self.state = QueuedVideoState.PENDING

        self.set_title(display_name)

        self.install_action('row.move-up', None, self.move_up)
        self.install_action('row.move-down', None, self.move_down)

        # TODO: add catch for thumbnailer, use video mimetype icon as fallback

        # set thumbnail
        thumb_thread = threading.Thread(
            target=self.set_thumbnail,
            args=[file_hash]
        )
        thumb_thread.daemon = True
        thumb_thread.start()

        preview_thread = threading.Thread(
            target=self.set_preview,
            args=[target_size_getter, fps_mode_getter]
        )
        preview_thread.daemon = True
        preview_thread.start()

    def get_resolution(self):
        if not self.width or not self.height:
            self.width, self.height = get_resolution(self.video_path)

        return (self.width, self.height)

    def get_fps(self):
        if not self.fps:
            self.fps = get_framerate(self.video_path)

        return self.fps

    def get_duration(self):
        if not self.duration:
            self.duration = get_duration(self.video_path)

        return self.duration

    # TODO: make this work with non-flatpak

    def set_thumbnail(self, file_hash):
        # TODO: add check for Totem. If not installed, use video-x-generic.

        tmp_dir = get_tmp_dir()

        print(f'temp dir: {tmp_dir}')

        if not tmp_dir:
            self.thumbnail.set_from_icon_name('video-x-generic')
            return

        thumb_file = str(tmp_dir / f'{file_hash}.jpg')

        print(thumb_file)

        subprocess.run([
            'totem-video-thumbnailer',
            self.video_path,
            thumb_file
        ])
        self.thumbnail.set_from_file(thumb_file)

    def set_preview(self, target_size_getter, fps_mode_getter):
        width, height = self.get_resolution()
        fps = self.get_fps()
        duration = self.get_duration()

        target_size = target_size_getter()
        fps_mode = fps_mode_getter()

        encode_settings = get_encode_settings(
            target_size,
            fps_mode,
            width,
            height,
            fps,
            duration
        )

        if not encode_settings:
            return

        _, _, target_pixels, target_fps = encode_settings

        src_pixels = self.height if self.height < self.width else self.width

        src_label = f'{src_pixels}p@{self.fps}'
        dest_label = f'{target_pixels}p@{target_fps}'

        subtitle = f'{dest_label} ← {src_label}' if (
            self.get_direction() == Gtk.TextDirection.RTL
        ) else f'{src_label} → {dest_label}'



        self.set_subtitle(subtitle)

    def set_state(self, state):
        # If new state and old state are the same:
        if state == self.state:
            return

        is_compressing = state == QueuedVideoState.COMPRESSING
        is_complete = state == QueuedVideoState.COMPLETE

        if is_compressing:
            self.progress_bar.set_fraction(0.0)

        self.progress_bar.set_visible(is_compressing)
        self.status_label.set_visible(is_complete)
        self.action_set_enabled('row.remove', not is_compressing)

        self.state = state

    def set_progress_text(self, label):
        self.progress_bar.set_text(label)

    def get_progress_text(self):
        return self.progress_bar.get_text()

    def pulse_progress(self):
        self.progress_bar.pulse()

    def set_progress_fraction(self, fraction):
        self.progress_bar.set_fraction(fraction)

    def move_up(self, *args):
        print('moved up')
        list_box = self.get_parent()
        prev_index = self.get_index() - 1
        prev_row = list_box.get_row_at_index(prev_index)

        if not prev_row:
            return

    def move_down(self, *args):
        print('moved down')
