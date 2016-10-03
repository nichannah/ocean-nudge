#!/usr/bin/env python

from __future__ import print_function

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


def sort_by_date(forcing_files):
    """
    Sort list in increasing order of date.
    """

    files_with_dates = []
    for filename in forcing_files:
        with nc.Dataset(filename) as f:
            if f.variables.has_key('time_counter'):
                first_time = f.variables['time_counter'][0]
            else:
                first_time = f.variables['time'][0]

            files_with_dates.append((filename, first_time))

    files_with_dates.sort(key=lambda x : x[1])

    return [f for f, _ in files_with_dates]


class DaySeries:
    """
    A list of days and a start date / origin.
    """

    def __init__(self, files):

        files = sort_by_date(files)

        self.origin = self._get_time_origin(files[0])
        self.days = []

        for filename in files:
            with nc.Dataset(filename) as f:
                if f.variables.has_key('time_counter'):
                    time_var = f.variables['time_counter']
                else:
                    time_var = f.variables['time']

                self.days.extend(time_var[:])

    def _get_time_origin(self, filename):
        """
        Parse time.units to find the start/origin date of the file. Return a
        datetime.date object.
        """

        with nc.Dataset(filename) as f:
            if f.variables.has_key('time_counter'):
                time_var = f.variables['time_counter']
            else:
                time_var = f.variables['time']

            assert('days since' in time_var.units)
            m = re.search('\d{4}-\d{2}-\d{2}', time_var.units)
            assert(m is not None)
            date = dt.datetime.strptime(m.group(0), '%Y-%m-%d')

        return dt.date(date.year, date.month, date.day)

    def normalise_to_year_start(self):
        """
        """

        date = self.origin + dt.timedelta(self.days[0])
        first_day = date.day

        return self.days - self.days[0] + first_day
