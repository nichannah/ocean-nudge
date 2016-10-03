
from __future__ import print_function

import pytest
import os
import subprocess as sp
import sh
import glob

data_tarball = 'test_data.tar.gz'
data_tarball_url = 'http://s3-ap-southeast-2.amazonaws.com/dp-drop/ocean-nudge/test/test_data.tar.gz'

def convert_grib_to_netcdf(input_dir):

    godas_tab = os.path.join(input_dir, 'godas.tab')

    for f in glob.glob(input_dir + '/*.grb'):
        ret = sp.call(['cdo', '-f', 'nc', '-t', godas_tab, 'copy', f, f + '.nc'])
        assert ret == 0

    return glob.glob(input_dir + '/*.grb.nc')

def regrid_to_nemo(regridder, input_dir, input_files):

    output_files = [inf + '_nemo.nc' for inf in input_files]

    hgrid = os.path.join(input_dir, 'coordinates.nc')
    vgrid = os.path.join(input_dir, 'data_1m_potential_temperature_nomask.nc')

    if os.path.exists('regrid_weights.nc'):
        os.remove('regrid_weights.nc')

    for inf, outf in zip(input_files, output_files):
        if os.path.exists(outf):
            os.remove(outf)

        ret = sp.call([regridder, 'GODAS', inf, inf, inf, 'POT',
                       'NEMO', hgrid, vgrid, outf, 'votemper',
                        '--regrid_weights', 'regrid_weights.nc'])
        assert ret == 0

    return output_files


class TestRegrid():

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

    def test_nemo_godas_pentad(self, input_dir, output_dir):

        # Convert GRIB pentad files to netcdf.
        pentad_files = convert_grib_to_netcdf(input_dir)

        # Regrid pendad files to NEMO grid.
        my_dir = os.path.dirname(os.path.realpath(__file__))
        regridder = os.path.join(my_dir, '../regridder/', 'regrid.py')
        nemo_pentad_files = regrid_to_nemo(regridder, input_dir, pentad_files)

        filenames = ['votemper_nomask.nc', 'resto.nc']
        output_files = [os.path.join(my_dir, '../', fn) for fn in filenames]
        for outf in output_files:
            if os.path.exists(outf):
                os.remove(outf)

        # Create the nudging source files.
        makenudge = os.path.join(my_dir, '../', 'makenudge.py')
        ret = sp.call([makenudge, '--model_name', 'NEMO', '--input_var_name',
                       'votemper'] + nemo_pentad_files)
        assert ret == 0

        # Check that outputs exist.
        for outf in output_files:
            assert os.path.exists(outf)
