
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

The 'godas.tab' file is metadata that describes the variable names, a minimal version can be found in the test data for this tool (http://s3-ap-southeast-2.amazonaws.com/dp-drop/ocean-nudge/test/test_data.tar.gz). It can also be downloaded from [here](http://www.nco.ncep.noaa.gov/pmb/docs/on388/table2.html#TABLE128) but care must be taken to ensure that the potential termperature variable name ends up being 'pottmp' and the salinity variable is 'salt'.

We can convert them all in a bash for loop as follows:

```{bash}
$ for d in 20031231 20040105 20040110; do \
    cdo -f nc -t godas.tab copy godas.P.${d}.grb godas.P.${d}.nc; \
  done
```

## Step 3.

Regrid data to NEMO grid, note that these commands are executed from within the test/test_data/input directory.

```{bash}
$ cd test/test_data/input
$ for d in 20031231 20040105 20040110; do \
    ../../../regrid_simple.py GODAS godas.P.${d}.nc POT NEMO \
    godas_temp_${d}_nemo_grid.nc --regrid_weights regrid_weights.nc; \
  done
```

Alternatively, regrid using regrid.py as described [here](../README.md).

## Step 4.

Combine the above regridded reanalysis files into a single nudging source file.

For Nemo:
```
$ ../../../makenudge.py NEMO temp --forcing_files godas_temp_20031231_nemo_grid.nc
    godas_temp_20040105_nemo_grid.nc godas_temp_20040105_nemo_grid.nc
```

## Step 4.1

There is a test which does steps 1-4 above using example data:

```
$ python -m pytest -s -m slow test/
```

## Step 5.

Configure the model to use the newly created nudging file. This similar as for monthly data ([see here](../README.md)), with the following differences:
    - since the nudging source file contains one month it needs to end with _m01.nc, for example 1_data_1m_potential_temperature_nomask_m01.nc and 1_data_1m_salinity_nomask_m01.nc
    - the files now contain 5 daily rather than monthly data, so the frequency column below must be changed. 
    
```{fortran}
&namrun        !   parameters of the run
!-----------------------------------------------------------------------
    ln_rstart   = .false.   !  start from rest (F) or from a restart file (T)

&namtsd    !   data : Temperature  & Salinity
!-----------------------------------------------------------------------
!          !  file name                            ! frequency (hours) ! variable  ! time interp. !  clim  ! 'yearly'/ ! weights  ! rotation ! land/sea mask !
!          !                                       !  (if <0  months)  !   name    !   (logical)  !  (T/F) ! 'monthly' ! filename ! pairing  ! filename      !
    sn_tem  = 'data_1m_potential_temperature_nomask',         120        ,'votemper' ,    .true.    , .true. , 'yearly'   , ''       ,   ''    ,    ''
    sn_sal  = 'data_1m_salinity_nomask'             ,         120        ,'vosaline' ,    .true.    , .true. , 'yearly'   , ''       ,   ''    ,    ''
    ln_tsd_init   = .true.    !  Initialisation of ocean T & S with T &S input data (T) or not (F)
    ln_tsd_tradmp = .true.   !  damping of ocean T & S toward T &S input data (T) or not (F)
```


