#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from iq_header import IQHeader
import numpy as np
import glob
import logging
import os
import sys
from scipy.interpolate import splprep, splev

# Import APRiL package
currentPath = os.path.dirname(os.path.realpath(__file__))
april_path = os.path.join(os.path.join(currentPath, "APRiL"), "pyapril")
sys.path.insert(0, april_path)
from targetParamCalculator import calculate_bistatic_target_parameters

"""
    This scripts extracts the relevant parameters of an observed target tracks from  
    FlightRadar24 CSV data files, fits them to the actual measurement based on the
    timestamps and then calculates the observable bistatic range and Doppler values for
    the observed target for all the records in the measurement.

    The processing steps are the followings:
        1.Determine the first and the last timestamps of the measured data
        2.Select those tracking data points from the reference track data (FlightRadar24),
          that falls within the timeframe of the measurement
        3.Calculate intermediate track points of the reference track with 
          interpolation to get finer resolution. The interpolation is performed
          in a way to ensure that the maximum time difference between two
          track points is 1 second
        4.Assign reference track data points to the measurement records.
          A reference track data point is assigned to a measurement record in case
          the time difference of their time stamps is minimal.
        5.Calculate bistatic range, Doppler frequency and bearing angle for all
          the measurement records based on the assigned reference track data points.
          
    The generate target reference track array will be save to the "target_info"
    folder of the VEGA measurement with ".trt" extension in text format.
    You can use the following sketch to interpret the data columns in this file:   
        
    +------------+-----------+----------+-----------+----------+-------+-----------+-------+---------+---------+
    | Time index | Timestamp | Latitude | Longitude | Altitude | Speed | Direction | Range | Doppler | Azimuth |
    +------------+-----------+----------+-----------+----------+-------+-----------+-------+---------+---------+
    |            |           |          |           |          |       |           |       |         |         |
    +------------+-----------+----------+-----------+----------+-------+-----------+-------+---------+---------+
          

"""
def GPX_interpolate(lat, lon, ele, speed, direct, tstamp, deg):
    """
        Performs interpolation on GPX data including latitude, longitude,
        altitude, speed and direction. The function use the B-Spline curve 
        evaluation of the scipy module.
        
        In case deg=1, linear interpolation will be performed.
        
        Parameters:
        -----------
            :param: lat   : Latitude coordinates of the target track
            :param: lon   : Longitude coordinates of the target track
            :param: ele   : Elevation values of the target track
            :param: speed : Recorded speed values of the target tracks 
            :param: direct: Recorded moving direction values of the target track
            :param: tstamp: Time stamps of the target track
            :param: deg   : Degree of the interpolator
    
            :type: lat    : float numpy array
            :type: lon    : float numpy array
            :type: ele    : float numpy array
            :type: speed  : float numpy array
            :type: direct : float numpy array
            :type: tstamp : int numpy array
            :type: deg    : int
        
        Return values:
        --------------
            Return values are packed into a python list
            
            :return: lat_interp   : Interpolated latitude coordinates of the target track
            :return: lon_interp   : Interpolated longitude coordinates of the target track
            :return: ele_interp   : Interpolated elevation values of the target track
            :return: speed_interp : Interpolated speed values of the target track
            :return: direct_interp: Interpolated direction values of the target track

            :rtype: lat_interp   : float numpy array
            :rtype: lon_interp   : float numpy array
            :rtype: ele_interp   : float numpy array
            :rtype: speed_interp : float numpy array
            :rtype: direct_interp: float numpy array
                
    """
    # Check input data
    if not 1 <= deg <= 5:
        logging.error('Deg out of [1-5] range, skipping interpolation')
        return None
    elif not len(lat) == len(lon) == len(ele) == len(tstamp):
        logging.error('Data input size mismatch, skipping interpolation')
        return None
    else:

        # Calculating time distances between trackpoint
        time_dist = np.zeros(len(tstamp))
        for i in np.arange(1, len(tstamp)):
            time_dist[i] =tstamp[i] - tstamp[i-1]

        # calculate normalized cumulative time distance
        dist_cum_norm = np.cumsum(time_dist)/np.sum(time_dist)
        
        # interpolate spatial data
        data = [lat, lon, ele, speed, direct]

        tck, _ = splprep(x = data, u = dist_cum_norm, k = int(deg), s = 0, nest = len(lat)+deg+1)
        
        res = 1
        u_interp = np.linspace(0, 1, 1+int(np.sum(time_dist)/res)) # Resolution is always one sec
            
        out = splev(u_interp, tck)

        lat_interp = out[0]
        lon_interp = out[1]
        ele_interp = out[2]
        speed_interp = out[3]
        direct_interp = out[4]

        # remove insignificant digits
        lat_interp = np.round(lat_interp*1e6)/1e6
        lon_interp = np.round(lon_interp*1e6)/1e6
        ele_interp = np.round(ele_interp*1e1)/1e1
        

    return(lat_interp, lon_interp, ele_interp, speed_interp, direct_interp)#, tstamp_interp)    
    



"""
---------------------------
                           
    P A R A M E T E R S    
                            
---------------------------
"""
#
# C O N S T A N T S
#
# For GPS data interpolation
EARTH_RADIUS = 6378137.0 # [meters]
# For Doppler calulcation
KNOTS_TO_MPS = 0.51444444444 
FEET_TO_M = 0.3048
c = 299792458

#-----MANDATORY PROCESSING PARAMETERS-----MANDATORY PROCESSING PARAMETERS-----
#-----MANDATORY PROCESSING PARAMETERS-----MANDATORY PROCESSING PARAMETERS-----
#-----MANDATORY PROCESSING PARAMETERS-----MANDATORY PROCESSING PARAMETERS-----
vega_measurement_path=  "/home/petot/WD/Vega/VEGAM20191225HR7C0S0"
#"/media/petot/IQStorage0/VEGAM20191219K4C0S7"

center_frequency = 90.3 *10**6 #634 *10 **6 # [Hz]

# -> Rx, Tx positions
# Elevation: Above Sea Level + Above Ground Level
radar_lat = 46.678105 #47.393033
radar_lon = 18.423188 # 19.287338
radar_ele = 103 + 3 # [m]
radar_bearing = 81 #111 + 6#113 # [deg]

# Illuminator of Opportuniy #1
lat_Szechenyi_hegy = 47.49166667
long_Szechenyi_hegy = 18.97888889
ele_Szechenyi_hegy = 457 + 182

# Illuminator of Opportuniy #2
lat_Harhat_hegy = 47.55027778
long_Harhat_hegy = 19.00138889
ele_Harhat_hegy = 439 + 94

# Illuminator of Opportuniy #3
lat_Szava_utca = 47.46861111
long_Szava_utca = 19.12638889
ele_Szava_utca = 115 + 107

# Illuminator of Opportunity #4
lat_uzd = 46.5911111
long_uzd = 18.5791667
ele_uzd = 204 + 94

ioo_lat = lat_uzd
ioo_lon = long_uzd
ioo_ele = ele_uzd
#-----MANDATORY PROCESSING PARAMETERS-----MANDATORY PROCESSING PARAMETERS-----
#-----MANDATORY PROCESSING PARAMETERS-----MANDATORY PROCESSING PARAMETERS-----
#-----MANDATORY PROCESSING PARAMETERS-----MANDATORY PROCESSING PARAMETERS-----

# -> Preconfiguration
logging.basicConfig(level=logging.INFO)
iq_folder_path       = os.path.join(vega_measurement_path,"iq")
target_info_path     = os.path.join(vega_measurement_path,"target_info")
ref_track_fname_temp = 'target_ref_track_'

iqf_files = glob.glob(os.path.join(iq_folder_path,"*.iqf"))
fr24_csv_files = glob.glob(os.path.join(target_info_path,"*.csv"))

wavelength = c/center_frequency
"""
---------------------------
                           
    P R O C E S S I N G 
                            
---------------------------
"""
# Get the first and the last time indexes and time stamps
for i, file_name in enumerate(iqf_files):
    logging.debug("Reading: {:s}".format(file_name))    
    
    file_descr = open(file_name, "rb")
    iq_header_bytes = file_descr.read(1024)
    iq_header = IQHeader()
    iq_header.decode_header(iq_header_bytes)
    #iq_header.dump_header() # Enable this to see the IQ header content during conversion                  
    file_descr.close()
    file_index = int((file_name.split('_')[-1]).split('.')[0])    
    if i==0:
        start_file_index  = int(file_index)
        stop_file_index   = int(file_index)
        start_time_stamp  = iq_header.time_stamp
        stop_time_stamp   = iq_header.time_stamp
    else:
        if iq_header.time_stamp < start_time_stamp:
            start_time_stamp = iq_header.time_stamp
        if iq_header.time_stamp > stop_time_stamp:
            stop_time_stamp = iq_header.time_stamp
        if file_index < start_file_index:
            start_file_index = file_index
        if file_index > stop_file_index:
            stop_file_index = file_index
            
logging.info("Start file index: {:d}".format(start_file_index))
logging.info("Stop file index: {:d}".format(stop_file_index))
logging.info("First time stamp: {:d}".format(start_time_stamp))
logging.info("Last time stamp: {:d}".format(stop_time_stamp))

# Prepare reference target track array 

target_ref_track_list = []
for target_index, target_gpx_file in enumerate(fr24_csv_files):
    logging.debug("Processing <{:s}> gpx track file".format(target_gpx_file))

    # Allocate array
    target_ref_track = np.zeros([stop_file_index-start_file_index+1, 10], dtype=float) 
    # Fill time index column
    target_ref_track[:,0] = np.arange(start_file_index, stop_file_index+1,1) 
    
    # Fill timestamp column
    fname_prefix = iqf_files[0].split('_')[0]+"_"
    for i in np.arange(start_file_index,stop_file_index+1,1):
        file_name = (fname_prefix+str(i)+".iqf")
        
        file_descr = open(file_name, "rb")
        iq_header_bytes = file_descr.read(1024)
        iq_header = IQHeader()
        iq_header.decode_header(iq_header_bytes)
        #iq_header.dump_header() # Enable this to see the IQ header content during conversion      
        target_ref_track[i-start_file_index, 1] = iq_header.time_stamp    
        file_descr.close()
    
    # Fill Lattitude, Longitude, Altitude, Speed and Direction columns
    """
    Processing Flight Radar 24 track filestarget_ref_track
    Track format:
        Timestamp,UTC,Callsign,Position,Altitude[feet],Speed[Ground Speed in Knots],Direction
        e.g.:1576755262,2019-12-19T11:34:22Z,LOT5KM,"52.142853,20.98628",1525,0,153
    """

    # Load FlightRadar24 CSV file
    ref_target_track_csv = np.loadtxt(target_gpx_file, delimiter= ',', skiprows=1, usecols=[0, 3, 4, 5, 6, 7],
                                      dtype={'names': ('timestamp', 'lat', 'long', 'alt', 'speed', 'dir'),
                                             'formats': (np.int, 'U15', 'U15', np.int, np.int, np.int)})

    target_reference_data=[]
    first_row_flag  = 0
    last_row_index  = 0
    
    for row_index, row in enumerate(ref_target_track_csv):    
        if row[0] >= start_time_stamp and row[0] <= stop_time_stamp:
            if first_row_flag == 0:
                first_row_flag = 1
                row_f = ref_target_track_csv[row_index-1]
                target_reference_data.append([row_f[0],float(row_f[1][1:]), float(row_f[2][:-1]), row_f[3], row_f[4], row_f[5]])
                
            target_reference_data.append([row[0],float(row[1][1:]), float(row[2][:-1]), row[3], row[4], row[5]])
            
            # Store the last row index. 
            # It will be used later to extend the overlaid time interval with plus 1 data row from the reference data
            if last_row_index < row_index:
                last_row_index = row_index
    # Extend overlaid time interval
    row = ref_target_track_csv[last_row_index+1]
    target_reference_data.append([row[0],float(row[1][1:]), float(row[2][:-1]), row[3], row[4], row[5]])
                
    if len(target_reference_data)==0:
        logging.warning("Reference data can not be extracted for target ID: {:d}".format(target_index))
    else:        
        """
        Interpolate missing values
        This code is originated from: https://github.com/remisalmon/GPX_interpolate
        Author: Remi Salmon
        """    
        # Convert reference data to numpy array
        target_reference_data_array= np.array(target_reference_data)
        
        # Perform expanding and interpolation
        (lat_interp, lon_interp, ele_interp, speed_interp, direct_interp) = \
        GPX_interpolate(lat=target_reference_data_array[:,1], 
                        lon=target_reference_data_array[:,2],
                        ele=target_reference_data_array[:,3],
                        speed=target_reference_data_array[:,4],
                        direct=target_reference_data_array[:,5],
                        tstamp=target_reference_data_array[:,0],
                        deg=1)
        interp_target_reference_data = np.zeros([len(lat_interp),6])
        interp_target_reference_data[:,0] = np.arange(target_reference_data_array[0,0], target_reference_data_array[-1,0]+1,1)
        interp_target_reference_data[:,1] = lat_interp
        interp_target_reference_data[:,2] = lon_interp
        interp_target_reference_data[:,3] = ele_interp
        interp_target_reference_data[:,4] = speed_interp
        interp_target_reference_data[:,5] = direct_interp
        
        # Assign interpolated target reference data to the measurements, based on the time stamp difference
        for t in np.arange(0,stop_file_index-start_file_index+1,1):                
            time_diff = abs(interp_target_reference_data[:,0]-target_ref_track[t,1])
            min_tim_diff_index = np.argmin(time_diff)
            
            target_ref_track[t, 2] = interp_target_reference_data[np.argmin(time_diff),1]  # Latitude
            target_ref_track[t, 3] = interp_target_reference_data[np.argmin(time_diff),2]  # Longitude
            target_ref_track[t, 4] = interp_target_reference_data[np.argmin(time_diff),3]  # Altitude
            target_ref_track[t, 5] = interp_target_reference_data[np.argmin(time_diff),4]  # Speed
            target_ref_track[t, 6] = interp_target_reference_data[np.argmin(time_diff),5]  # Direction
        
        # Store the prepared target reference track array
        target_ref_track_list.append(target_ref_track)
        
        """
            Calculate bistatic range and bistatic Doppler frequencies from the 
            positions and the velocities of the target and the location of the radar unit.
        """    
        logging.info("Calcaulating bistatic range and Doppler for target ID: {:d}".format(target_index))

       
        for t in np.arange(0,stop_file_index-start_file_index+1,1):
            
            (Rb, fD, theta) = \
            calculate_bistatic_target_parameters(radar_lat, 
                                                 radar_lon, 
                                                 radar_ele, 
                                                 radar_bearing,
                                                 ioo_lat, 
                                                 ioo_lon, 
                                                 ioo_ele,
                                                 target_lat=target_ref_track[t, 2] , 
                                                 target_lon=target_ref_track[t, 3],
                                                 target_ele=target_ref_track[t, 4]* FEET_TO_M,
                                                 target_speed=target_ref_track[t, 5]*KNOTS_TO_MPS , 
                                                 target_dir=target_ref_track[t, 6],
                                                 wavelength=wavelength)
            target_ref_track[t, 7] =  Rb
            target_ref_track[t, 8] =  fD
            target_ref_track[t, 9] = theta
        logging.info("Saving target reference track array for target ID: {:d}".format(target_index))
        fname = os.path.join(target_info_path, ref_track_fname_temp+str(target_index)+".trt")
        np.savetxt(fname, target_ref_track)
logging.info("Target reference track generation finished")



