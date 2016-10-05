
# Nudging NEMO using GODAS pentad data

## Step 1.

Download GODAS pentad data from (here)[http://cfs.ncep.noaa.gov/cfs/godas/pentad/]:

```{bash}
$ mkdir -p test/test_data/input
$ cd test/test_data/input
$ wget http://cfs.ncep.noaa.gov/cfs/godas/pentad/2003/godas.P.20031231.grb
$ wget http://cfs.ncep.noaa.gov/cfs/godas/pentad/2004/godas.P.20040105.grb
$ wget http://cfs.ncep.noaa.gov/cfs/godas/pentad/2004/godas.P.20040110.grb
```

Alternatively download the test dataset for this tool.

```{bash}
$ cd test/
$ wget http://s3-ap-southeast-2.amazonaws.com/dp-drop/ocean-nudge/test/test_data.tar.gz
$ tar zxvf test_data.tar.gz
$ cd test_data/input
```

## Step 2.

Convert downloaded data to netCDF format. Unfortunately the GODAS pentad data is only available in GRIB format so we need to convert to netCDF. There are many tools that can be used to do this, we recommend using (cdo)[https://code.zmaw.de/projects/cdo] because it is widely available on weather and climate computing platforms.

```{bash}
$ cdo -f nc -t test_data/godas.tab copy godas.P.20031231.grb godas.P.20031231.nc
```

The 'godas.tab' file is metadata that describes the variable names, it can be downloaded from [here](http://www.nco.ncep.noaa.gov/pmb/docs/on388/table2.html#TABLE128) or a minimal version can be found in the test data for this tool (http://s3-ap-southeast-2.amazonaws.com/dp-drop/ocean-nudge/test/test_data.tar.gz).

We can convert them all in a bash for loop as follows:

```{bash}
$ for d in 20031231 20040105 20040110; do \
    cdo -f nc -t godas.tab copy godas.P.${d}.grb godas.P.${d}.nc; \
  done
```

## Step 3.

Regrid data to NEMO grid, note that these commands are executed from within the test/test_data/input directory.

```{bash}
$ for d in 20031231 20040105 20040110; do \
    ../../../regridder/regrid.py GODAS godas.P.${d}.nc godas.P.${d}.nc godas.P.${d}.nc POT \
    NEMO coordinates.nc data_1m_potential_temperature_nomask.nc \
    godas_temp_${d}_nemo_grid.nc votemper --regrid_weights regrid_weights.nc; \
  done
```

## Step 4.

Combine the above regridded reanalysis files into a single nudging source file.

For Nemo:
```
$ ../../../makenudge.py --model_name NEMO --input_var_name votemper \
    godas_temp_20031231_nemo_grid.nc godas_temp_20040105_nemo_grid.nc godas_temp_20040105_nemo_grid.nc
```

## Step 4.1

There is a test which does steps 1-4 above using example data:

```
$ python -m pytest -s -m slow test/
```

## Step 5.

Configure the model to use the newly created nudging file. This is the same as for monthly data, [see here](../README.md)

