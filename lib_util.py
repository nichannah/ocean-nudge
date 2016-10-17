#!/usr/bin/env python

from __future__ import print_function

import numpy as np
import tempfile
import shlex
import shutil
import subprocess as sp
import re
import datetime as dt
import netCDF4 as nc

def compress_netcdf_file(filename, compression_level=7):
    """
    Use nccopy to compress a netcdf file.
    """

    _, tmp = tempfile.mkstemp()

    cmd = 'nccopy -d {} {} {}'.format(compression_level, filename, tmp)
    print(cmd)
    ret = sp.call(shlex.split(cmd))
    assert(ret == 0)

    shutil.move(tmp, filename)

def get_time_origin(filename):
    """
    Parse time.units to find the start/origin date of the file. Return a
    datetime.date object.
    """

    with nc.Dataset(filename) as f:
        if f.variables.has_key('time_counter'):
            time_var = f.variables['time_counter']
        else:
            time_var = f.variables['time']

        assert 'days since' in time_var.units or \
            'hours since' in time_var.units
        m = re.search('\d{4}-\d{2}-\d{2}', time_var.units)
        assert(m is not None)
        date = dt.datetime.strptime(m.group(0), '%Y-%m-%d')

    return dt.date(date.year, date.month, date.day)


def sort_by_date(forcing_files):
    """
    Sort list in increasing order of date.
    """

    files_with_dates = []
    for filename in forcing_files:
        first_time = get_time_origin(filename)
        files_with_dates.append((filename, first_time))

    files_with_dates.sort(key=lambda x : x[1])

    return [f for f, _ in files_with_dates]


class DaySeries:
    """
    Pull days from files and arrange in an increasing sequence. Each day in the
    sequence is the number of days (or hours) since the start date. By default
    the start date (or origin) is the start date of the earlies file.
    """

    def __init__(self, files):

        files = sort_by_date(files)

        # The origin is the origin of the first file.
        self.origin = get_time_origin(files[0])
        self.days = []

        for filename in files:
            with nc.Dataset(filename) as f:
                f_origin = get_time_origin(filename)

                if f.variables.has_key('time_counter'):
                    time_var = f.variables['time_counter']
                else:
                    time_var = f.variables['time']


                assert 'days since' in time_var.units or \
                    'hours since' in time_var.units
                if 'days since' in time_var.units:
                    days = time_var[:]
                else:
                    days = int(time_var[:] / 24.0)

                # Days variable is relative to f_origin, we need to adjust so
                # that it is relative to self.origin
                base_delta = f_origin - self.origin
                assert base_delta >= dt.timedelta(0)

                self.days.extend(days + base_delta.days)

        assert np.all(np.diff(self.days) > 1), \
                'Error: One or more dates and/or input files are repeated.'
