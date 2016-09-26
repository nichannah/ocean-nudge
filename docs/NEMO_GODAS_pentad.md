
# Nudging NEMO using GODAS pentad data

## Step 1.

Download GODAS pentad data from (here)[http://cfs.ncep.noaa.gov/cfs/godas/pentad/]:

```{bash}
$ wget http://cfs.ncep.noaa.gov/cfs/godas/pentad/2003/godas.P.20031231.grb
$ wget http://cfs.ncep.noaa.gov/cfs/godas/pentad/2004/godas.P.20040105.grb
$ wget http://cfs.ncep.noaa.gov/cfs/godas/pentad/2004/godas.P.20040110.grb
```

## Step 2.

Convert downloaded data to netCDF format. Unfortunately the GODAS pentad data is only available in GRIB format so we need to convert to netCDF. There are many tools that can be used to do this, we recommend using (cdo)[https://code.zmaw.de/projects/cdo] because it is widely available on weather and climate computing platforms.

```{bash}
$ cdo -f nc -t test_data/godas.tab copy godas.P.20031231.grb godas.P.20031231.nc
```

The 'godas.tab' file is metadata that describes the variable names, it can be downloaded from [here](http://www.nco.ncep.noaa.gov/pmb/docs/on388/table2.html#TABLE128) or a minimal version can be found in the test_data directory of this repository.

We can convert them all in a bash for loop as follows:

```{bash}
$ for d in 20031231 20040105 20040110; do \
    cdo -f nc -t godas.tab copy godas.P.${d}.grb godas.P.${d}.nc; \
  done
```

## Step 3.

Regrid data to NEMO grid.

```{bash}
$ for d in 20031231 20040105 20040110; do \
    ./regrid.py GODAS godas.P.${d}.nc godas.P.${d}.nc godas.P.${d}.nc POT \
    NEMO coordinates.nc data_1m_potential_temperature_nomask.nc \
    godas_temp_${d}_nemo_grid.nc votemper --regrid_weights regrid_weights.nc; \
  done
```

## Step 4.

## Step 5.

