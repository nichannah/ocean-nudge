#!/usr/bin/env python

from __future__ import print_function

import sys, os
import shutil
import argparse
import numpy as np
import multiprocessing as mp
import netCDF4 as nc

from file_util import create_mom_nudging_file, create_nemo_nudging_file
from lib_util import compress_netcdf_file

"""
Combine forcing fields to create nudging files that can be used to nudge salt
and temperature within MOM or NEMO.

Example use:

./makenudge.py ocean.nc temp -d 1e-08

Output for MOM:

temp_sponge_coeff.nc
temp_sponge.nc

Output for NEMO:

Assumptions:
- The base files are monthly means.
"""

def make_nudging_field(forcing_files, var_name, output_file,
                       start_date, monthly_resolution):
    """
    Combine forcing files into a nudging field/file. This may invlolve
    increasing the time resolution of the forcing using linear interpolation.
    """

    of = nc.Dataset(output_file, 'r+')
    output_idx = 0

    for file in forcing_files:
        with nc.Dataset(file, 'r') as ff:
            time_var = ff.variables['time']
            for t in range(time_var.shape[0]):
                tmp_var = ff.variables[var_name][t, :]
                # Convert to degrees C, used internally by the model.
                if var_name == 'temp' and 'degrees K' in ff.variables[var_name].units:
                    tmp_var -= 273.15

                of.variables[var_name][output_idx, :] = tmp_var[:]
                output_idx += 1

    if var_name == 'temp':
        # Check temperature units.
        assert(np.max(of.variables[var_name][0, 0, :, :]) < 40.0)
        of.variables[var_name].units = 'degrees C'

    # FIXME: figure out what to do with the time variable.
    #of.variables['time'][0] = start_day
    #of.variables['time'][-1] = end_day

    # Check that time dimension looks reasonable, we expect that the base
    # files have an increasing time dimension.
    #assert(min(np.diff(of.variables['time'])) >= 29)
    #assert(max(np.diff(of.variables['time'])) <= 46)

    of.close()        


def make_damp_coeff_field(output_file, damp_coeff, variable):
    """
    Make the damping coeffiecient field.
    """
    with nc.Dataset(output_file, 'r+') as of:
        of.renameVariable(variable, 'coeff')

        time_var = of.variables['time']
        for t in range(time_var.shape[0]):
            of.variables['coeff'][t, :] = damp_coeff

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("forcing_files", nargs='+',
                        help="""The files containing salt and temp
                        forcing variables.
                        This is expected to contain monthly means.""")
    parser.add_argument("--model_name", default='MOM',
                        help="Name of the model to nudge, can be MOM or NEMO.")
    parser.add_argument("--damp_coeff", type=float, default=1e-5,
                        help="Value for the damping coefficient.")
    parser.add_argument("--start_date", default='01-01-0001',
                        help="The start date of the nudging output.")
    parser.add_argument("--resolution", default=0,
                        help="""The number of intra-monthly points created by
                                interpolating between forcing inputs.""")
    args = parser.parse_args()

    assert args.model_name == 'MOM' or args.model_name == 'NEMO'

    if args.model_name == 'MOM':
        temp_var = 'temp'
        salt_var = 'salt'
    else:
        temp_var = 'votemper'
        salt_var = 'vosaline'

    for var in [temp_var, salt_var]:
        for postfix in ['_spong.nc', '_sponge_coeff.nc']:
            filename = var + postfix
            if os.path.exists(filename):
                print('Error: output file {} exists. '.format(filename) + \
                      'Please move or remove', file=sys.stderr)
                return 1

    #for var in (temp_var, salt_var):
    for var_name in [temp_var]:
        nudging_file = var_name + '_sponge.nc'
        create_mom_nudging_file(nudging_file, var_name, '', '', args.forcing_files[0])
        make_nudging_field(args.forcing_files, var_name, nudging_file,
                           args.start_date, args.resolution)

        coeff_file = '{}_sponge_coeff.nc'.format(var_name)
        shutil.copy(nudging_file, coeff_file)
        make_damp_coeff_field(coeff_file, args.damp_coeff, var_name)

    pool = mp.Pool(2)
    pool.map(compress_netcdf_file, [nudging_file, coeff_file])


if __name__ == "__main__":
    sys.exit(main())
