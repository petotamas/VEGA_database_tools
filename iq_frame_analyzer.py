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
    These result are shown in Figure 1. and Figure 2.
    
    In case the CPI index field in the data frame increases with more than one 
    across the file indexes, then CPIs are lost during the data acquisition.
    This information can be extracted from Figure 3. and Figure 4.
    
    The evaluation of the sample delay and the IQ synchronization states 
    over file indexes can be analyzed in Figure 5.
    
    In case the gain values of the receiver channels are not set properly, 
    overdrive may occour during the data acquisition. Figure 6. shows the
    evaluation of the overdrive detect per channel. The total number of
    generated overdrive detection per channel is shown in Figure 7.
    
    Usage:
    ------
    To use the scripts specify the "fname_prefix", "start_index" and
    "stop_index" values in the "P A R A M E T E R S" section.
    
    

"""
import numpy as np
import logging
from iq_header import IQHeader
from matplotlib import pyplot as plt

#-------> P A R A M E T E R S <-------
fname_prefix = "VEGAM20191219K4C0S5/iq/VEGAM20191219K4C0S5_" # Filename without the counter value
start_index = 1042 
stop_index = 2148

# Enable or Disable different analyzes
en_time_stamp_analysis = True 
en_cpi_index_analysis  = True
en_sync_analysis       = True
en_overdrive_analysis  = True
#-----------------------------------------------------------

logging.basicConfig(level=logging.INFO)
time_stamps=[]
cpi_indexes=[]
delay_sync_flags=[]
iq_sync_flags=[]
overdrive_flags = np.empty(0)
for i in np.arange(start_index,stop_index+1,1):
    file_name = (fname_prefix+str(i)+".iqf")
    logging.info("Converting: {:s}".format(file_name))    
    
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
    
    # Check overdrive flag
    if i==start_index:
        M = iq_header.active_ant_chs
        overdrive_flags = np.zeros([M, (stop_index-start_index+1)], dtype=np.int)        
    for m in range(M):        
        if iq_header.adc_overdrive_flags & 1<<m:        
            overdrive_flags[m, i-start_index] = 1
        
    
time_stamps      = np.array(time_stamps)
cpi_indexes      = np.array(cpi_indexes)
delay_sync_flags = np.array(delay_sync_flags)
iq_sync_flags    = np.array(iq_sync_flags)

if en_time_stamp_analysis:
    # Figure 1: File index vs timestamps
    plt.figure(1)
    plt.plot(np.arange(start_index,stop_index+1,1), time_stamps)
    plt.xlabel("File index")
    plt.ylabel("Timestamp")
    plt.grid()
    
    # Figure 2: Timestamp differences between file indexes
    plt.figure(2)
    plt.plot(np.arange(start_index+1,stop_index+1,1),np.diff(time_stamps))
    plt.ylabel("Timestamp difference")
    plt.xlabel("File index")
    plt.grid()

if en_cpi_index_analysis:
    # Figure 3: File index vs cpi index
    plt.figure(3)
    plt.plot(np.arange(start_index,stop_index+1,1), cpi_indexes)
    plt.ylabel("CPI index")
    plt.xlabel("File index")
    plt.grid()
    
    # Figure 4: CPI index differences between file indexes
    plt.figure(4)
    plt.plot(np.arange(start_index+1,stop_index+1,1), np.diff(cpi_indexes))
    plt.ylabel("CPI index")
    plt.xlabel("File index")
    plt.grid()

if en_sync_analysis:
    # Figure 5: IQ and delay sync flag vs file index
    plt.figure(5)
    plt.plot(np.arange(start_index,stop_index+1,1), delay_sync_flags)
    plt.plot(np.arange(start_index,stop_index+1,1), iq_sync_flags)
    plt.ylabel("Sync flag")
    plt.xlabel("File index")
    plt.legend(["Delay sync","IQ sync"])
    plt.grid()

    unique, counts = np.unique(delay_sync_flags, return_counts=True)
    d = dict(zip(unique, counts))
    try:
        logging.info("Delay sync statistics [lost/total]:  [{:d}/{:d}]".format(d[0],d[0]+d[1]))
    except KeyError:
        logging.info("Delay sync statistics [lost/total]:  [{:d}/{:d}]".format(0,d[1]))

if en_overdrive_analysis:    
     # Figure 6: Overdrive flags vs file index
    plt.figure(6)
    labels=[]
    for m in range(M):
        plt.plot(overdrive_flags[m,:])
        labels.append("Channel:"+str(m))
    plt.legend(labels)
    plt.ylabel("Overdrive flag")
    plt.xlabel("File index")
    
    # Figure 7: Number of overdrives per channel
    plt.figure(7)
    plt.bar(np.arange(M),np.sum(overdrive_flags, axis=1))
    plt.ylabel("Number of overdrives")
    plt.xlabel("Channel index")
    