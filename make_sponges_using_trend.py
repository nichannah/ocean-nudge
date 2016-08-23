#!/usr/bin/env python

import sys
import shutil
import argparse
import numpy as np
import multiprocessing as mp
import netCDF4 as nc

sys.path.append('../analyse/')
from lib_util import create_output_file_from_mom_base, compress_netcdf_file

"""
Make sponge damping coefficient and restoring fields using existing ocean
fields and a trend. The purpose is to be able to restore an ocean field to
follow a trend. As such it's necessary to do two model runs: the first will
establish the base and the second will relax to the base + trend.

This script does two things to make sponge files:
    1) Add a trend to an existing ocean field and output the result. This is
    the restoring field.
    2) Create the damping coefficient file based on the trend, i.e. the damping
    coefficient is zero everywhere where the trend is zero.

The output can be several years in length.

Example use:

./make_sponges_using_trend.py ocean.nc --annual_trend SSTTrend_1992to2011_mom_grid.nc temp -d 1e-08

Output:

temp_sponge_coeff.nc
temp_sponge.nc

Assumptions:

- The trend file is in deg C / year.
- The base files are monthly means.

"""

def make_restoring_field(base_files, trend_file, variable):
    """
    Make the restoring field by adding an annual trend to a base variable.

    We need to make a single sponge file that covers our whole time period. So
    combine a collection of base files adding the trend to each.

    We also return the combined files without the trend added.

    Assumptions: the base files are monthly and the trend file is annual.
    FIXME: test these assumptions.
    """

    output_file = '{}_sponge.nc'.format(variable)
    vars = ['yt_ocean', 'xt_ocean', 'st_ocean', 'time', variable]
    create_output_file_from_mom_base(base_files[0], vars, output_file)

    no_trend_output_file = '{}_sponge_no_trend.nc'.format(variable)
    create_output_file_from_mom_base(base_files[0], vars, no_trend_output_file)

    with nc.Dataset(trend_file) as tf:
        trend = tf.variables[variable][0, :, :, :] / 12.0

    of = nc.Dataset(output_file, 'r+')
    nt_of = nc.Dataset(no_trend_output_file, 'r+')

    month_idx = 0

    for base in base_files:
        with nc.Dataset(base, 'r') as bf:
            time_var = bf.variables['time']
            for t in range(time_var.shape[0]):

                # Make no trend variable - just a copy.
                tmp_var = np.copy(bf.variables[variable][t, :, :, :])
                # Convert to degrees C, used internally by the model.
                if variable == 'temp' and 'degrees K' \
                    in bf.variables[variable].units:
                    tmp_var -= 273.15
                # Put in 0's where possible so that the file compresses well.
                tmp_var[np.where(trend == 0)] = 0.0

                nt_of.variables[variable][month_idx, :, :, :] = tmp_var[:]
                # Copy over the time
                nt_of.variables['time'][month_idx] = bf.variables['time'][t]

                tmp_var[:] += trend[:]*(month_idx + 1)
                of.variables[variable][month_idx, :, :, :] = tmp_var[:]
                of.variables['time'][month_idx] = bf.variables['time'][t]

                month_idx += 1

    if variable == 'temp':
        # Check temperature units.
        assert(np.max(of.variables[variable][0, 0, :, :]) < 40.0)
        of.variables[variable].units = 'degrees C'

    # Adjust time axis to the beginning and end of the month.
    assert(month_idx % 12 == 0)
    of.variables['time'][0] -= 15.5
    of.variables['time'][-1] += 15.5
    nt_of.variables['time'][0] -= 15.5
    nt_of.variables['time'][-1] += 15.5

    # Check that time dimension looks reasonable, we expect that the base
    # files have an increasing time dimension.
    assert(min(np.diff(of.variables['time'])) >= 29)
    assert(max(np.diff(of.variables['time'])) <= 46)
    assert(min(np.diff(nt_of.variables['time'])) >= 29)
    assert(max(np.diff(nt_of.variables['time'])) <= 46)

    of.close()
    nt_of.close()

    return output_file, no_trend_output_file


def make_damp_coeff_field(restoring_file, trend_file, damp_coeff, variable):
    """
    Make the damping coeffiecient field. It has a non-zero value everywhere
    where there is a trend.
    """

    with nc.Dataset(trend_file) as tf:
        trend = tf.variables[variable][0, :, :, :]

    output_file = '{}_sponge_coeff.nc'.format(variable)
    shutil.copy(restoring_file, output_file)

    with nc.Dataset(output_file, 'r+') as of:
        of.renameVariable(variable, 'coeff')

        time_var = of.variables['time']
        for t in range(time_var.shape[0]):
            var = of.variables['coeff'][t, :]
            var[:] = 0.0
            var[np.where(trend != 0)] = damp_coeff
            of.variables['coeff'][t, :] = var[:]

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("base_files", nargs='+',
                        help="""The file containing the base variable.
                        This is expected to contain monthly means.""")
    parser.add_argument("--annual_trend",
                        help="""The file containing the trend. The trend is
                        expected to be annual.""")
    parser.add_argument("--variable", default='temp',
                        help="""
                        The name of the variable being sponged. This needs
                        to exist in both the base_file and annual trend file.""")
    parser.add_argument("--damp_coeff", type=float, default=1e-5,
                        help="""
                        Value for the damping coefficient in grid boxes where
                        there is a trend. Elsewhere the coefficient will be zero.
                        """)
    args = parser.parse_args()

    restoring_file, no_trend_restoring_file = \
        make_restoring_field(args.base_files, args.annual_trend, args.variable)

    pool = mp.Pool(2)
    pool.map(compress_netcdf_file, [restoring_file, no_trend_restoring_file])
    make_damp_coeff_field(restoring_file, args.annual_trend,
                            args.damp_coeff, args.variable)

if __name__ == "__main__":
    sys.exit(main())
