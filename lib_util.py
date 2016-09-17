#!/usr/bin/env python

from __future__ import print_function

import tempfile
import shlex
import shutil
import subprocess as sp

def compress_netcdf_file(filename, compression_level=1):
    """
    Use nccopy to compress a netcdf file.
    """

    _, tmp = tempfile.mkstemp()

    cmd = 'nccopy -d {} {} {}'.format(compression_level, filename, tmp)
    print(cmd)
    ret = sp.call(shlex.split(cmd))
    assert(ret == 0)

    shutil.move(tmp, filename)
