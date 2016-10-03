# ocean-nudge

Create ocean temperature and salt nudging and damping coefficient files. These files can used to nudge an either MOM or NEMO towards observations.

Build status: [![Build Status](https://travis-ci.org/nicjhan/ocean-nudge.svg?branch=master)](https://travis-ci.org/nicjhan/ocean-nudge)

## Install

This tool is written in Python and depends a few different Python packages. It also depends on
 [ESMF_RegridWeightGen](https://www.earthsystemcog.org/projects/regridweightgen/) program to perform regridding between non-rectilinear grids.

## Download

Download ocean-nudge:
```{bash}
$ git clone --recursive https://github.com/nicjhan/ocean-nudge.git
```

## Python dependencies

Use Anaconda as described below or an existing Python setup.

1. Download and install [Anaconda](https://www.continuum.io/downloads) for your platform.
2. Setup the Anaconda environment. This will download all the necessary Python packages.
```{bash}
$ cd ocean-ic
$ conda env create -f regrid.yml
$ source activate regrid
```

## ESMF dependencies

Install ESMF_RegridWeightGen. ESMF releases can be found [here](http://www.earthsystemmodeling.org/download/data/releases.shtml).

There is a bash script regridder/contrib/build_esmf.sh which the testing system uses to build ESMF. This may be useful in addition to the ESMF installation docs.

# Use

Follow the example steps below to nudge MOM or NEMO using ORAS4 monthly data. In addition [here](docs/NEMO_GODAS_pentad.md) is an example that nudges [NEMO using GODAS pentad](docs/NEMO_GODAS_pentad.md).

## Step 1

Download temperature and salinity fields from the GODAS or ORAS reanalysis dataset. Be sure to download GODAS in NetCDF format. Useful URLs:

- GODAS: http://www.esrl.noaa.gov/psd/data/gridded/data.godas.html
- ORAS4: ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/

For example for ORAS4:

```{bash}
$ cd test
$ mkdir -p test_data/input/
$ cd test_data/input/
$ wget ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/monthly_orca1/thetao_oras4_1m_2003_grid_T.nc.gz
$ wget ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/monthly_orca1/thetao_oras4_1m_2004_grid_T.nc.gz
$ wget ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/monthly_orca1/thetao_oras4_1m_2005_grid_T.nc.gz
$ wget ftp://ftp.icdc.zmaw.de/EASYInit/ORA-S4/orca1_coordinates/coordinates_grid_T.nc
$ gunzip *.gz
```

Note that the coordinates of the T grid are also downloaded.

Alternatively, download the test data that comes with the package:

```{bash}
$ cd test
$ wget http://s3-ap-southeast-2.amazonaws.com/dp-drop/ocean-nudge/test/test_data.tar.gz
$ tar zxvf test_data.tar.gz
$ cd test_data/input
```

## Step 2

Regrid the reanalysis files to the model grid. Do this with the ocean-regrid tool found in the regridder directory. Additional documentation can be found here [here](https://github.com/nicjhan/ocean-regrid).

The following commands assume a working directory of test/test_data/input.

For example, for MOM:
```{bash}
$ ../../../regridder/regrid.py ORAS4 coordinates_grid_T.nc coordinates_grid_T.nc thetao_oras4_1m_2004_grid_T.nc thetao \
        MOM ocean_hgrid.nc ocean_vgrid.nc oras4_temp_on_mom_grid.nc temp \
        --dest_mask ocean_mask.nc --regrid_weights oras4_mom_regrid_weights.nc
```

We can use a bash for-loop to regrid multiple files with a single command:
```{bash}
$ for i in 2003 2004 2005; do \
    ../../../regridder/regrid.py ORAS4 coordinates_grid_T.nc coordinates_grid_T.nc thetao_oras4_1m_${i}_grid_T.nc thetao \
        MOM ocean_hgrid.nc ocean_vgrid.nc oras4_temp_${i}_mom_grid.nc temp \
        --dest_mask ocean_mask.nc --regrid_weights oras4_mom_regrid_weights.nc;
done
```

And for NEMO:

```{bash}
$ for i in 2003 2004 2005; do \
    ../../../regridder/regrid.py ORAS4 coordinates_grid_T.nc coordinates_grid_T.nc thetao_oras4_1m_${i}_grid_T.nc thetao \
        NEMO coordinates.nc data_1m_potential_temperature_nomask.nc oras4_temp_${i}_nemo_grid.nc votemper \
        --regrid_weights oras4_nemo_regrid_weights.nc; \
done
```

Note that in this case because the --regrid_weights option is used the computationally expensive part of the regridding only done once and the whole operation should be relatively fast. It can be sped up further by using the --use_mpi option.

## Step 3

Combine the above regridded reanalysis files into a single nudging source file. Note the reanalyses are monthly averages with a nominal time index in the middle of the month. This means that in order for nudging to start at the beginning of the year data from the previous year is needed - the models create data for the beginning of January by interpolating from December of the previous year. So, for example to nudge the model for the whole of 2004:

e.g. for MOM:
```
$ time ../../../makenudge.py oras4_temp_2003_mom_grid.nc oras4_temp_2004_mom_grid.nc \
    oras4_temp_2005_mom_grid.nc
real    16m46.109s
user    15m44.637s
sys     3m56.738s
```

Note that this is a long-running operation, the nudging files can be big and time consuming compression is needed. For MOM there will be two kinds of otuput, the actual nudging source file which ends in \_sponge.nc and the 3D relaxation coefficient file which ends in \_coeff_sponge.nc.

For Nemo:
```
$ ../../../makenudge.py --model_name NEMO --input_var_name votemper oras4_temp_2003_nemo_grid.nc \
    oras4_temp_2004_nemo_grid.nc oras4_temp_2005_nemo_grid.nc
```

This will output two files: \<input_var_name\>\_nomask.nc and resto.nc. In order to do temperature and salinity nudging this needs to be done twice, once for temperature (and above) and once for salinity. For example:

```
$ ../../../makenudge.py --model_name NEMO --input_var_name vosaline oras4_salt_2003_nemo_grid.nc \
    oras4_salt_2004_nemo_grid.nc oras4_salt_2005_nemo_grid.nc
```

## Step 4

Configure the model to use the newly created nuding file. See below for instructions for both MOM and NEMO.

### MOM

Copy the \*\_sponge.nc files from above into the MOM INPUT directory. Then add the following to the input.nml:

```{fortran}
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

### NEMO

The NEMO_3.6 ORCA2 configuration is already set up to do global nudging, it does this to maintain temperature and salinity tracers in the Mediterranean. To carry out global nudging with the files generated above:

1. replace the input files: 1_data_1m_potential_temperature_nomask.nc and 1_data_1m_salinity_nomask.nc with the corrosponding temperature and salinity \_nomask.nc files generated above. Overwrite the input file resto.nc with the file of the same name generated above.

2. Check the values of following configuration namelist parameters:

```{fortran}
&namrun        !   parameters of the run
!-----------------------------------------------------------------------
    ln_rstart   = .false.   !  start from rest (F) or from a restart file (T)

&namtsd    !   data : Temperature  & Salinity
!-----------------------------------------------------------------------
!          !  file name                            ! frequency (hours) ! variable  ! time interp. !  clim  ! 'yearly'/ ! weights  ! rotation ! land/sea mask !
!          !                                       !  (if <0  months)  !   name    !   (logical)  !  (T/F) ! 'monthly' ! filename ! pairing  ! filename      !
    sn_tem  = 'data_1m_potential_temperature_nomask',         -1        ,'votemper' ,    .true.    , .true. , 'yearly'   , ''       ,   ''    ,    ''
    sn_sal  = 'data_1m_salinity_nomask'             ,         -1        ,'vosaline' ,    .true.    , .true. , 'yearly'   , ''       ,   ''    ,    ''
    ln_tsd_init   = .true.    !  Initialisation of ocean T & S with T &S input data (T) or not (F)
    ln_tsd_tradmp = .true.   !  damping of ocean T & S toward T &S input data (T) or not (F)

!-----------------------------------------------------------------------
&namtra_dmp    !   tracer: T & S newtonian damping
!-----------------------------------------------------------------------
    ln_tradmp   =  .true.   !  add a damping termn (T) or not (F)
    nn_zdmp     =    0      !  vertical   shape =0    damping throughout the water column
                            !                   =1 no damping in the mixing layer (kz  criteria)
                            !                   =2 no damping in the mixed  layer (rho crieria)
    cn_resto    = 'resto.nc'! Name of file containing restoration coefficient field
/
```
