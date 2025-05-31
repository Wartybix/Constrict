from gi.repository import Adw, Gtk

@Gtk.Template(resource_path='/com/github/wartybix/Constrict/video_sources_list_box.ui')
class VideoSourcesListBox(Gtk.ListBox):
    __gtype_name__ = "VideoSourcesListBox"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_source(self, video_source_row):
        self.append(video_source_row)
