# Joe Hollowed
# March 2026
#
# This file provides functions for handling data download and location specification

import os
import tarfile
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

def get_mip_dir():
    '''
    Get the location of the MIP data, if exists, else raise error
    '''
    if(MIP_DIR is not None):
        return MIP_DIR
    else:
        raise RuntimeError('MIP data not found\n'\
                           'Run: OCO_v11MIP_analysis download all')

def get_region_file():
    '''
    Get the location of the region data, if exists, else raise error
    '''
    if(REGION_FILE is not None):
        return REGION_FILE
    else:
        raise RuntimeError('Region data not found\n'\
                           'Run: OCO_v11MIP_analysis download all')

def get_aggregate_file():
    '''
    Get the location of the aggregate region data, if exists, else raise error
    '''
    if(AGGREGATE_FILE is not None):
        return AGGREGATE_FILE
    else:
        raise RuntimeError('Aggregate region data not found\n'\
                           'Run: OCO_v11MIP_analysis download all')

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
