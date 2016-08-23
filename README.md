# ocean-nudge

Create ocean nudging tracer source and damping coeficient using GODAS reanalysis. These files can these be used to nudge an either MOM or NEMO towards observations.

# Use

Download temperature and salinity fields from the GODAS reanalysis dataset:

http://www.esrl.noaa.gov/psd/data/gridded/data.godas.html

Example command to create temperature and salinity sources for MOM with a damping coefficient.
```
$ ./makenudge.py MOM --ocean_mask ocean_mask.nc ocean_hgrid.nc ocean_vgrid.nc --temp pottmp.2016.nc --salt salt.2016.nc --damp_coeff 1e-5
```

