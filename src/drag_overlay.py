# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2023-2024 Sophie Herold
# SPDX-FileCopyrightText: Copyright 2023 FineFindus
# SPDX-FileCopyrightText: Copyright 2024-2025 kramo
# SPDX-FileCopyrightText: Copyright 2025 Wartybix

# Taken from Showtime, which was taken from Loupe, rewritten in PyGObject
# Updated to Loupe's latest style and modified for Constrict.
# https://gitlab.gnome.org/GNOME/showtime/-/blob/59c8f10d37d0769bcc923334a26a06c21675a5ed/showtime/widgets/drag_overlay.py
# https://gitlab.gnome.org/GNOME/loupe/-/blob/d66dd0f16bf45b3cd46e3a084409513eaa1c9af5/src/widgets/drag_overlay.rs

from typing import Any
from gi.repository import Adw, GObject, Gtk
from constrict import PREFIX

@Gtk.Template(resource_path=f'{PREFIX}/drag_overlay.ui')
class DragOverlay(Adw.Bin):
    """A widget that shows an overlay when dragging a video over the window."""

    __gtype_name__ = "DragOverlay"

    # _drop_target: Gtk.DropTarget | None = None

    drop_target = Gtk.Template.Child()
    overlay = Gtk.Template.Child()
    revealer = Gtk.Template.Child()

    @GObject.Property(type=Gtk.Widget)
    def child(self) -> Gtk.Widget | None:
        """Usual content."""
        return self.overlay.get_child()

    @child.setter
    def child(self, child: Gtk.Widget) -> None:
        self.overlay.set_child(child)

    @GObject.Property(type=Gtk.DropTarget)
    def drop_target(self) -> Gtk.DropTarget | None:
        """Get the drop target."""
        return self._drop_target

    @drop_target.setter
    def drop_target(self, drop_target: Gtk.DropTarget) -> None:
        self._drop_target = drop_target

        if not drop_target:
            return

        drop_target.connect(
            "notify::current-drop",
            lambda *_: self.revealer.set_reveal_child(
                bool(drop_target.props.current_drop)
            ),
        )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.revealer.set_can_target(False)
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        self.revealer.set_reveal_child(False)
