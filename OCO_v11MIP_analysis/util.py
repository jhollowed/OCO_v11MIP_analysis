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

def climo_phase_shift(climo1, climo2, return_fits=False, fit_res=100):
    '''
    Get phase shift, in months, between two climatology datasets

    Params
    ------
    climo1, climo2 : xarray DataArray
        1-dimensional climatology datasets with dim 'month'
    get_fits : bool, optional
        whether or not to return the evaluated fitted sine functions. 
        Defaults to False.
    fit_res : int, optional
        temporal resolution increase factor for returned fitted sines, 
        if get_fits=True. Defaults to 100, in which case the fitted 
        sines are evaluated on a temporal grid with spacing decreased
        by a factor of 100 with respect to the input dataset.
        If fit_res=1, then the 'month' dim of the fitted sines will 
        be identical to that of the input data.

    Returns
    -------
    float
        the phase shift between climo1 and climo2, in months
    [xarray DataArray, xarray DataArray], optional
        the fitted sine functions
    '''
    # ----- define sine fitting model
    # freq is constrained to 1/year
    sine_model = lambda x, A, phi, C: A * np.sin((2*np.pi/12) * x + phi) + C
    initial_guess = [1, 0, 0]
    fit_params = {'initial_guess':initial_guess}
    # ----- do fitting
    params1, cov1 = curve_fit(sine_model, climo.month, np.array(climo.values), **fit_params)
    params2, cov2 = curve_fit(sine_model, tm5_climo.month, np.array(tm5_climo[flux]), **fit_params)
    # ----- get phase shift
    phase_shift = (params1[-2]-params2[-2]) / (2*np.pi/12)
    # ----- get fitted forms and return
    if(return_fits):
        if(fit_res == 1):
            months = climo1.month
        else:
            months = np.linspace(climo1.month[0], climo1.month[-1], fit_res)
        sin1 = sine_model(months, *params1)
        sin2 = sine_model(months, *params2)
        return phase_shift, sin1, sin2
    else:
        return phase_shift

# ---------------------------------------------------------------------

def zonal_band_climo(flux, lat1, lat2):
    '''
    Computes the climatology of an zonal-band-aggregated flux.
    See zonal_aggregate() docstrings for parameter descriptions.
     
    Returns
    -------
    xarray DataArray
        The climatology of the zonal-band-integrated flux data, in (Pg C) / year,
        with dim 'month', as well as any dims in the input data other than
        'lat', 'lon', 'time'
    '''
    flux_aggregated = zonal_aggregate(flux, lat1, lat2)
    return ctb.compute_climatology(flux_aggregated)


def regional_climo(flux, region):
    '''
    Computes the climatology of an TransCom region-aggregated flux.
    See region_aggregate() docstrings for parameter descriptions.
    
    Returns
    -------
    xarray DataArray
        The climatology of the region-integrated flux data, in (Pg C) / year,
        with dim 'month', as well as any dims in the input data other than
        'lat', 'lon', 'time'
    '''
    flux_aggregated = region_aggregate(flux, region)
    return ctb.compute_climatology(flux_aggregated)

# ---------------------------------------------------------------------

def mask_on_region(x, region):
    '''
    Mask a dataset on a transcom region (all data outside the region
    becomes NaN)

    Params
    ------
    x : xarray DataArray, or float
        if a DataArray, the data to mask
        if a float, then apply this float uniformly over the region
    region : int, or int list
        The TransCom region(s) to mask on, specified by integer ID
        If an int, mask on this single region
        If a list of ints, mask on the union of the regions

    Returns
    -------
    xarray DataArray
        the masked data, in its input units
    '''
    # ----- get mask
    try:
        masks = []
        for i in range(len(region)):
            masks.append(get_region_mask(region[i]))
        mask = np.logical_or.reduce(masks)
    except TypeError:
        mask = get_region_mask(region)
    mask = mask.where(mask, np.nan).astype(float)

    # ----- mask the data
    if(isinstance(x, float)):
        x = mask * x
    else:
        x.values = mask * x.values
    return x


def mask_on_zonal_band(flux, lat1, lat2):
    '''
    Mask a dataset on a zonal band (all data outside the region
    becomes NaN)

    Params
    ------
    x : xarray DataArray, or float
        if a DataArray, the data to mask
        if a float, then apply this float uniformly over the region
    lat1 : float
        Southern latitude of the band
    lat2: float
        Northern latitude of the band

    Returns
    -------
    xarray DataArray
        the masked data, in its input units
    '''
    # ----- get mask
    mask = x.where((x['lat']>=lat1) & (x['lat']<=lat2), 1.0, np.nan)
    # ----- mask the data
    if(isinstance(x, float)):
        x = mask * x
    else:
        x.values = mask * x.values
    return x

# ---------------------------------------------------------------------

def zonal_aggregate(flux, lat1, lat2, return_gridded=False):
    '''
    Computes a flux agregate across a latitude band

    Params
    ------
    lat1 : float
        Southern latitude of the band
    lat2: float
        Northern latitude of the band

    See docstrings of _horz_aggregate for description of other params and returns
    '''
    mask = (flux.lat >= lat1) & (flux.lat <= lat2)
    return _horz_aggregate(flux, mask, return_gridded)


def region_aggregate(flux, region, return_gridded=False):
    '''
    Computes a flux aggregate across a TransCom region by name or by number

    Params
    ------
    region : int, or int list
        The TransCom region(s) to aggregate over, specified by integer ID
        If an int, aggregate over this single region
        If a list of ints, aggregate over the union of the regions

    See docstrings of _horz_aggregate for description of other params and returns
    '''
    # ---- get mask for specified region
    try:
        masks = []
        for i in range(len(region)):
            masks.append(get_region_mask(region[i]))
        mask = np.logical_or.reduce(masks)
    except TypeError:
        mask = get_region_mask(region)

    # ---- aggregate and return
    return _horz_aggregate(flux, mask, return_gridded)

# ---------------------------------------------------------------------

def _horz_aggregate(flux, grid_mask, return_gridded=False):
    '''
    Computes a flux aggregate across horizontal area specified by a mask

    Params
    ------
    flux : xarray DataArray or Dataset
        The flux data to aggregate, in (g C) / (m^2 day), with dims
        'lat', 'lon'
    grid_mask : xarray DataArray
        boolean mask, matching the data shape in the 'lat', 'lon' dims
    return_gridded : bool, optional
        Whether or not to return the grid-cell-area-weighted masked data in 
        ((Pg C) / year), in its native dimensionality, in addition to the 
        scalar flux aggregate. Defaults to False.
    
    Returns
    -------
    xarray DataArray
        The integrated flux data over the region, in (Pg C) / year, matching any dimensions
        of the input data other than 'lat','lon'
    xarray DataArray, optional
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

    if(return_gridded):
        return flux_aggregate, flux_weighted
    else:
        return flux_aggregate
