#!/usr/bin/python3

# constrict.py
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

import sys
import subprocess
import os
import argparse
import datetime

# Module responsible for compression logic. This script can be packaged
# on its own to provide a CLI compressor *only*. The GTK wrapper depends on
# this script for its 'business logic' too.


def get_duration(file_input):
    return float(
        subprocess.check_output([
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_input
        ])[:-1]
    )


def new_file(file_path):
    """
    Returns a unique file path for the file path given. Ensures that no file is
    overwritten, as if the input file path already exists, the file path output
    will be in the form of '{file_root}-{n}{file_ext}' where n incremented with
    every existing file in the directory.

    Do not use if you *want* to overwrite something.
    """

    final_path = file_path
    root_ext = os.path.splitext(file_path)

    counter = 0
    while os.path.exists(final_path):
        counter += 1
        final_path = f'{root_ext[0]}-{counter}{root_ext[1]}'

    return final_path


def get_res_preset(bitrate, source_width, source_height, framerate):
    """
    Returns a suitable resolution preset (i.e. 1080p, 720p, etc.) from a given
    bitrate and source resolution. Allows source videos to be shrunk according
    to a new, reduced bitrate for optimal perceived video quality. This
    function should not return a resolution preset larger than the source
    resolution (i.e. an upscaled or stretched resolution).

    -If -1 is returned, then the video's source resolution is recommended.
    """

    source_pixels = source_width * source_height  # Get pixel count
    bitrate_Kbps = bitrate / 1000  # Convert to kilobits
    """
    Bitrate-resolution recommendations are taken from:
    https://developers.google.com/media/vp9/settings/vod
    """
    bitrate_res_map_30 = {
        12000: (3840, 2160),  # 4K
        6000: (2560, 1440),  # 2K
        1800: (1920, 1080),  # 1080p
        1024: (1280, 720),  # 720p
        512: (640, 480),  # 480p
        276: (640, 360),  # 360p
        150: (320, 240),  # 240p
        0: (192, 144)  # 144p
    }
    bitrate_res_map_60 = {
        18000: (3840, 2160),  # 4K
        9000: (2560, 1440),  # 2K
        3000: (1920, 1080),  # 1080p
        1800: (1280, 720),  # 720p
        750: (640, 480),  # 480p
        276: (640, 360),  # 360p
        150: (320, 240),  # 240p
        0: (192, 144)  # 144p
    }

    bitrate_res_map = (
        bitrate_res_map_30 if framerate <= 30 else bitrate_res_map_60
    )

    # print(bitrate_res_map)

    for bitrate_lower_bound, res_preset in bitrate_res_map.items():
        preset_width, preset_height = res_preset[0], res_preset[1]
        preset_pixels = preset_width * preset_height
        if (
            bitrate_Kbps >= bitrate_lower_bound and
            source_pixels >= preset_pixels
        ):
            return preset_height

    return -1


def get_encoding_speed(frame_height, codec, extra_quality):
    hd = frame_height > 480

    match codec:
        case 'h264':
            if extra_quality:
                return 'veryslow'
            else:
                return 'medium' if hd else 'slower'
        case 'hevc':
            if extra_quality:
                return 'veryslow'
            else:
                return 'medium' if hd else 'slow'
        case 'av1':
            if extra_quality:
                return '4'
            else:
                return '10' if hd else '8'

        case _:
            sys.exit('Error: unknown codec passed to get_encoding_speed')


def get_progress(file_input, ffmpeg_cmd):
    #pv_cmd = subprocess.Popen(['pv', file_input], stdout=subprocess.PIPE)
    # ffmpeg_cmd = subprocess.check_output(ffmpeg_cmd, stdin=pv_cmd.stdout)
    # pv_cmd.wait()
    # subprocess.run()

    subprocess.run(ffmpeg_cmd)


def transcode(
    file_input,
    file_output,
    video_bitrate,
    audio_bitrate,
    width,
    height,
    framerate,
    codec,
    extra_quality,
):
    portrait = height > width
    frame_height = width if portrait else height

    print(f' frame height: {frame_height}')

    preset = get_encoding_speed(frame_height, codec, extra_quality)

    # TODO: dynamically look for installed encoders?
    # TODO: see if VP9 works in flatpak?

    cv_params = {
        'h264': 'libx264',
        'hevc': 'libx265',
        'av1': 'libsvtav1'
    }

    pass1_cmd = [
        'ffmpeg',
        '-y',
        # '-hide_banner',
        # '-loglevel', 'error',
        '-i', f'{file_input}',
        '-row-mt', '1',
        '-frame-parallel', '1',
        '-preset', f'{preset}',
        # '-deadline', 'good',
        # '-cpu-used', '4',
        # '-threads', '24',
        '-vf', f'scale={width}:{height}',
    ]

    if codec == 'h264':
        pass1_cmd.extend(['-profile:v', 'main'])

    if framerate != -1:
        pass1_cmd.extend(['-r', f'{framerate}'])

    pass1_cmd.extend([
        '-c:v', f'{cv_params[codec]}',
        '-b:v', str(video_bitrate) + '',
        '-pass', '1',
        '-an',
        '-f', 'null',
        '/dev/null'
    ])

    print(" ".join(pass1_cmd))
    print(' Transcoding... (pass 1/2)')
    get_progress(file_input, pass1_cmd)

    audio_channels = 1 if audio_bitrate < 12000 else 2

    pass2_cmd = [
        'ffmpeg',
        '-y',
        # '-hide_banner',
        # '-loglevel', 'error',
        '-i', f'{file_input}',
        '-row-mt', '1',
        '-frame-parallel', '1',
        '-preset', f'{preset}',
        # '-threads', '24',
        # '-deadline', 'good',
        # '-cpu-used', cpuUsed,
        '-vf', f'scale={width}:{height}',
    ]

    if codec == 'h264':
        pass2_cmd.extend(['-profile', 'main'])

    if framerate != -1:
        pass2_cmd.extend(['-r', f'{framerate}'])

    pass2_cmd.extend([
        '-c:v', f'{cv_params[codec]}',
        '-b:v', str(video_bitrate) + '',
        '-pass', '2',
        # '-x265-params', 'pass=1',
        '-c:a', 'libopus',
        '-b:a', f'{audio_bitrate}',
        '-ac', f'{audio_channels}',
        file_output
    ])
    print(" ".join(pass2_cmd))
    print(' Transcoding... (pass 2/2)')
    get_progress(file_input, pass2_cmd)


def get_framerate(file_input):
    cmd = [
        'ffprobe',
        '-v', '0',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        '-select_streams', 'v:0',
        '-show_entries',
        'stream=r_frame_rate',
        file_input
    ]
    fps_bytes = subprocess.check_output(cmd)
    fps_fraction = fps_bytes.decode('utf-8')
    fps_fraction_split = fps_fraction.split('/')
    fps_numerator = int(fps_fraction_split[0])
    fps_denominator = int(fps_fraction_split[1])
    fps_float = round(fps_numerator / fps_denominator)
    return fps_float


def get_resolution(file_input):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=s=x:p=0',
        file_input
    ]

    res_bytes = subprocess.check_output(cmd)
    res = res_bytes.decode('utf-8')
    res_array = res.split('x')
    width = int(res_array[0])
    height = int(res_array[1])

    return (width, height)


def get_rotation(file_input):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream_side_data=rotation',
        '-of', 'csv=s=x:p=0',
        file_input
    ]

    rotation_bytes = subprocess.check_output(cmd)
    rotation = rotation_bytes.decode('utf-8')

    try:
        rotation = int(rotation)
    except ValueError:
        rotation = 0

    return rotation


def bold(text):
    return f'\033[1m{text}\033[0m'


def heading(text):
    return f':: {bold(text)}'


def table(data):
    max_key_len = 0
    max_value_len = 0

    for row in data:
        row[0] += ':'

        if len(row[0]) > max_key_len:
            max_key_len

        max_key_len = (
            len(row[0]) if len(row[0]) > max_key_len else max_key_len
        )
        max_value_len = (
            len(row[1]) if len(row[1]) > max_value_len else max_value_len
        )

    msg = ""

    for row in data:
        spaces_to_add = max_key_len - len(row[0])
        for i in range(spaces_to_add):
            row[0] += ' '

        spaces_to_add = max_value_len - len(row[1])
        for i in range(spaces_to_add):
            row[1] = ' ' + row[1]

        msg += f' {row[0]}  {row[1]}'

    return msg


def preview(input_file, target_size_MiB, fps_mode):
    # TODO: this is very inefficient... use some kind of caching and whatnot
    # to not fetch/calculate resolution, framerate, bitrate etc. more than
    # once. Lots of redundant code with compress function.

    src_width, src_height = get_resolution(input_file)
    src_fps = get_framerate(input_file)

    target_size_KiB = target_size_MiB * 1024
    target_size_bytes = target_size_KiB * 1024
    target_size_bits = target_size_bytes * 8
    duration_seconds = get_duration(input_file)

    target_bitrate = round(target_size_bits / duration_seconds)

    crush_mode = (target_bitrate / 1000) < 150 + 96
    target_audio_bitrate = 6000 if crush_mode else 96000
    target_video_bitrate = target_bitrate - target_audio_bitrate

    # To account for metadata and such to prevent overshooting
    target_video_bitrate = round(target_video_bitrate * 0.99)

    if target_video_bitrate < 1000:
        return 'Video bitrate too low'

    preset_height = None
    max_fps = None

    if crush_mode:
        max_fps = 24
    elif fps_mode == 'prefer-clear':
        max_fps = 30
    elif fps_mode == 'prefer-smooth':
        max_fps = 60
    elif fps_mode == 'auto':
        preset_height_30fps = get_res_preset(
            target_video_bitrate,
            src_width,
            src_height,
            30
        )
        preset_height_60fps = get_res_preset(
            target_video_bitrate,
            src_width,
            src_height,
            60
        )

        preset_height = preset_height_30fps
        heights_match = preset_height_30fps == preset_height_60fps
        max_fps = 60 if heights_match and preset_height >= 720 else 30

    target_fps = src_fps if src_fps <= max_fps else max_fps

    if preset_height is None:
        preset_height = get_res_preset(
            target_video_bitrate,
            src_width,
            src_height,
            target_fps
        )

    if src_height > src_width:
        src_height = src_width

    return f'{src_height}p@{src_fps} → {preset_height}p@{target_fps}'


""" TODO:
check for non-existent files (or non-video files) -- exit 1 with error msg
allow different units for desired file size
add input validation for arguments
add overwrite confirmation and argument
add 'source overwrite' mode: -o value same as input file path
check for when file size doesnt change
add more error checking for very low target file sizes
add support for bulk compression
force container on any file name
add 'general compression' mode - no target file size(?)
reconsider where log and streamable files go (output dir rather than PWD?)
check for output file directory permissions
add verbosity options (GUI and quiet)
don't use streamable temp file with quiet verbosity mode
add overwrite-safe default file outputs (streamable file and compressed file)
Add check when video bitrate calculation goes over original bitrate
change how tolerance works
inhibit suspend while running
get rid of all this unused and commented out code
investigate error messages and performance further
use some kind of maths magic to reduce number of attempts at low file sizes
improve bitrate recalculation, change from simple multiplication (!!)
check calculations for bitrate etc. are correct (i.e. MiB vs MB etc)
add checkers for codecs
clean up ffmpeg 2pass logs after compression
improve text formatting
check framerate text indicator
Fix 'Application provided invalid, non monotonically increasing dts to muxer in stream'
Add speed options (CONSIDER HANDBRAKE PRESETS)
See about 64K audio? and capping audio based on original audio bitrate...
Add preview mode for GUI version
Lower to 16 FPS instead of 24?
add 10 bit support?
Clean up AV1 text output
revisit qt-faststart (doesn't work on fedora)
perhaps check out FFmpeg python libraries? revisit using pv for progress
change output_fn argument to be raw data, not strings (human readable strings
    should be created on the interface side, not in these functions).
change 'pv' command to output to output_fn, not writing directly to the
    terminal.
use a sliding window for repeated compression attempts?
"""

def compress(
    file_input,
    target_size_MiB,
    framerate_option='auto',
    extra_quality=False,
    codec='h264',
    tolerance=10,
    file_output=None,
    output_fn=lambda x: None
):
    start_time = datetime.datetime.now().replace(microsecond=0)

    if file_output is None:  # i.e., if -o hasn't been passed
        root_ext = os.path.splitext(file_input)
        file_output = new_file(f'{root_ext[0]} (compressed).mp4')

    target_size_KiB = target_size_MiB * 1024
    target_size_bytes = target_size_KiB * 1024
    target_size_bits = target_size_bytes * 8
    duration_seconds = get_duration(file_input)

    before_size_bytes = os.stat(file_input).st_size

    if before_size_bytes <= target_size_bytes:
        output_fn("File already meets the target size.")
        return

    reduction_factor = target_size_bytes / before_size_bytes

    target_total_bitrate = round(target_size_bits / duration_seconds)
    source_fps = get_framerate(file_input)
    width, height = get_resolution(file_input)
    # print(f'Resolution: {width}x{height}')
    portrait = (width < height) ^ (get_rotation(file_input) == -90)  # xor gate
    print(f'width heigher than height: {width < height}')
    print(f'rotation = {get_rotation(file_input)}')
    print(f'rotated = {get_rotation(file_input) == -90}')
    print(f'portrait = {portrait}')

    factor = 0
    attempt = 0
    while (factor > 1.0 + (tolerance / 100)) or (factor < 1):
        attempt = attempt + 1
        target_total_bitrate = round((target_total_bitrate) * (factor or 1))
        print(f'target total {target_total_bitrate // 1000}Kbps')

        '''
        crush mode tries to save some image clarity by significantly reducing audio
        quality and introducing a 24 FPS framerate cap. This makes the footage look
        slightly less blurry at 144p, and can sometimes save it from being
        downgraded to 144p as a preset resolution due to the boost in video
        bitrate.

        Why is the threshold 150 + 96 (= 246)? It's the sum of the lowest
        recommended bitrate for 240p (150Kbps), plus a 'good quality' bitrate for
        Opus audio (96Kbps). It means that it shouldn't be possible to 'downgrade'
        the video to 144p without applying crush mode. Additionally, footage can be
        'saved' from being downgraded to 144p where, for example:

        Total target bitrate = 200Kbps
        Bitrate less than threshold, therefore apply crush mode.
        Target audio bitrate set to 6Kbps (rather than 96Kbps) due to crush mode.
        Therefore, video bitrate is 194Kbps
        This is *above* 150Kbps, therefore preset resolution is 240p@24

        And if there was no crush mode:
        Total target bitrate = 200Kbps
        Target audio bitrate set to 96Kbps
        Therefore, video bitrate is 104Kbps
        This is *below* 150Kbps, therefore preset resolution is 144p@?
        '''
        crush_mode = (target_total_bitrate / 1000) < 150 + 96
        target_audio_bitrate = 6000 if crush_mode else 96000
        target_video_bitrate = target_total_bitrate - target_audio_bitrate

        # To account for metadata and such to prevent overshooting
        target_video_bitrate = round(target_video_bitrate * 0.99)

        if (target_video_bitrate < 1000):
            output_fn("Video bitrate got too low (<1kbps); aborting")
            return

        target_height = height
        target_width = width

        preset_height = None
        max_fps = None

        if crush_mode:
            print('max fps set to 24')
            max_fps = 24
        elif framerate_option == 'prefer-clear' or source_fps <= 30:
            print('max fps set to 30')
            max_fps = 30
        elif framerate_option == 'prefer-smooth':
            print('max fps set to 60')
            max_fps = 60
        elif framerate_option == 'auto':
            print('auto fps mode...')
            preset_height_30fps = get_res_preset(
                target_video_bitrate,
                width,
                height,
                30
            )
            preset_height_60fps = get_res_preset(
                target_video_bitrate,
                width,
                height,
                60
            )

            preset_height = preset_height_30fps
            heights_match = preset_height_30fps == preset_height_60fps
            max_fps = 60 if heights_match and preset_height >= 720 else 30

        keep_fps = source_fps <= max_fps  # Don't 'increase' FPS from source
        target_fps = source_fps if source_fps <= max_fps else max_fps

        if preset_height is None:
            preset_height = get_res_preset(
                target_video_bitrate,
                width,
                height,
                target_fps
            )

        print(f'Target height {preset_height}')

        if preset_height != -1:  # If being downscaled:
            target_height = preset_height
            scaling_factor = height / target_height
            target_width = int(((width / scaling_factor + 1) // 2) * 2)

            if portrait:
                # Swap height and width
                buffer = target_width
                target_width = target_height
                target_height = buffer

        displayed_res = target_width if portrait else target_height

        output_fn('')
        output_fn(heading((
            f'(Attempt {attempt}) '
            f'compressing to {target_video_bitrate // 1000}Kbps / '
            f'{displayed_res}p@{target_fps}...'
        )))

        transcode(
            file_input,
            file_output,
            target_video_bitrate,
            target_audio_bitrate,
            target_width,
            target_height,
            -1 if keep_fps else target_fps,
            codec,
            extra_quality,
        )
        after_size_bytes = os.stat(file_output).st_size
        percent_of_target = (100 / target_size_bytes) * after_size_bytes

        factor = 100 / percent_of_target

        if (percent_of_target > 100):
            # Prevent a lot of attempts resulting in above-target sizes
            factor -= 0.05
            #  print(f'Reducing factor by 5%')

        output_fn('')
        output_fn(table([
            ['New Size', f"{'{:.2f}'.format(after_size_bytes/1024/1024)}MB"],
            ['Percentage of Target', f"{'{:.0f}'.format(percent_of_target)}%"]
        ]))

    time_taken = datetime.datetime.now().replace(microsecond=0) - start_time
    output_fn(f"\nCompleted in {time_taken}.")

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser("constrict")
    arg_parser.add_argument(
        'file_path',
        help='Location of the video file to be compressed',
        type=str
    )
    arg_parser.add_argument(
        'target_size',
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
        choices=['h264', 'hevc', 'av1'],
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
            'supported, and may not embed properly on some services.'
        )
    )
    args = arg_parser.parse_args()

    compress(
        args.file_path,
        args.target_size,
        args.framerate_option,
        args.extra_quality,
        args.codec,
        args.tolerance,
        args.output,
        lambda x: print(x)
    )
