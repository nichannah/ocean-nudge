# ocean-nudge

Create ocean temperature and salt nudging and damping coefficient files. These files can used to nudge an either MOM or NEMO towards observations.

# Step 1

Download temperature and salinity fields from the GODAS or ORAS reanalysis dataset. Be sure to download GODAS in NetCDF format. Useful URLs:

- GODAS: http://www.esrl.noaa.gov/psd/data/gridded/data.godas.html
- ORAS4: ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/

For example for ORAS4:

```
$ wget ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/monthly_orca1/thetao_oras4_1m_2003_grid_T.nc.gz
$ wget ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/monthly_orca1/thetao_oras4_1m_2004_grid_T.nc.gz
$ wget ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/monthly_orca1/thetao_oras4_1m_2005_grid_T.nc.gz
$ wget ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/orca1_coordinates/coordinates_grid_T.nc
$ gunzip *.gz
```

Note that the coordinates of the T grid are also downloaded.

# Step 2

Regrid the reanalysis files to the model grid. Do this with the ocean-regrid tool by following the documentation [here](https://github.com/nicjhan/ocean-regrid).

For example, for MOM:
```
$ ./regrid.py ORAS4 coordinates_grid_T.nc coordinates_grid_T.nc thetao_oras4_1m_2004_grid_T.nc thetao \
        MOM ocean_hgrid.nc ocean_vgrid.nc oras4_temp_on_mom_grid.nc temp \
        --dest_mask ocean_mask.nc --regrid_weights regrid_weights.nc
```

We can use a bash for-loop to regrid multiple files with a single command:
```
$ for i in 2003 2004 2005; do \
    ./regrid.py ORAS4 coordinates_grid_T.nc coordinates_grid_T.nc thetao_oras4_1m_${i}_grid_T.nc thetao \
        MOM ocean_hgrid.nc ocean_vgrid.nc oras4_temp_${i}_mom_grid.nc temp \
        --dest_mask ocean_mask.nc --regrid_weights regrid_weights.nc;
done
```

Note that in this case because the --regrid_weights option is used the computationally expensive part of the regridding only done once and the whole operation should be relatively fast. It can be sped up further by using the --use_mpi option.

# Step 3

Combine the above regridded reanalysis files into a single nudging source file. Note the reanalyses are monthly averages with a nominal time index in the middle of the month. This means that in order for nudging to start at the beginning of the year data from the previous year is needed - makenudge.py creates data for the beginning of January by interpolating from December of the previous year. So, for example to nudge the model for the whole of 2004:

e.g. for MOM:
```
$ time ./makenudge.py oras4_temp_2003_mom_grid.nc oras4_temp_2004_mom_grid.nc \
    oras4_temp_2005_mom_grid.nc --base_year 2003
real    16m46.109s
user    15m44.637s
sys     3m56.738s
```

Note that this is a long-running operation, the nudging files can be big and time consuming compression is needed. For MOM there will be two kinds of otuput, the actual nudging source file which ends in \_sponge.nc and the 3D relaxation coefficient file which ends in \_coeff_sponge.nc.

For Nemo:
```
$ ./makenudge.py oras4_temp_2003_nemo_grid.nc oras4_temp_2004_nemo_grid.nc \
    oras4_temp_2005_nemo_grid.nc --base_year 2003
```

This will output two files: 1_data_1m_potential_temperature_nomask.nc (for temperature) and resto.nc.

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

Take note of the model output as MOM starts up, there should be output similar to the following:

```
==> Note from ocean_sponges_tracer_mod: Using this module.
==> Using sponge damping times specified from file INPUT/temp_sponge_coeff.nc
==> Using sponge data specified from file INPUT/temp_sponge.nc
```

A common error looks like:
```
FATAL from PE   39: time_interp_external 2: time after range of list,file=INPUT/temp_sponge.nc,field=temp
```

This means that the time range covered by the nudging/sponge file does not match the model runtime. For example the sponge time may go from 0001-01-01 to 0002-01-01 while the model starts in 2004. Check the time range of the nudging source file with the following commands:

```
$ ncdump -h temp_sponge.nc
$ ncdump -v time temp_sponge.nc
```

## NEMO

The NEMO_3.6 ORCA2_LIM configuration is already set up to do global nudging, it does this to maintain temperature and salinity tracers in the Mediterranean. To carry out global nudging with the files generated above just replace the input files: 1_data_1m_potential_temperature_nomask.nc, 1_data_1m_salinity_nomask.nc and resto.nc
