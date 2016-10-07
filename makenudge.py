#!/usr/bin/env python

from __future__ import print_function

import sys, os
import shutil
import argparse
import datetime as dt
import numpy as np
import multiprocessing as mp
import netCDF4 as nc

from file_util import create_mom_nudging_file, create_nemo_nudging_file
from lib_util import compress_netcdf_file, sort_by_date, DaySeries, get_time_origin

def make_nudging_field(forcing_files, var_name, output_file,
                       start_date):
    """
    Combine forcing files into a nudging field/file. This may invlolve
    increasing the time resolution of the forcing using linear interpolation.
    """

    of = nc.Dataset(output_file, 'r+')

    if of.variables.has_key('time_counter'):
        time_name = 'time_counter'
    else:
        time_name = 'time'

    output_idx = 0

    day_series = DaySeries(forcing_files)
    days = day_series.days

    for file in forcing_files:
        with nc.Dataset(file, 'r') as ff:
            time_var = ff.variables[time_name]

            for t in range(time_var.shape[0]):
                tmp_var = ff.variables[var_name][t, :]
                of.variables[var_name][output_idx, :] = tmp_var[:]
                of.variables[time_name][output_idx] = days[output_idx]
                output_idx += 1

    of.close()


def make_damp_coeff_field(output_file, damp_coeff, variable, model_name):
    """
    Make the damping coeffiecient field.
    """
    with nc.Dataset(output_file, 'r+') as of:
        if model_name == 'MOM':
            coeff_name = 'coeff'
        else:
            assert model_name == 'NEMO'
            coeff_name = 'resto'

        of.renameVariable(variable, coeff_name)

        if of.variables.has_key('time_counter'):
            time_name = 'time_counter'
        else:
            time_name = 'time'

        time_var = of.variables[time_name]
        for t in range(time_var.shape[0]):
            of.variables[coeff_name][t, :] = damp_coeff


def guess_input_var_name(forcing_file, tracer):

    if tracer == 'temp':
        possible_vars = ['temp', 'votemper', 'POT', 'pottmp']
    else:
        assert tracer == 'salt'
        possible_vars = ['salt', 'vosaline', 'SALTY']

    with nc.Dataset(forcing_file) as f:
        for pv in possible_vars:
            if f.variables.has_key(pv):
                return pv

    return None


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("model_name",
                        help="Name of the model to nudge, can be MOM or NEMO.")
    parser.add_argument('nudging_var',
                        help="Variable to nudge. Must be 'salt' or 'temp'.")
    parser.add_argument("--forcing_files", nargs='+', default=None,
                        help="""The files containing salt or temp
                        forcing variables.
                        This is expected to contain monthly means or pentad.""")
    parser.add_argument("--input_var_name", default=None, help="""
                        The input variable name. Default is to guess
                        based on the nudging_var option""")
    parser.add_argument("--output_dir", default='./',
                        help="Directory where output files will be placed.")
    parser.add_argument("--damp_coeff", type=float, default=1e-5,
                        help="Value for the damping coefficient.")
    parser.add_argument("--start_year", default=None, type=int,
                        help="""
                        The start year of the nudging output. The default is to
                        use the start year of the earliest forcing file.
                        """)
    args = parser.parse_args()

    assert args.model_name == 'MOM' or args.model_name == 'NEMO'
    assert args.forcing_files is not None

    var_name = guess_input_var_name(args.forcing_files[0], args.nudging_var)
    assert var_name is not None

    if args.model_name == 'MOM':
        assert var_name == 'temp' or var_name == 'salt'

    if args.model_name == 'NEMO':
        assert var_name == 'votemper' or var_name == 'vosaline'

    forcing_files = sort_by_date(args.forcing_files)

    start_date = get_time_origin(forcing_files[0])
    if args.start_year is not None:
        start_date = dt.date(args.start_year, start_date.month, start_date.day)

    if args.model_name == 'MOM':
        assert var_name == 'temp' or var_name == 'salt'
        nudging_file = var_name + '_sponge.nc'
        coeff_file = '{}_sponge_coeff.nc'.format(var_name)
    else:
        nudging_file = var_name + '_nomask.nc'
        coeff_file = 'resto.nc'

    nudging_file = os.path.join(args.output_dir, nudging_file)
    coeff_file = os.path.join(args.output_dir, coeff_file)

    if args.model_name == 'MOM':
        create_mom_nudging_file(nudging_file, var_name, '', '',
                                start_date,
                                args.forcing_files[0])
    else:
        create_nemo_nudging_file(nudging_file, var_name, '', '',
                                start_date,
                                args.forcing_files[0])
    make_nudging_field(args.forcing_files, var_name, nudging_file, start_date)

    # Sort out units. FIXME: units are missing in netcdf, better way to do this.
    with nc.Dataset(nudging_file, 'r+') as f:
        if var_name == 'temp' or var_name == 'votemper':
            if np.max(f.variables[var_name][:]) > 273.0:
                f.variables[var_name][:] -= 273.15

                assert np.min(f.variables[var_name][:]) > -10.0 

        if var_name == 'salt' or var_name == 'vosaline':
            if np.max(f.variables[var_name][:]) < 1.0:
                f.variables[var_name][:] *= 1000

    shutil.copy(nudging_file, coeff_file)
    make_damp_coeff_field(coeff_file, args.damp_coeff, var_name, args.model_name)

    pool = mp.Pool(2)
    pool.map(compress_netcdf_file, [nudging_file, coeff_file])

if __name__ == "__main__":
    sys.exit(main())
