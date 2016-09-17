# ocean-nudge

Create ocean nudging tracer source and damping coeficient files. These files can these be used to nudge an either MOM or NEMO towards observations.

# What needs to be done

# Use

Download temperature and salinity fields from the GODAS or ORAS reanalysis dataset. Consider the length of your run and download however many months of reanalysis are needed. Be sure to download GODAS in NetCDF format. Here are the URLs:

GODAS: http://www.esrl.noaa.gov/psd/data/gridded/data.godas.html

Use the regridding functionality of makeic.py to move all of the downloaded files to the correct grid. We use a bash for-loop to run the program repeatedly:

```
$ ./makeic.py
```

Combine all of the above into a single nudging source file and create damping coefficient input.

e.g. for MOM:
```
$ ./makenudge.py ./makenudge.py mom_oras4.nc --damp_coeff 1e-5
```

for NEMO:
```
$ ./makenudge.py NEMO --damp_coeff 1e-5 --start_date "01-01-2016" <input01.nc> <input02.nc>
```


