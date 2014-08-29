Colored Logcat
==============

A python script which outputs logcat messages in color.

This script was originally written by [Jeff Sharkey](http://jsharkey.org/blog/) and can be found [here](http://jsharkey.org/downloads/coloredlogcat.pytxt).

I changed the code substantially in order to support multiple logcat output formats. The color codes roughly correspond
to the usual output (warning = yellow, error = red, ...) now.

![example screenshot](./example.png "Colored Logcat")

Usage
=====

`coloredlogcat.py` behaves like plain `adb logcat`:

```
$> coloredlogcat.py

$> coloredlogcat.py -v time
```

Or reads from stdin:

```
$> cat logfile.log | coloredlogcat.py

$> adb logcat -v time | grep --line-buffered  `adb shell ps | grep com.android.chrome | cut -c 10-15` | coloredlogcat.py
```
