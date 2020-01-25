"""
    This script converts VEGA database compatible IQ data frames with ".iqf" 
    extendsion to MATLAB interpretable ".mat" files
    The converted MATLAB data file contains both the IQ header and the 
    multichannel IQ data sections.
    
"""
import numpy as np
import scipy.io as io
import logging
from iq_header import IQHeader


#-------> C O N V E R S I O N   P A R A M E T E R S <-------
fname_prefix = "VEGAM20191219K4C0S9_" # Filename without the counter value
start_index = 758 
stop_index = 758
#-----------------------------------------------------------

logging.basicConfig(level=logging.INFO)
for i in np.arange(start_index,stop_index+1,1):
    file_name = (fname_prefix+str(i)+".iqf")
    print("Converting: {:s}".format(file_name))    
    
    file_descr = open(file_name, "rb")
    iq_header_bytes = file_descr.read(1024)
    iq_header = IQHeader()
    iq_header.decode_header(iq_header_bytes)
    iq_header.dump_header() # Enable this to see the IQ header content during conversion      
    
    iq_data_length = int((iq_header.cpi_length * iq_header.active_ant_chs * (2*iq_header.sample_bit_depth))/8)
    iq_data_bytes = file_descr.read(iq_data_length)
        
    file_descr.close()
              
    iq_cf64 = np.frombuffer(iq_data_bytes, dtype=np.complex64).reshape(iq_header.active_ant_chs,
                                                                       iq_header.cpi_length)
    
    matlab_data= dict(header_version       = iq_header.header_version,
                      frame_type           = iq_header.frame_type,           
                      hardware_id          = iq_header.hardware_id,         
                      unit_id              = iq_header.unit_id,
                      active_ant_chs       = iq_header.active_ant_chs,
                      ioo_type             = iq_header.ioo_type,             
                      rf_center_freq       = iq_header.rf_center_freq,       
                      adc_sampling_freq    = iq_header.adc_sampling_freq,    
                      sampling_freq        = iq_header.sampling_freq,
                      cpi_length           = iq_header.cpi_length,           
                      time_stamp           = iq_header.time_stamp,           
                      cpi_index            = iq_header.cpi_index,            
                      ext_integration_cntr = iq_header.ext_integration_cntr, 
                      data_type            = iq_header.data_type,            
                      sample_bit_depth     = iq_header.sample_bit_depth,     
                      adc_overdrive_flags  = iq_header.adc_overdrive_flags,                           
                      delay_sync_flag      = iq_header.delay_sync_flag,  
                      iq_sync_flag         = iq_header.iq_sync_flag,  
                      sync_state           = iq_header.sync_state,  
                      noise_source_state   = iq_header.noise_source_state,     
                      iq_data              = iq_cf64)
    for m in range(32):
        matlab_data['if_gain_{:02.0f}'.format(m)] = iq_header.if_gains[m]
    
    io.savemat((fname_prefix+str(i)+".mat"),matlab_data) # Save to matlab file
    
    
    
