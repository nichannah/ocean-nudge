# ocean-nudge

Create ocean temperature and salt nudging and damping coefficient files. These files can used to nudge an either MOM or NEMO towards observations.

# Step 1

Download temperature and salinity fields from the GODAS or ORAS reanalysis dataset. Be sure to download GODAS in NetCDF format. Useful URLs:

GODAS: http://www.esrl.noaa.gov/psd/data/gridded/data.godas.html
ORAS4: ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/

# Step 2

Regrid the reanalysis files to the model grid. Do this with the ocean-regrid tool by following the documentation here.

For example, for MOM:
```
$ ./regrid.py ORAS4 coords_T.nc coords_T.nc thetao_oras4_1m_2014_grid_T.nc thetao MOM ocean_hgrid.nc ocean_vgrid.nc oras4_on_mom_grid.nc temp --dest_mask ocean_mask.nc
```

We can use a bash for-loop to regrid multiple files with a single command:
```
$ ./regrid.py
```

The same can be done for NEMO:

```
$ ./regrid.py
```

# Step 3

Combine the above regridded reanalysis files into a single nudging source file. Note the reanalyses are monthly averages with a nominal time index in the middle of the month. This means that in order for nudging to start at the beginning of the year data from the previous year is needed - makenudge.py can create data for the beginning January by interpolating from December of the previous year.

e.g. for MOM:
```
$ ./makenudge.py oras4_on_mom_grid.nc
```

For MOM there will be two kinds of otuput

for NEMO:
```
$ ./makenudge.py NEMO --damp_coeff 1e-5 --start_date "01-01-2016" <input01.nc> <input02.nc>
```

Be careful with the --run_start_year and --run_start_month options. These are used to specify the date at which the nudging will start within the run. If it does not match the model run date then either the model will exit with an error or the nudging will not be applied correctly.

# Step 4

Configure the model to use the newly created nuding file. See below for instructions for both MOM and NEMO.

## MOM

Copy the \*\_sponge.nc files from above into the MOM INPUT directory. Then add the following to the input.nml:

```
&ocean_sponges_tracer_nml
    use_this_module = .TRUE.
    damp_coeff_3d = .TRUE.
/
```

Take not of the model output as MOM starts up, there should be output similar to the following:

```
==> Note from ocean_sponges_tracer_mod: Using this module.
==> Using sponge damping times specified from file INPUT/temp_sponge_coeff.nc
==> Using sponge data specified from file INPUT/temp_sponge.nc
```

A common error looks like:
```
FATAL from PE   39: time_interp_external 2: time after range of list,file=INPUT/temp_sponge.nc,field=temp
```

This means that the time range covered by the nudging/sponge file does not match the model runtime. For example the sponge time may go from 0001-01-01 to 0002-01-01 while the model starts in 2004.

## NEMO


