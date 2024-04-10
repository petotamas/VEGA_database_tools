"""
    Description:
    ------------
    Using this script one can analyze the internal states of the data acquisition
    system by interpreting various fields of the IQ frames.
    
    The scripts read all designated IQ data frames and extracts the following 
    information:
        - Time stamp evaluation over time
        - Coherent Processing Interval (CPI) index evaluation over time 
        - Synchronization state evaluation over time
        - Channel overdrive statistics
    
    The analyzation of the timestamp and the CPI index fields could reveal 
    potentail frame or data losses.
    
    In RTL-SDR based DAQ systems, the current timestamp field is equal with 
    Unix Epoch Time of the data block. Consequently data losses can be detected
    only on a per second basis.
    
    In case the CPI index field in the data frame increases with more than one 
    across the file indexes, then CPIs are lost during the data acquisition.
        
    The evaluation of the sample delay and the IQ synchronization states 
    over file indexes can also be analyzed.
    
    In case the gain values of the receiver channels are not set properly, 
    overdrive may occour during the data acquisition. The corresponding Figure
    shows the evaluation of the overdrive detect flag per channel. 
        
    Usage:
    ------
    To use the scripts specify the "fname_prefix", "start_index" and
    "stop_index" values in the "P A R A M E T E R S" section.
    
    

"""
import numpy as np
import logging
from iq_record_tools.iq_header import IQHeader
from iq_record_tools import iq_util
from iq_record_tools.iq_util import path_leaf, sort_iq_frames

import glob
import sys
from os.path import join 

from plotly import graph_objects as go
from plotly.offline import plot
from plot_util.format import format_matplotlib

#-------> P A R A M E T E R S <-------
meas_path         = "MEASUREMENT PATH" 
meas_id = 300

iq_path            = join(join(meas_path,"{:04d}".format(meas_id), "iq"))
res_path           = join(join(meas_path,"{:04d}".format(meas_id), "results"))
iqf_files          = glob.glob(join(iq_path,"*.iqf"))


# Enable or Disable different analyzes
en_time_stamp_analysis  = True 
en_cpi_index_analysis   = True
en_sync_analysis        = True
en_overdrive_analysis   = True
en_frame_type_analysis  = True
en_rx_gain_analysis     = True
#-----------------------------------------------------------



"""
--- Initialize processing ---
"""
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

for handler in logger.handlers[:]:
    logger.removeHandler(handler)

    
sh = logging.StreamHandler()       
logger.addHandler(sh)

fh = logging.FileHandler(join(res_path, "IQ frame analysis.log"))
#fh.setFormatter(formatter)
logger.addHandler(fh)

iqf_files, ignore_list = sort_iq_frames(iqf_files, 
                                    ignore_non_data_frames=True,
                                    ignore_non_synced_frames=False)
logger.warning("Ignored IQ frames: {:d}".format(sum(ignore_list)))
iqf_files = [iqf_file for index, iqf_file in enumerate(iqf_files) if not ignore_list[index]]
logger.info(f"Available IQ frames {len(iqf_files)}")
if not len(iqf_files): sys.exit() # Terminate running if no IQ frames are available after the selection


file_descr = open(iqf_files[0], "rb")
iq_header_bytes = file_descr.read(1024)
iq_header = IQHeader()
iq_header.decode_header(iq_header_bytes)
iq_header.dump_header() 
file_descr.close()

M = iq_header.active_ant_chs


time_stamps=[]
cpi_indexes=[]
delay_sync_flags=[]
iq_sync_flags=[]
overdrive_flags = np.zeros([M, len(iqf_files)], dtype=np.int32)            
frame_types = []
file_indexes = []
rx_gains = np.empty([M,0])

"""
---------------------
P R O C E S S I N G
---------------------    
"""
for file_index, file_name in enumerate(iqf_files):
    logger.info("Processing CPI: {:d}/{:d}".format(int(path_leaf(file_name).split('.')[0]), len(iqf_files)))
    file_indexes.append(int(path_leaf(file_name).split('.')[0]))
    
    
    file_descr = open(file_name, "rb")
    iq_header_bytes = file_descr.read(1024)
    iq_header = IQHeader()
    iq_header.decode_header(iq_header_bytes)
    #iq_header.dump_header() # Enable this to see the IQ header content during conversion      
            
    file_descr.close()
    time_stamps.append(iq_header.time_stamp)
    cpi_indexes.append(iq_header.cpi_index)
    delay_sync_flags.append(iq_header.delay_sync_flag)
    iq_sync_flags.append(iq_header.iq_sync_flag)
    frame_types.append(iq_header.frame_type)
    
    # Check overdrive
    for m in range(M):               
        if iq_header.adc_overdrive_flags & 1<<m:        
            overdrive_flags[m, file_index] = 1     
    rx_gains = np.append(rx_gains, np.array(iq_header.if_gains[0:M]).reshape([M,1]), axis=1)    
        
file_indexes     = np.array(file_indexes)    
time_stamps      = np.array(time_stamps)
cpi_indexes      = np.array(cpi_indexes)
delay_sync_flags = np.array(delay_sync_flags)
iq_sync_flags    = np.array(iq_sync_flags)
frame_types      = np.array(frame_types)

if en_time_stamp_analysis:
    # Figure 1: File index vs timestamps
    fig_1 = go.Figure()
    fig_1 = format_matplotlib(fig_1)
    fig_1.add_trace(go.Scatter(x=file_indexes, y=time_stamps))
    fig_1.update_layout(xaxis=dict(title="File index"))
    fig_1.update_layout(yaxis=dict(title="Timestamp"))
    fig_1.write_html(join(res_path, "Analysis_timestamp.html"))
    
    # Figure 2: Timestamp differences between file indexes
    fig_2 = go.Figure()
    fig_2 = format_matplotlib(fig_2)
    fig_2.add_trace(go.Scatter(x=file_indexes, y=np.diff(time_stamps)/1e6))
    fig_2.update_layout(xaxis=dict(title="File index"))
    fig_2.update_layout(yaxis=dict(title="Timestamp difference [ms]"))
    fig_2.write_html(join(res_path, "Analysis_timestamp_diff.html"))

if en_cpi_index_analysis:
    # Figure 3: File index vs cpi index
    fig_3 = go.Figure()
    fig_3 = format_matplotlib(fig_3)
    fig_3.add_trace(go.Scatter(y=cpi_indexes))
    fig_3.update_layout(xaxis=dict(title="File index"))
    fig_3.update_layout(yaxis=dict(title="CPI index"))
    fig_3.write_html(join(res_path, "Analysis_cpi_indexes.html"))
    
    # Figure 4: CPI index differences between file indexes
    fig_4 = go.Figure()
    fig_4 = format_matplotlib(fig_4)
    fig_4.add_trace(go.Scatter(x=file_indexes, y=np.diff(cpi_indexes)))
    fig_4.update_layout(xaxis=dict(title="File index"))
    fig_4.update_layout(yaxis=dict(title="CPI index difference"))
    fig_4.write_html(join(res_path, "Analysis_cpi_indexe_differences.html"))

if en_sync_analysis:
    # Figure 5: IQ and delay sync flag vs file index
    fig_5 = go.Figure()
    fig_5 = format_matplotlib(fig_5)    
    fig_5.add_trace(go.Scatter(x=file_indexes, y=delay_sync_flags, name="Delay sync"))
    fig_5.add_trace(go.Scatter(x=file_indexes, y=iq_sync_flags, name="IQ sync"))
    fig_5.update_layout(xaxis=dict(title="File index"))
    fig_5.update_layout(yaxis=dict(title="Sync flags"))
    fig_5.write_html(join(res_path, "Analysis_sync_flag.html"))
    unique, counts = np.unique(delay_sync_flags, return_counts=True)
    d = dict(zip(unique, counts))
    try:
        logging.info("Delay sync statistics [lost/total]:  [{:d}/{:d}]".format(d[0],d[0]+d[1]))
    except KeyError:
        pass
        #logging.info("Delay sync statistics [lost/total]:  [{:d}/{:d}]".format(0,d[1]))

if en_overdrive_analysis:    
     # Figure 6: Overdrive flags vs file index
    fig_6 = go.Figure()
    fig_6 = format_matplotlib(fig_6)
    labels=[]
    for m in range(M):
        fig_6.add_trace(go.Scatter(y=overdrive_flags[m,:], name="Channel:"+str(m)))            
    fig_6.update_layout(xaxis=dict(title="File index"))
    fig_6.update_layout(yaxis=dict(title="Overdrive flag"))
    fig_6.write_html(join(res_path, "Analysis_overdrive.html"))

    # Figure 7: Number of overdrives per channel
    #plt.figure(7)
    #plt.bar(np.arange(M),np.sum(overdrive_flags, axis=1))
    #plt.ylabel("Number of overdrives")
    #plt.xlabel("Channel index")

if en_frame_type_analysis:
    fig_8 = go.Figure()
    fig_8 = format_matplotlib(fig_8)
    fig_8.add_trace(go.Scatter(x=file_indexes, y=frame_types))
    fig_8.update_layout(xaxis=dict(title="File index"))
    fig_8.update_layout(yaxis=dict(title="Frame types"))
    fig_8.write_html(join(res_path, "Analysis_frame_types.html"))

if en_rx_gain_analysis:
    fig_9 = go.Figure()
    fig_9 = format_matplotlib(fig_9)
    for m in range(M):
        fig_9.add_trace(go.Scatter(x=file_indexes, y=rx_gains[m,:]/10, name="Channel:"+str(m)))
    fig_9.update_layout(xaxis=dict(title="File index"))
    fig_9.update_layout(yaxis=dict(title="rx gains"))
    fig_9.write_html(join(res_path, "Analysis_rx_gains.html"))
