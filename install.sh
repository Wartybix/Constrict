#!/bin/sh

# Install Flathub
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# Build & install
flatpak-builder --force-clean --user --install-deps-from=flathub --repo=repo --install builddir com.github.wartybix.Constrict.json

# Run
flatpak run com.github.wartybix.Constrict
