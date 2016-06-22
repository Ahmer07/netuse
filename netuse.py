#!/usr/bin/python3

"""
Calculate internet usage from log files created
by a custom script, and display statistics.
"""

import sys
import os

# Used for calculating suggested internet usage
from datetime import date, timedelta

# Load settings from config file
# See file 'config.py.example' for what the settings mean.
from config import (
    START_DATE,
    DAYS_IN_MONTH,
    TOTAL_DATA,
    EPOCH_DIFF,
    CORRECTION_FACTOR,
    LOGFILES_PATH,
)

# How many bytes in an MB?
MB = 1024 * 1024

# Ideally, these values shouldn't be globals but passed around to functions!
s_day, s_month, s_year = map(int, START_DATE.split("/"))

# not (Explicit is better than implicit)
join = os.path.join


def gen_file_list():
    """Generate a list of 'monthly' files to read in."""

    down_filelist = []
    up_filelist = []

    start_date = date(s_year, s_month, s_day)
    end_date = date.today()

    for din in daterange(start_date, end_date):
        down_path = join(LOGFILES_PATH, str(din.year), din.strftime('%b'), "down")
        up_path = join(LOGFILES_PATH, str(din.year), din.strftime('%b'), "up")

        day = "%02d" % din.day

        # Skip when day doesn't exist
        if not os.path.isfile(join(down_path, day)):
            continue

        down_filelist.append(join(down_path, day))
        up_filelist.append(join(up_path, day))

    return down_filelist, up_filelist


def read_files(files):
    """Read files and generate tuples of (data, epoch)."""

    tuples = []

    for _file in files:
        with open(_file) as f:
            tuples.extend([tuple(map(to_int, s.split(";")))
                           for s in f.readlines()])

    return tuples


def calculate(tuples):
    """Calculate actual data usage from the list of tuples."""

    total = 0
    previous = tuples[0]

    for current in tuples[1:]:

        # Some of the data has no epoch entries
        # only byte usage for that day
        if len(current) == 1:
            total += current[0]
            continue

        usage = current[0] - previous[0]
        duration = current[1] - previous[1]

        if duration <= EPOCH_DIFF and usage >= 0:
            total += usage
        else:
            total += current[0]

        previous = current

    return total


def month():
    """ Print stats for the current month. """

    down_filelist, up_filelist = gen_file_list()

    total_download = calculate(read_files(down_filelist)) // MB
    total_download += correction(total_download)

    total_upload = calculate(read_files(up_filelist)) // MB

    data_left = TOTAL_DATA - total_download - total_upload

    start_date = date(s_year, s_month, s_day)
    end_date = start_date + timedelta(days=DAYS_IN_MONTH)
    days_left = (end_date - date.today()).days

    suggested = data_left // days_left

    output = [
        "Downloaded:\t%4d MB" % total_download,
        "Uploaded:\t%4d MB\n" % total_upload,
        "Data Left:\t%4d MB" % data_left,
        # "Days Left:\t%4d Days" % days_left,
        "End Date:\t%s (11:59 PM)\n" % end_date,
        "Suggested:\t%4d MB (Per Day)" % suggested,
    ]

    print("\n".join(output))


def daily(t=date.today()):
    """Print stats for a single day, default today."""

    # Path of day's file
    path = join(LOGFILES_PATH, t.strftime('%G'), t.strftime('%b'), "%s", t.strftime('%d'))

    download = calculate(read_files([path % "down"])) // MB
    upload = calculate(read_files([path % "up"])) // MB

    output = (
        "Downloaded:\t%4d MB \n"
        "Uploaded:\t%4d MB \n"
    ) % (download, upload)

    print(output)


################################################################# Helper functions

def to_int(s):
    """Convert string to integer, empty string is zero."""
    if s.strip() and s.strip('\0'):
        return int(s)
    else:
        return 0


def daterange(start_date, end_date):
    """Iterate over a range of dates. Both ends inclusive."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def correction(n):
    """
    For reasons I can't comprehend, the results are wrong.

    My results differ significantly from what MTS shows me.

    The correction factor, if it exists, will depend on, the
    total data that has been downloaded till now.

    This is a really crude hack - I have no idea what I am doing.
    """
    return n * CORRECTION_FACTOR


# If I am being called directly (rather than being imported)
if __name__ == '__main__':

    # FIXME: Replace this with something 'real' like docopt/click
    if '-t' in sys.argv:
        daily()
    else:
        month()
