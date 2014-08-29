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


import os, sys, re, StringIO
import fcntl, termios, struct

# unpack the current terminal width/height
data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, '1234')
HEIGHT, WIDTH = struct.unpack('hh',data)

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

TAG_WIDTH = 20
#D 08-29 11:58:36.739 ar.NetworkController( 1052): 
HEADER_SIZE = 2 + TAG_WIDTH + 8 + 1

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
	if reset: codes.append("0")
	else:
		if not fg is None: codes.append("3%d" % (fg))
		if not bg is None:
			if not bright: codes.append("4%d" % (bg))
			else: codes.append("10%d" % (bg))
		if bold: codes.append("1")
		elif dim: codes.append("2")
		else: codes.append("22")
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

def format_tagtype(tagtype):
	return "%s%s%s" % (format(fg=tagtype2color(tagtype)), tagtype, format(reset=True))



re_tag = re.compile("^(.*?)([A-Z])/([^\(]+)\(([^\)]+)\): (.*)$")
re_meta = re.compile("^(\d*-\d* \d*:\d*:\d*\.\d*)(.*?)$")

adb_args = ' '.join(sys.argv[1:])

# if someone is piping in to us, use stdin as input.  if not, invoke adb logcat
if os.isatty(sys.stdin.fileno()):
	input = os.popen("adb %s logcat" % adb_args)
else:
	input = sys.stdin

while True:
	try:
		line = input.readline()
	except KeyboardInterrupt:
		break

	timestamp = None
	match = re_tag.match(line)
	cur_header_size = HEADER_SIZE
	if not match is None:
		meta, tagtype, tag, owner, message = match.groups()
		metamatch = re_meta.match(meta)
		if (metamatch):
			timestamp, _ = metamatch.groups()

		linebuf = StringIO.StringIO()
		color = tag2color(tag)
		if (color == None):
			color = tagtype2color(tagtype)
		linebuf.write(format(fg=color))
		linebuf.write("%s " % tagtype)
		if (timestamp):
			cur_header_size += len(timestamp) + 1
			linebuf.write("%s " % timestamp)


		# right-align tag title and allocate color if needed
		tag = tag.strip()
		tag = tag[-TAG_WIDTH:].rjust(TAG_WIDTH)
		linebuf.write("%s(%s): " % (tag, owner))

		# insert line wrapping as needed
		message = indent_wrap(message, cur_header_size, WIDTH)
		linebuf.write("%s" % message)

		linebuf.write(format(reset=True))
		line = linebuf.getvalue()

	print line
	if len(line) == 0: break












