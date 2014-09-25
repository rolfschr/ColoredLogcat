#!/usr/bin/python

'''
    Copyright 2009, The Android Open Source Project

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
'''

# script to highlight adb logcat output for console
# written by jeff sharkey, http://jsharkey.org/
# piping detection and popen() added by other android team members
# multiple logcat format support added by rolf schroder


import os
import sys
import re
import StringIO
import fcntl
import termios
import struct

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
LIGHT_BACKGROUND = 0
if LIGHT_BACKGROUND:
    WHITE = BLACK
TAG_WIDTH = 20
TAGTYPE2COLOR = {
    "V": WHITE,
    "D": BLUE,
    "I": GREEN,
    "W": YELLOW,
    "E": RED,
}
KNOWN_TAG_COLOR = CYAN
KNOWN_TAGS = ["dalvikvm", "Process", "ActivityManager", "ActivityThread"]


def format(fg=None, bg=None, bright=False, bold=False, dim=False, reset=False):
    # manually derived from http://en.wikipedia.org/wiki/ANSI_escape_code#Codes
    codes = []
    if reset:
        codes.append("0")
    else:
        if fg is not None:
            codes.append("3%d" % (fg))
        if bg is not None:
            if not bright:
                codes.append("4%d" % (bg))
            else:
                codes.append("10%d" % (bg))
        if bold:
            codes.append("1")
        elif dim:
            codes.append("2")
        else:
            codes.append("22")
    return "\033[%sm" % (";".join(codes))


def indent_wrap(message, indent=0, width=80):
    wrap_area = width - indent
    messagebuf = StringIO.StringIO()
    current = 0
    while current < len(message):
        next = min(current + wrap_area, len(message))
        messagebuf.write(message[current:next])
        if next < len(message):
            messagebuf.write("\n%s" % (" " * indent))
        current = next
    return messagebuf.getvalue()


def tagtype2color(tagtype):
    return TAGTYPE2COLOR[tagtype]


def tag2color(tag):
    if (tag in KNOWN_TAGS):
        return KNOWN_TAG_COLOR
    return None

if __name__ == '__main__':
    # unpack the current terminal width/height
    data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, '1234')
    HEIGHT, WIDTH = struct.unpack('hh', data)

    # 08-29 11:32:28.839 D/dalvikvm( 7497): GC_CONCURRENT freed 1976K, 73% ...
    re_time = re.compile('^(\d*-\d* \d*:\d*:\d*\.\d*):? '
                         '([A-Z])/(.*)\(\s*(\d*)\): (.*)$')

    # D/dalvikvm( 7497): GC_CONCURRENT freed 1976K, 73% free 3084K/11380K, ...
    re_brief = re.compile("^([A-Z])/(.*)\(\s*(\d*)\): (.*)$")

    # 08-29 13:35:56.819  1052  1052 D StatusBar.NetworkController: mDataCo...
    re_threadtime = re.compile('^(\d*-\d* \d*:\d*:\d*\.\d*)\s*(\d*)\s*(\d*) '
                               '([A-Z]) (.*): (.*)$')

    # E 09-25 15:16:59.777 xxxxxxxxxxxxxxxxx170(22811): yyyyyyyyyyyy...
    re_self = re.compile('^([A-Z]) (\d*-\d* \d*:\d*:\d*\.\d*) '
                         '(.*)\(\s*(\d*)\): (.*)$')

    adb_args = ' '.join(sys.argv[1:])

    # if someone is piping in to us, use stdin as input. else invoke adb logcat
    if os.isatty(sys.stdin.fileno()):
        input = os.popen("adb logcat %s" % adb_args)
    else:
        input = sys.stdin

    while True:
        try:
            line = input.readline()
        except KeyboardInterrupt:
            break

        header_size = 2 + TAG_WIDTH + 8 + 1
        mbrief = re_brief.match(line)
        mtime = re_time.match(line)
        mthreadtime = re_threadtime.match(line)
        mself = re_self.match(line)
        if mbrief:
            tagtype, tag, pid, message = mbrief.groups()
            timestamp = None
        elif mtime:
            timestamp, tagtype, tag, pid, message = mtime.groups()
        elif mthreadtime:
            timestamp, pid, _, tagtype, tag, message = mthreadtime.groups()
        elif mself:
            tagtype, timestamp, tag, pid, message = mself.groups()
        elif len(line) == 0:
            break
        else:
            continue

        linebuf = StringIO.StringIO()
        color = tag2color(tag)
        if not color:
            color = tagtype2color(tagtype)
        linebuf.write(format(fg=color))
        linebuf.write("%s " % tagtype)

        if timestamp is not None:
            header_size += len(timestamp) + 1
            linebuf.write("%s " % timestamp)

        # right-align tag title and allocate color if needed
        tag = tag.strip()
        tag = tag[-TAG_WIDTH:].rjust(TAG_WIDTH)
        pid = pid.rjust(5)
        linebuf.write("%s(%s): " % (tag, pid))

        # insert line wrapping as needed
        message = indent_wrap(message, header_size, WIDTH)
        linebuf.write("%s" % message)

        linebuf.write(format(reset=True))
        line = linebuf.getvalue()

        print(line)
