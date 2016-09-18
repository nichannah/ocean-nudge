# ocean-nudge

Create ocean temperature and salt nudging and damping coefficient files. These files can used to nudge an either MOM or NEMO towards observations.

# Step 1

Download temperature and salinity fields from the GODAS or ORAS reanalysis dataset. Consider the length of your run and download however many months of reanalysis are needed. Be sure to download GODAS in NetCDF format. Useful URLs:

GODAS: http://www.esrl.noaa.gov/psd/data/gridded/data.godas.html
ORAS4: ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/

# Step 2

Regrid the reanalysis files to the model grid. Do this with the ocean-regrid tool by following the documentation here.

For example, for MOM:
```
$ ./regrid.py
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

Combine the above regridded reanalysis files into a single nudging source file.

e.g. for MOM:
```
$ ./makenudge.py mom_oras4.nc --damp_coeff 1e-5
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

## NEMO

