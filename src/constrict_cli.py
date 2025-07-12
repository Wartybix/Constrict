#!/usr/bin/python3

# constrict_cli.py
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

import argparse
from constrict_utils import compress
from enums import FpsMode, VideoCodec
import datetime

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser("constrict-cli")
    arg_parser.add_argument(
        '-i',
        dest='file_path',
        help='Location of the video file to be compressed',
        type=str
    )
    arg_parser.add_argument(
        '-s',
        dest='target_size',
        help='Desired size of the compressed video in MB',
        type=int
    )
    arg_parser.add_argument(
        '-t',
        dest='tolerance',
        type=int,
        default=10,
        help='Tolerance of end file size under target in percent (default 10)'
    )
    arg_parser.add_argument(
        '-o',
        dest='output',
        type=str,
        help='Destination path of the compressed video file'
    )
    arg_parser.add_argument(
        '--framerate',
        dest='framerate_option',
        choices=['auto', 'prefer-clear', 'prefer-smooth'],
        default='auto',
        help=(
            'The maximum framerate to apply to the output file. NOTE: this '
            'option has no bearing on source videos at 30 FPS or below, and '
            'the output will be the same regardless of the option set. '
            'Additionally, videos compressed to very low bitrates will have '
            'their framerate capped to 24 FPS regardless of the option '
            'set.\n\n'
            'auto: auto-apply a 60 FPS maximum framerate in cases where the '
            'percieved reduction in image clarity from 30 FPS is '
            'negligable.\n\n'
            'prefer-clear: apply a 30 FPS framerate cap, ensuring higher '
            'image clarity in fewer frames.\n\n'
            'prefer-smooth: apply a 60 FPS framerate cap, ensuring smoothness '
            'at a cost to image clarity and sometimes resolution'
        )
    )
    arg_parser.add_argument(
        '--extra-quality',
        action='store_true',
        help='Increase image quality at the cost of much longer encoding times'
    )
    arg_parser.add_argument(
        '--codec',
        dest='codec',
        choices=['h264', 'hevc', 'av1', 'vp9'],
        default='h264',
        help=(
            'The codec used to encode the compressed video.\n'
            'h264: uses the H.264 codec. Compatible with most devices and '
            'services, but with relatively low compression efficiency.\n'
            'hevc: uses the H.265 (HEVC) codec. Less compatible with devices '
            'and services, and is slower to encode, but has higher '
            'compression efficiency.\n'
            'av1: uses the AV1 codec. High compression efficiency, and is '
            'open source and royalty free. However, it is less widely '
            'supported, and may not embed properly on some services.\n'
            'vp9: uses the VP9 codec.'
        )
    )
    args = arg_parser.parse_args()

    def get_fps_mode():
        match args.framerate_option:
            case 'auto':
                return FpsMode.AUTO
            case 'prefer-clear':
                return FpsMode.PREFER_CLEAR
            case 'prefer-smooth':
                return FpsMode.PREFER_SMOOTH

    def get_video_codec():
        match args.codec:
            case 'h264':
                return VideoCodec.H264
            case 'hevc':
                return VideoCodec.HEVC
            case 'av1':
                return VideoCodec.AV1
            case 'vp9':
                return VideoCodec.VP9

    start_time = datetime.datetime.now().replace(microsecond=0)

    def print_progress(fraction, seconds_left):
        if seconds_left is None:
            seconds_left = 0
        mins = seconds_left // 60
        seconds = seconds_left % 60
        hours = mins // 60
        mins = mins % 60

        time_str = f'{hours}:{mins}:{seconds}'

        percent = int(round(fraction * 100, 0))

        print(f'{percent}% -- ~{time_str} left')

        time_now = datetime.datetime.now().replace(microsecond=0) - start_time
        print(f'time spent: {time_now}s')

    def show_attempt_details(
        attempt,
        vid_bitrate,
        audio_bitrate,
        height,
        fps
    ):
        print(f'Attempt {attempt} -- {vid_bitrate // 1000}Kbps ({height}p@{fps}, {audio_bitrate // 1000}Kbps audio)')

    def show_attempt_fail(
        attempt,
        vid_bitrate,
        audio_bitrate,
        height,
        fps,
        after_size_bytes,
        target_size_bytes
    ):
        print(f'Attempt fail: compressed size is {after_size_bytes / 1024 // 1024}MB')

    file_output, final_size, error = compress(
        args.file_path,
        args.output,
        args.target_size,
        get_fps_mode(),
        args.extra_quality,
        get_video_codec(),
        args.tolerance,
        print_progress,
        None,
        lambda: False,
        show_attempt_details,
        show_attempt_fail
    )

    if error:
        print('*** COMPRESSION ERROR ***')
        print(error)
