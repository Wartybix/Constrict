#!/usr/bin/python3

# enums.py
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

class FpsMode:
    AUTO = 0
    PREFER_CLEAR = 1
    PREFER_SMOOTH = 2


class VideoCodec:
    H264 = 0
    HEVC = 1
    AV1 = 2
    VP9 = 3


class SourceState:
    PENDING = 0
    COMPRESSING = 1
    COMPLETE = 2
    ERROR = 3
    BROKEN = 4
    INCOMPATIBLE = 5
    WARN = 6

