#!/bin/sh

# Install Flathub
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# Install ffmpeg-full dependency
flatpak install --user flathub -y runtime/org.freedesktop.Platform.ffmpeg-full/x86_64/24.08

# Build & install
flatpak-builder --force-clean --user --install-deps-from=flathub --install builddir io.github.wartybix.Constrict.Devel.json

# Run
flatpak run io.github.wartybix.Constrict.Devel
