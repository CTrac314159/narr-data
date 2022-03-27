# -*- coding: utf-8 -*-
"""
Created on Tue Aug 31 11:48:45 2021

@author: Chris Tracy

This module contains two separate functions for plotting meteorological data from the
NCEP North American Regional Reanalysis (NARR) project. Metadata is available at
https://psl.noaa.gov/data/gridded/data.narr.html . The first function plots the wind speed 
and geopotential height at a vertical pressure level, while the second function plots the 10-meter
wind speed and the 2-meter dewpoint temperature. Additional functions for other variables
and/or pressure levels can be added, as needed.
"""

#Import the necessary global packages
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from metpy.plots import USCOUNTIES

#Short function to convert the time in the file into a string with the year, month, day, hour, and minute.
def time_convert(file):
    from datetime import datetime, timedelta
    
    start = datetime(1800, 1, 1) #In the files, time is in units past 01/01/1800. More info in metadata.
    delta = [timedelta(hours=int(i)) for i in file['time'][:].data] # Time step
    offset = [(start + x) for x in delta]
    new_time = [x.strftime('%Y-%m-%d %H:%M:%S') for x in offset]
    
    return new_time

def weather_plot_hgt(uwnd_file, vwnd_file, hgt_file, level, date, cmap = 'Reds', barb_color = 'darkblue', 
                     extent = None):
    """
    Filenames of the wind component files (first two arguments) are of the following format:
    'uwnd.(year)(month).nc', 'vwnd.(year)(month).nc' (Example: 'uwnd.202203.nc')
    
    Filename of the height file (third argument) is of the following format:
    'hgt.(year)(month).nc' (Example: 'hgt.202203.nc')
    
    Files can be downloaded at: https://downloads.psl.noaa.gov/Datasets/NARR/pressure/
    
    Parameters
    ----------------
    uwnd_file : filepath of the file containing the u-wind components at the pressure levels (string)
    vwnd_file : filepath of the file containing the v-wind components at the pressure levels (string)
    hgt_file  : filepath of the file containing the geopotential heights at the pressure levels (string)
    level     : the pressure level in hPa/mb on which to plot the data (int)
    date      : the desired date and analysis hour, of the format 'Year-Month-Day Hour:Minute:Second'
                The hour needs to be in UTC. Example: '2022-01-01 18:00:00' (string)
    cmap      : the colormap to use for the geopotential height data (string of a Matplotlib colormap)
                Default is 'Reds'.
    barb_color: the color to plot the wind barbs (string of a Matplotlib color type). Default is 'darkblue'.
    extent    : the desired coordinate bounds of the plot in the following order: [west, east, south, north]
                (list). Default is None.

    Returns
    ----------------
    hgt : The gridded geopotential height data at the specified pressure level (2D array)
    ax  : The axis plot object
    """
    
    #Read in the netCDF files and convert the time.
    uwnd_file = Dataset(uwnd_file)
    vwnd_file = Dataset(vwnd_file)
    hgt_file = Dataset(hgt_file)
    time = time_convert(uwnd_file)
    
    #Get the winds and heights at the specified pressure level and date indices. File index order is 
    #(time, level, lat, lon).
    time_where = np.where(np.array(time) == date)[0][0]
    level_where = np.where(uwnd_file['level'][:] == level)[0][0]
    uwnd = uwnd_file['uwnd'][time_where][level_where][:][:].data #In m/s
    vwnd = vwnd_file['vwnd'][time_where][level_where][:][:].data
    hgt = hgt_file['hgt'][time_where][level_where][:][:].data
    lat = uwnd_file['lat'][:].data
    lon = uwnd_file['lon'][:].data
    uwnd = uwnd/0.514 #Convert to knots for the plot
    vwnd = vwnd/0.514
    
    uwnd_file.close() #Close the files
    vwnd_file.close()
    hgt_file.close()
    
    #Original Projection
    # proj = ccrs.LambertConformal(central_longitude=-107.0, central_latitude=50.0, false_easting=5632642.22547, 
    #                              false_northing=4612545.65137, standard_parallels=(50,50))
    
    #Plotting the data
    fig, ax = plt.subplots(figsize = (8, 8), subplot_kw = dict(projection = ccrs.PlateCarree()))
    height_range = np.arange(5910, 6000, 5) #Adjust the range and intervals for the color scale accordingly
    if extent is not None: #If provided, adjust the plot extent accordingly
        ax.set_extent(extent)
    hgt_plot = ax.contourf(lon, lat, hgt, height_range, cmap = cmap, transform = ccrs.PlateCarree())
    ax.barbs(lon[::2, ::2], lat[::2, ::2], uwnd[::2, ::2], vwnd[::2, ::2], barbcolor = barb_color, 
             linewidth = 2.0, transform = ccrs.PlateCarree()) #Plot every other barb on the grid
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.RIVERS)
    ax.add_feature(cfeature.GSHHSFeature(levels = [1]))
    ax.add_feature(USCOUNTIES.with_scale('500k'))
    cbar = plt.colorbar(hgt_plot, shrink = 0.7, ax = ax)
    cbar.set_label(str(level) + ' mb Geopotential Height (meters)')
    
    return hgt, ax

def weather_plot_dew(uwnd_file, vwnd_file, dew_file, date, cmap = 'Greens', barb_color = 'blue', 
                     extent = None):
    """
    Filenames of the wind component files (first two arguments) are of the following format:
    'uwnd.10m.(year).nc', 'vwnd.10m.(year).nc' (Example: 'uwnd.10m.2022.nc')
    
    Filename of the 2-meter dewpoint file (third argument) is of the following format:
    'dpt.2m.(year).nc' (Example: 'dpt.2m.2022.nc')
    
    Files can be downloaded at: https://downloads.psl.noaa.gov/Datasets/NARR/monolevel/
    
    Parameters
    ----------------
    uwnd_file : filepath of the file containing the 10-meter u-wind component (string)
    vwnd_file : filepath of the file containing the 10-meter v-wind component (string)
    dew_file  : filepath of the file containing the 2-meter dewpoint (string)
    date      : the desired date and analysis hour, of the format 'Year-Month-Day Hour:Minute:Second'
                The hour needs to be in UTC. Example: '2022-01-01 18:00:00' (string)
    cmap      : the colormap to use for the 2-meter dewpoint data (string of a Matplotlib colormap)
                Default is 'Greens'.
    barb_color: the color to plot the wind barbs (string of a Matplotlib color type). Default is 'blue'.
    extent    : the desired coordinate bounds of the plot in the following order: [west, east, south, north]
                (list). Default is None.

    Returns
    ----------------
    dew : The gridded 2-meter dewpoint data (2D array)
    ax  : The axis plot object
    """
    
    #Read in the netCDF files and convert the time.
    uwnd_file = Dataset(uwnd_file)
    vwnd_file = Dataset(vwnd_file)
    dew_file = Dataset(dew_file)
    time = time_convert(uwnd_file)
    
    #Get the winds at the specified pressure level and date indices. File index order is (time, level, lat, lon).
    time_where = np.where(np.array(time) == date)[0][0]
    uwnd = uwnd_file['uwnd'][time_where][:][:].data
    vwnd = vwnd_file['vwnd'][time_where][:][:].data
    dew = dew_file['dpt'][time_where][:][:].data #The data is originally in Kelvin
    lat = uwnd_file['lat'][:].data
    lon = uwnd_file['lon'][:].data
    uwnd = uwnd/0.514 #Convert to knots for the plot
    vwnd = vwnd/0.514
    
    uwnd_file.close() #Close the files
    vwnd_file.close()
    dew_file.close()
    
    #Original projection
    # proj = ccrs.LambertConformal(central_longitude=-107.0, central_latitude=50.0, false_easting=5632642.22547, 
    #                              false_northing=4612545.65137, standard_parallels=(50,50))
    
    #Plotting the data. The 2-meter dewpoint is plotted in degrees Celsius.
    fig, ax = plt.subplots(figsize = (8,8), subplot_kw = dict(projection = ccrs.PlateCarree()))
    if extent is not None: #If provided, adjust the plot extent accordingly
        ax.set_extent(extent)
    dew_range = np.arange(18.5, 24.0, 0.3) #Adjust the range and intervals for the color scale accordingly
    dew_plot = ax.contourf(lon, lat, dew - 273.15, dew_range, transform = ccrs.PlateCarree(), cmap = cmap)
    ax.barbs(lon[::2, ::2], lat[::2, ::2], uwnd[::2, ::2], vwnd[::2, ::2], barbcolor = barb_color, 
             linewidth = 2.0, transform = ccrs.PlateCarree()) #Plot every other barb on the grid
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.RIVERS)
    ax.add_feature(cfeature.GSHHSFeature(levels = [1]))
    ax.add_feature(USCOUNTIES.with_scale('500k'))
    cbar = plt.colorbar(dew_plot, shrink = 0.7, ax = ax)
    cbar.set_label('2-Meter Dewpoint (Celsius)')
    
    return dew, ax

#Example usage
# jul19_geo500 = weather_plot_hgt('uwnd.202007.nc', 'vwnd.202007.nc', 'hgt.202007.nc', 
#                                 '2020-07-19 18:00:00', extent = [-89.0, -85.0, 31.0, 36.0])[0]
# jun30_geo500, ax = weather_plot_hgt('uwnd.202106.nc', 'vwnd.202106.nc', 'hgt.202106.nc', 
#                                     date='2021-06-30 18:00:00', cmap = 'Blues', extent = [-89.0, -85.0, 31.0, 36.0])
# jul19_dew = weather_plot_dew('uwnd.10m.2020.nc', 'vwnd.10m.2020.nc', 'dpt.2m.2020.nc', 
#                              '2020-07-19 18:00:00', barb_color = 'red', extent = [-89.0, -85.0, 31.0, 36.0])[0]
# jun30_dew, ax = weather_plot_dew('uwnd.10m.2021.nc', 'vwnd.10m.2021.nc', 'dpt.2m.2021.nc', 
#                                  '2021-06-30 18:00:00', extent = [-89.0, -85.0, 31.0, 36.0])