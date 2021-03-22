from iq_header import IQHeader
import numpy as np
def load_iq(file_name):
    """
        Description: 
        ------------
        Load IQ frame and prepare the payload section for further processings
        
        Parameters:
        -----------
        :param: file_name: Filename which stores the recorded IQ frame with 
                          ".iqf" extension.
        :type: file_name : string
        
        Return values:
        --------------
        :return: iq_samples: IQ sample matrix extracted from the IQ frame
        :return: iq_header : IQ header extracted from the IQ frame
        
        :rtype: iq_samples: M x N complex numpy array 
        :rtype: iq_header : IQ header object 
            
    """
    
    file_descr = open(file_name, "rb")
    iq_header_bytes = file_descr.read(1024)
    iq_header = IQHeader()
    iq_header.decode_header(iq_header_bytes)

    iq_data_length = int((iq_header.cpi_length * iq_header.active_ant_chs * (2*iq_header.sample_bit_depth))/8)
    iq_data_bytes = file_descr.read(iq_data_length)

    file_descr.close()
          
    iq_cf64 = np.frombuffer(iq_data_bytes, dtype=np.complex64).reshape(iq_header.active_ant_chs, iq_header.cpi_length)
    iq_samples = iq_cf64.copy()
    
    return iq_samples, iq_header
