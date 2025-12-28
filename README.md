
<!-- Nice layout taken from Drum Machine: https://github.com/Revisto/drum-machine/blob/a87023afcf9733c56b6689246b1cf9d001d19b0b/README.md -->

<div align="center">
  <img src="/data/icons/hicolor/scalable/apps/io.github.wartybix.Constrict.svg" width="128" height="128">

  # Constrict

  **Compress videos to target sizes**

  [![GNOME Circle](https://circle.gnome.org/assets/button/badge.svg)](https://apps.gnome.org/Constrict/) 
  [![Please do not theme this app](https://stopthemingmy.app/badge.svg)](https://stopthemingmy.app)

  <img src="screenshots/queued.png" alt="A screenshot of the application">
</div>

## About

Constrict compresses your videos to your chosen file size — useful for uploading to services with specific file size limits. No more relying on online services for video compression, or the manual trial-and-error of re-encoding at various bitrates yourself.

Features include:

- An intuitive, easy to use interface.
- Automatic calculation of average bitrate (ABR), resolution, framerate, and audio quality each video is re-encoded with to meet the target file size.
- Bulk compression of multiple videos to one output directory.
- Customization of framerate limits, to ensure a clearer or smoother image.
- A choice of codecs to encode output files with, including H.264, HEVC, AV1, and VP9.

The app attempts to retain as much audiovisual quality as possible for the file size given. However, extremely steep reductions in file size can cause significant loss of quality in the output file, and sometimes compression may not be possible at all. All processing is done locally — and as such, compression speeds are only as fast as your hardware allows.

## Install
Constrict is officially published as a Flatpak, via Flathub. Please ensure you are using an up-to-date version of this Flatpak when filing any new bug reports.

<a href='https://flathub.org/apps/org.gimp.GIMP'>
  <img width='240' alt='Get it on Flathub' src='https://flathub.org/api/badge?locale=en'/>
</a>

## Contributing
If you are new to contibuting to open-source projects, or projects in the GNOME ecosystem, this [contribution guide](https://welcome.gnome.org/app/Constrict/) for Constrict might be helpful to you.

This page will tell you how to file new issues efficiently, test pre-release versions of the app, as well as how to submit translations and code contributions.

## Code of Conduct
This project follows [GNOME's Code of Conduct](https://conduct.gnome.org/).

## Acknowledgements
Thanks to Matthew Baggett for creating the original ['8mb' repository](https://github.com/matthewbaggett/8mb) which this project used as its foundation.
