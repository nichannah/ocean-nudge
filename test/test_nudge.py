
from __future__ import print_function

import pytest
import os
import subprocess as sp
import sh
import glob

data_tarball = 'test_data.tar.gz'
data_tarball_url = 'http://s3-ap-southeast-2.amazonaws.com/dp-drop/ocean-nudge/test/test_data.tar.gz'

def convert_grib_to_netcdf(input_dir, infiles, output_dir):

    ret = sp.call(['which', 'cdo'])
    assert ret == 0, 'Error: cdo not found.'

    godas_tab = os.path.join(input_dir, 'godas.tab')

    outfiles = [os.path.join(output_dir, os.path.basename(f)) \
                    + '.nc' for f in infiles]

    for inf, outf in zip(infiles, outfiles):
        ret = sp.call(['cdo', '-f', 'nc', '-t', godas_tab, 'copy', inf, outf])
        assert ret == 0

    return outfiles

def regrid_to_nemo(regridder, pentad_files, reanalysis_var, input_dir, output_dir):

    output_files = [os.path.join(output_dir, os.path.basename(f)) \
                        + reanalysis_var + '.nc' for f in pentad_files]

    weights = os.path.join(output_dir, 'regrid_weights.nc')

    if os.path.exists(weights):
        os.remove(weights)

    for inf, outf in zip(pentad_files, output_files):
        if os.path.exists(outf):
            os.remove(outf)

        ret = sp.call([regridder, 'GODAS', inf, reanalysis_var,
                       'NEMO', outf, '--regrid_weights', weights])
        assert ret == 0

    return output_files

def create_nemo_nudge_with_godas_pentad(input_dir, input_files, output_dir):

    # Convert GRIB pentad files to netcdf.
    pentad_files = convert_grib_to_netcdf(input_dir, input_files, output_dir)

    # Regrid pendad files to NEMO grid.
    my_dir = os.path.dirname(os.path.realpath(__file__))
    regridder = os.path.join(my_dir, '../', 'rere.py')
    nemo_temp_files = regrid_to_nemo(regridder, pentad_files, 'temp',
                                     input_dir, output_dir)
    nemo_salt_files = regrid_to_nemo(regridder, pentad_files, 'salt',
                                     input_dir, output_dir)

    filenames = ['votemper_nomask.nc', 'vosaline_nomask.nc', 'resto.nc']
    output_files = [os.path.join(output_dir, fn) for fn in filenames]
    for outf in output_files:
        if os.path.exists(outf):
            os.remove(outf)

    # Create the nudging source files.
    makenudge = os.path.join(my_dir, '../', 'makenudge.py')
    ret = sp.call([makenudge, 'NEMO', 'temp', '--output_dir', output_dir,
                   '--forcing_files'] + nemo_temp_files)
    assert ret == 0
    ret = sp.call([makenudge, 'NEMO', 'salt', '--output_dir', output_dir,
                   '--forcing_files'] + nemo_salt_files)
    assert ret == 0

    # Check that outputs exist.
    for outf in output_files:
        assert os.path.exists(outf)


class TestNudge():

    @pytest.fixture
    def input_dir(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        test_data_dir = os.path.join(test_dir, 'test_data')
        test_data_tarball = os.path.join(test_dir, data_tarball)

        if not os.path.exists(test_data_dir):
            if not os.path.exists(test_data_tarball):
                sh.wget('-P', test_dir, data_tarball_url)
            sh.tar('zxvf', test_data_tarball, '-C', test_dir)

        return os.path.join(test_data_dir, 'input')

    @pytest.fixture
    def output_dir(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        test_data_dir = os.path.join(test_dir, 'test_data')

        return os.path.join(test_data_dir, 'output')

    @pytest.mark.slow
    def test_nemo_godas_pentad(self, input_dir, output_dir):

        infiles = glob.glob(input_dir + '/*.grb')
        create_nemo_nudge_with_godas_pentad(input_dir, infiles, output_dir)

    @pytest.mark.fast
    def test_nemo_godas_pentad_minimal(self, input_dir, output_dir):

        infiles = glob.glob(input_dir + '/*.grb')
        create_nemo_nudge_with_godas_pentad(input_dir, [infiles[0]], output_dir)

