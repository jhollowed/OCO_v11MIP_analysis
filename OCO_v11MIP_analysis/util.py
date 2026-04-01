# Joe Hollowed
# March 2026
#
# This file provides utility functions and tools for the MIP analysis

import sys
import pdb
import glob
import numpy as np
import xarray as xr
from datetime import datetime
from scipy.optimize import curve_fit

from .data_io import *
from .constants import *

sys.path.insert(1, '/Users/joe/repos/climate_utils')
import climate_toolbox as ctb

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------

def lat_band_aggregate(flux, lat1, lat2, return_gridded=False):
    '''
    Computes a flux agregate across a latitude band

    Params
    ------
    flux : xarray DataArray or Dataset
        The flux data to aggregate, in (g C) / (m^2 day)
    lat1 : float
        Southern latitude of the band
    lat2: float
        Northern latitude of the band
    return_gridded : bool, optional
        Whether or not to return the grid-cell-area-weighted masked data in 
        ((Pg C) / year), in its native dimensionality, in addition to the 
        scalar flux aggregate. Defaults to False.

    Returns
    -------
    The flux data aggregated over the latittude band, in (Pg C) / year
    '''
    mask = (flux.lat >= lat1) & (flux.lat <= lat2)
    return _horz_aggregate(flux, mask, return_gridded)

# ---------------------------------------------------------------------

def region_aggregate(flux, region, return_gridded=False):
    '''
    Computes a flux aggregate across a TransCom region by name or by number

    Params
    ------
    flux : xarray DataArray or Dataset
        The flux data to aggregate, in (g C) / (m^2 day)
    region : int
        The TransCom region to aggregate over, specified by it's integer ID
    return_gridded : bool, optional
        Whether or not to return the grid-cell-area-weighted masked data in 
        ((Pg C) / year), in its native dimensionality, in addition to the 
        scalar flux aggregate. Defaults to False.
    
    Returns
    -------
    The flux data aggregated over the latittude band, in (Pg C) / year
    '''
    # ---- get region mapping
    region_map  = to_latlon(xr.open_dataset(get_region_file()))
    tc_regions  = region_map['transcom_regions']
    # ---- get mask for specified region
    mask = tc_regions == region
    # ---- aggregate and return
    return _horz_aggregate(flux, mask, return_gridded)

# ---------------------------------------------------------------------

def _horz_aggregate(flux, grid_mask, return_gridded=False):
    '''
    Computes a flux aggregate across horizontal area specified by a mask

    Params
    ------
    flux : xarray DataArray or Dataset
        The flux data to aggregate, in (g C) / (m^2 day)
    grid_mask : xarray DataArray
        boolean mask, matching the data shape in the 'latitude', 'longitude' dims
    return_gridded : bool, optional
        Whether or not to return the grid-cell-area-weighted masked data in 
        ((Pg C) / year), in its native dimensionality, in addition to the 
        scalar flux aggregate. Defaults to False.
    
    Returns
    -------
    float
        The integrated flux data over the region, in (Pg C) / year
    xarray DataArray
        The area-weighted flux data in (Pg C) / year, matching the input dimensions
    '''
    
    # first mask the data
    flux_masked = flux.where(grid_mask)

    # get grid cell areas
    grid_cell_areas = to_latlon(xr.open_dataset(get_region_file())['grid_cell_area'])
    grid_cell_areas = grid_cell_areas.where(grid_mask)
    
    # now aggregate by:
    # 1. multiplying the flux density by the grid cell area 
    #    ((g C) / (m2 day)) -> ((g C) / day)
    # 2. converting per-day -> per-year, and g->Pg
    # 3. summing the flux per-grid-cell
    
    # weight by cell areas and sum
    flux_weighted  = flux_masked * grid_cell_areas
    
    # convert from g/day to Pg/year
    dpm = flux_weighted.time.dt.days_in_month
    flux_weighted *= (dpm * 12) * g2Pg

    # integrate over lat,lon
    flux_aggregate = flux_weighted.sum(('lat', 'lon'))

    #gretchen mentioned ken schultx is involved with this; if its more useful or productive for me to talk to him direclty then I'm happy to do that 

    if(return_gridded):
        return flux_aggregate, flux_weighted
    else:
        return flux_aggregate
