# Joe Hollowed
# March 2026
#
# This file provides functions for handling data reading, download, and location specification

import os
import pdb
import glob
import tarfile
import numpy as np
import xarray as xr
import urllib.request
from pathlib import Path

MIP_URL        = 'https://gml.noaa.gov/ccgg/arc/tmp/arcrepo_5o55jt6itntdbB1OASR/OCO2_v11MIP_gridded_fluxes_all_20260127.tar.gz'
REGION_URL     = 'https://gml.noaa.gov/aftp//products/carbontracker/co2/regions.nc'
AGGREGATES_URL = 'https://gml.noaa.gov/aftp/user/andy/OCO-2/mip/oco2_regions_l4mip_v7.nc'

MIP_DIR        = None
REGION_FILE    = None
AGGREGATE_FILE = None

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------

def get_region_list():
    '''
    Get a list of TransCom regions available
    '''
    # ---- get region identifiers, sort
    region_map  = xr.open_dataset(get_region_file())
    tc_regions  = region_map['transcom_regions']
    all_regions = sorted(np.unique(tc_regions).astype(int))

    # ---- get region names
    dim          = 'dim_transcom23'
    tc_names     = region_map['transcom_names']
    region_names = {}
    for ri in all_regions:
        region_names[ri] = str(tc_names.sel({dim:ri-1}).astype('str').values).strip()
    return region_names

def get_model_list():
    '''
    Get a list of models in the MIP ensemble
    '''
    dd = get_data_dir('MIP')
    files = glob.glob(f'{dd}/*gridded_fluxes_IS.nc4')
    models = [f.split('/')[-1].split('_')[0] for f in files]
    return models

def get_gc_model_list(transport=None):
    '''
    Get a list of GeosChem models in the MIP ensemble
    '''
    return ['Ames', 'CMS-Flux', 'GCAS', 'JHU', 'WOMBAT-GC'][::-1]

def get_tm5_model_list(transport=None):
    '''
    Get a list of GeosChem models in the MIP ensemble
    '''
    return ['CT', 'CT-MP', 'TM5-4DVAR', 'WOMBAT-TM5'][::-1]

def get_ensemble(obs, transport='all'):
    '''
    Read and return the netCDF data for the ensemble as an xarray Dataset, with
    new dimension 'model'

    Params
    ------
    obs : str
        the observational set to filter on. Must be one of the following:
        'IS', 'LNLG', 'LNLGIS', 'LNLGOGIS', or 'Prior'
    transport : str, optional
        transport model to filter on; either 'all', 'gc', or 'tm5'. Defaults
        to 'all', in which case no filtering is applied

    Returns
    -------
    xarray Dataset
        The ensemble data, with each model being an entry in the 'model' dimension,
        and coordinates as a string of its model name
    '''
    dd = get_data_dir('MIP')
    all_models = {'all':get_model_list(), 'tm5':get_tm5_model_list(), 
                  'gc':get_gc_model_list()}[transport]
    models = {}
    for model in all_models:
        models[model] = glob.glob(f'{dd}/*{model}*_{obs}*.nc4')[0]
 
    ens = xr.concat([xr.open_dataset(models[model]) for model in all_models],
                     dim=xr.DataArray(all_models, dims="model", name="model"))
    ens = to_latlon(ens)
    return ens

def get_tm5_ensemble(obs):
    '''
    Calls get_ensemble(obs, transport = 'tm5'); see docstrings therein
    '''
    return get_ensemble(obs, 'tm5')

def get_gc_ensemble(obs):
    '''
    Calls get_ensemble(obs, transport = 'gc'); see docstrings therein
    '''
    return get_ensemble(obs, 'gc')

def get_region_mask(region):
    '''
    Returns a binary region mask in lat,lon for the speicifed TransCom region

    Params
    ------
    region : int
        The TransCom region, specified by it's integer ID
    
    Returns
    -------
    The binary mask specifying this region
    '''
    # ---- get region mapping
    region_map  = to_latlon(xr.open_dataset(get_region_file()))
    tc_regions  = region_map['transcom_regions']
    # ---- get mask for specified region
    mask = tc_regions == region
    return mask

def to_latlon(x):
    '''
    Renames 'longitude' and 'latitude' dims to 'lon' and 'lat'

    Params
    ------
    x : xarray DataArray or Dataset

    Returns
    -------
    the input data with renamed dims
    '''
    return x.rename({'longitude':'lon', 'latitude':'lat'})


# --------------------------------------------------------------------------------


def get_mip_dir():
    '''
    Get the location of the MIP data, if exists, else raise error
    '''
    return get_data_dir('MIP')

def get_region_file():
    '''
    Get the location of the region data, if exists, else raise error
    '''
    return get_data_dir('regions')

def get_aggregate_file():
    '''
    Get the location of the aggregate region data, if exists, else raise error
    '''
    return get_data_dir('aggregates')


# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------


def get_cache_dir():
    '''
    Get data cache location, either specified by the OCO_MIP_DATASETS environment
    variable, or defaulting to the hidden diretory ~/.OCO_v11MIP_analysis 
    '''
    return os.getenv('OCO_MIP_DATASETS', f'{Path.home()}/.OCO_v11MIP_analysis')

def download_data(dataset, force=False):
    '''
    Download the data for the specified dataset

    Params
    ------
    dataset : str
        which dataset to download, either being
        'MIP'       : the MIP gridded flux data
        'regions'    : the CarbonTracker region definitions
        'aggregates' : the CarbonTracker regional aggregate definitions
        'all'       : all of the above
    '''
    cache_dir = get_cache_dir()
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    if(dataset == 'all'):
        MIP_DIR        = download_data('MIP')
        REGION_FILE    = download_data('regions')
        AGGREGATE_FILE = download_data('aggregates')
        return

    if(dataset == 'MIP'):
        filename    = MIP_URL.split('/')[-1]
        dirname     = filename.split('.')[0]
        tar_path    = f'{cache_dir}/{filename}'
        extract_dir = f'{cache_dir}/{dirname}'

        if Path(extract_dir).exists() and not force:
            print(f'Dataset already exists at {extract_dir}')
            return extract_dir

        if Path(tar_path).exists() and not force:
            print(f'Download already exists at {tar_path}')
        else:
            print('Downloading MIP data...')
            urllib.request.urlretrieve(MIP_URL, tar_path)

        print('Extracting dataset...')
        with tarfile.open(tar_path, 'r:gz') as tar:
            tar.extractall(extract_dir)
            os.remove(tar_path)

        print(f'Dataset ready at: {extract_dir}')
        return extract_dir

    elif(dataset == 'aggregates' or dataset == 'regions'):
        if(dataset == 'aggregates'): DATA_URL = AGGREGATES_URL
        elif(dataset == 'regions'):  DATA_URL = REGION_URL
        filename  = DATA_URL.split('/')[-1]
        data_file = f'{cache_dir}/{filename}'
        
        if Path(data_file).exists() and not force:
            print(f'Dataset already exists at {data_file}')
            return data_file

        print(f'Downloading {dataset} data...')
        urllib.request.urlretrieve(DATA_URL, data_file)

        print(f'Dataset ready at: {data_file}')
        return data_file

def get_data_dir(dataset, force=False):
    '''
    Retrieve the data location of the specified dataset

    Params
    ------
    dataset : str
        which dataset to locate, either being
        'MIP'       : the MIP gridded flux data
        'regions'    : the CarbonTracker region definitions
        'aggregates' : the CarbonTracker regional aggregate definitions
    '''
    cache_dir = get_cache_dir()
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    if(dataset == 'MIP'):
        filename    = MIP_URL.split('/')[-1]
        dirname     = filename.split('.')[0]
        extract_dir = f'{cache_dir}/{dirname}'

        if Path(extract_dir).exists():
            return extract_dir
        else:
            raise RuntimeError('Data not found!\n'\
                               'Run: OCO_v11MIP_analysis download all')

    elif(dataset == 'aggregates' or dataset == 'regions'):
        if(dataset == 'aggregates'): DATA_URL = AGGREGATES_URL
        elif(dataset == 'regions'):  DATA_URL = REGION_URL
        filename  = DATA_URL.split('/')[-1]
        data_file = f'{cache_dir}/{filename}'
        
        if Path(data_file).exists() and not force:
            return data_file
        else:
            raise RuntimeError('Data not found!\n'\
                               'Run: OCO_v11MIP_analysis download all')
