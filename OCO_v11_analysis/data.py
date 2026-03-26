# Joe Hollowed
# March 2026
#
# This file provides functions for handling data download and location specification

import os
import zipfile
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
    return Path(
        os.getenv('OCO_MIP_DATASETS', f'{Path.home()}/.OCO_v11MIP_analysis')
    )

def download_data(dataset, force=False):
    '''
    Download the data for the specified dataset

    Params
    ------
    dataset : str
        which dataset to download, either being
        'MIP'       : the MIP gridded flux data
        'region'    : the CarbonTracker region definitions
        'aggregate' : the CarbonTracker regional aggregate definitions
        'all'       : all of the above
    '''
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    if(dataset == 'all'):
        MIP_DIR        = download_data('MIP')
        REGION_FILE    = download_data('regions')
        AGGREGATE_FILE = download_data('aggregatge')
        return

    if(dataset == 'MIP'):
        zip_path = f'{cache_dir}/mip.zip'
        extract_dir = f'{cache_dir}/OCO_V11MIP_gridded_fluxes_all_20260127'

        if extract_dir.exists() and not force:
            print(f'Dataset already exists at {extract_dir}')
            return extract_dir

        print('Downloading MIP data...')
        urllib.request.urlretrieve(DATA_URL, zip_path)

        print('Extracting dataset...')
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)

        print(f'Dataset ready at: {extract_dir}')
        return extract_dir

    elif(dataset == 'aggregates' or dataset == 'regions'):
        if(dataset == 'aggregates'): DATA_URL = AGGREGATES_URL
        or dataset == 'regions'):    DATA_URL = REGION_URL
        data_file = f'{cache_dir}/{DATA_URL.split('/')[-1]}'
        
        if data_file.exists() and not force:
            print(f'Dataset already exists at {data_file}')
            return data_file

        print(f'Downloading {dataset} data...')
        urllib.request.urlretrieve(DATA_URL, data_file)

        print(f'Dataset ready at: {data_file}')
        return data_file
