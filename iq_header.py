from struct import pack,unpack
import logging

class IQHeader():
    
    def __init__(self):
        
        self.logger = logging.getLogger(__name__)
        self.header_size = 1024 # size in bytes

        self.header_version=0       # uint32_t 
        self.frame_type=0           # uint32_t 
        self.hardware_id=""         # char [16];
        self.unit_id=0              # uint32_t 
        self.active_ant_chs=0;      # uint32_t 
        self.ioo_type=0             # uint32_t 
        self.rf_center_freq=0       # uint64_t 
        self.adc_sampling_freq=0    # uint64_t 
        self.sampling_freq=0        # uint64_t 
        self.cpi_length=0           # uint32_t 
        self.time_stamp=0           # uint64_t 
        self.cpi_index=0            # uint32_t 
        self.ext_integration_cntr=0 # uint64_t 
        self.data_type=0            # uint32_t 
        self.sample_bit_depth=0     # uint32_t 
        self.adc_overdrive_flags=0  # uint32_t 
        self.if_gains=[0]*32        # uint32_t x 32
        self.delay_sync_flag=0      # uint32_t
        self.iq_sync_flag=0         # uint32_t
        self.sync_state=0           # uint32_t
        self.noise_source_state=0   # uint32_t        
        self.reserved=[0]*193       # uint32_t x193

    def decode_header(self, iq_header_byte_array):
        """
            Unpack,decode and store the content of the iq header
        """
        iq_header_list = unpack("II16sIIIQQQIQIQIII"+"I"*32+"IIII"+"I"*193, iq_header_byte_array)
        
        self.header_version       = iq_header_list[0]
        self.frame_type           = iq_header_list[1]
        self.hardware_id          = iq_header_list[2].decode()
        self.unit_id              = iq_header_list[3]
        self.active_ant_chs       = iq_header_list[4]
        self.ioo_type             = iq_header_list[5]
        self.rf_center_freq       = iq_header_list[6]
        self.adc_sampling_freq    = iq_header_list[7]
        self.sampling_freq        = iq_header_list[8]
        self.cpi_length           = iq_header_list[9]
        self.time_stamp           = iq_header_list[10]
        self.cpi_index            = iq_header_list[11]
        self.ext_integration_cntr = iq_header_list[12]
        self.data_type            = iq_header_list[13]
        self.sample_bit_depth     = iq_header_list[14]
        self.adc_overdrive_flags  = iq_header_list[15]
        self.if_gains             = iq_header_list[16:48]
        self.delay_sync_flag      = iq_header_list[48]
        self.iq_sync_flag         = iq_header_list[49]
        self.sync_state           = iq_header_list[50]  
        self.noise_source_state   = iq_header_list[51]

    def encode_header(self):
        """
            Pack the iq header information into a byte array
        """
        iq_header_byte_array=pack("II", self.header_version, self.frame_type)
        iq_header_byte_array+=self.hardware_id.encode()+bytearray(16-len(self.hardware_id.encode()))
        iq_header_byte_array+=pack("IIIQQQIQIQIII",
                                self.unit_id, self.active_ant_chs, self.ioo_type, self.rf_center_freq, self.adc_sampling_freq,
                                self.sampling_freq, self.cpi_length, self.time_stamp, self.cpi_index, self.ext_integration_cntr,
                                self.data_type, self.sample_bit_depth, self.adc_overdrive_flags)
        for m in range(32):
            iq_header_byte_array+=pack("I", self.if_gains[m])

        iq_header_byte_array+=pack("I", self.delay_sync_flag)
        iq_header_byte_array+=pack("I", self.iq_sync_flag)
        iq_header_byte_array+=pack("I", self.sync_state)
        iq_header_byte_array+=pack("I", self.noise_source_state)

        for m in range(193):
            iq_header_byte_array+=pack("I",0)

        return iq_header_byte_array

    def dump_header(self):
        """
            Prints out the content of the header in human readable format
        """
        self.logger.info("Header version: {:d}".format(self.header_version))        
        self.logger.info("Frame type: {:d}".format(self.frame_type))
        self.logger.info("Hardware ID: {:16}".format(self.hardware_id))
        self.logger.info("Unit ID: {:d}".format(self.unit_id))
        self.logger.info("Active antenna channels: {:d}".format(self.active_ant_chs))
        self.logger.info("Illuminator type: {:d}".format(self.ioo_type))
        self.logger.info("RF center frequency: {:.2f} MHz".format(self.rf_center_freq/10**6))
        self.logger.info("ADC sampling frequency: {:.2f} MHz".format(self.adc_sampling_freq/10**6))
        self.logger.info("IQ sampling frequency {:.2f} MHz".format(self.sampling_freq/10**6))
        self.logger.info("CPI length: {:d}".format(self.cpi_length))
        self.logger.info("Time stamp: {:d}".format(self.time_stamp))
        self.logger.info("CPI index: {:d}".format(self.cpi_index))
        self.logger.info("Extended integration counter {:d}".format(self.ext_integration_cntr))
        self.logger.info("Data type: {:d}".format(self.data_type))
        self.logger.info("Sample bit depth: {:d}".format(self.sample_bit_depth))
        self.logger.info("ADC overdrive flags: {:d}".format(self.adc_overdrive_flags))    
        for m in range(32):
            self.logger.info("Ch: {:d} IF gain: {:.1f} dB".format(m, self.if_gains[m]/10))
        self.logger.info("Delay sync  flag: {:d}".format(self.delay_sync_flag))
        self.logger.info("IQ sync  flag: {:d}".format(self.iq_sync_flag))
        self.logger.info("Sync state: {:d}".format(self.sync_state))
        self.logger.info("Noise source state: {:d}".format(self.noise_source_state))
