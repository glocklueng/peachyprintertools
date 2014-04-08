import pyaudio
import numpy as np
import math
import time

human_readable_depths = {
            pyaudio.paFloat32 : '32 bit Floating Point', 
            pyaudio.paInt32 : '32 bit',
            pyaudio.paInt24 : '24 bit',
            pyaudio.paInt16 : '16 bit',
            pyaudio.paInt8 : '8 bit',
            }

class AudioSetup(object):
    def __init__(self ):
        self._supported_rates = [ 44100, 48000, 96000, 192000]
        self._supported_depths = [ pyaudio.paFloat32, pyaudio.paInt32, pyaudio.paInt24, pyaudio.paInt16, pyaudio.paInt8, ]
    def _get_depths_for_rate(self, pa, device_id, sample_rate, io_type):
        depths = []
        for format in  self._supported_depths:
            try:
                if io_type == 'input':
                    if pa.is_format_supported(sample_rate,input_device=device_id, input_channels=1, input_format = format):
                        depths.append(format)
                else:
                    if pa.is_format_supported(sample_rate,output_device = device_id, output_channels=2, output_format= format):
                        depths.append(format)
            except ValueError:
                pass
        return depths

    def get_valid_sampling_options(self):
        pa = None
        inputs = []
        outputs =  []
        try:
            pa = pyaudio.PyAudio()
            input_device = pa.get_default_input_device_info()
            output_device = pa.get_default_output_device_info()
            input_device_id = input_device['index']
            output_device_id = output_device['index']
            for sample_rate in self._supported_rates:
                if input_device['maxInputChannels'] >= 1:
                    for depth in self._get_depths_for_rate(pa,input_device_id,sample_rate,'input'):
                        inputs.append({'sample_rate': sample_rate, 'depth' : depth})
                if input_device['maxOutputChannels'] >= 2:
                    for depth in self._get_depths_for_rate(pa,output_device_id,sample_rate,'output'):
                        outputs.append({'sample_rate': sample_rate, 'depth' : depth})
        finally:
            if pa:
                pa.terminate()
        return { 'input' : inputs, 'output' : outputs}


class AudioWriter(object):
    def __init__(self, sample_rate, bit_depth):
        self._sample_rate = sample_rate
        self._bit_depth = bit_depth
        self._set_format_from_depth(bit_depth)
        self._max_bit_value = math.pow(2, bit_depth - 1) - 1.0
        self._pa = pyaudio.PyAudio()
        self._buffer_size = self._sample_rate / 8

        if not self._configuration_supported(self._sample_rate,self._format):
            raise Exception("Audio configuration not supported; Sample Rate: %s; Sample Bits: %s " % (self._sample_rate, self._bit_depth) )
        self._outstream = self._pa.open(
            format=self._format,
            channels = 2,
            rate=self._sample_rate,
            output=True,
            frames_per_buffer=self._buffer_size 
            )
        self._outstream.start_stream()

    def _configuration_supported(self, sample_rate, format):
        device_info = self._pa.get_default_host_api_info()
        default_device_id = device_info['defaultInputDevice']
        supported = self._pa.is_format_supported(sample_rate,output_device=default_device_id,output_channels=2,output_format=format)
        return supported

    def _set_format_from_depth(self,depth):
        if depth == 8:
            self._format =  pyaudio.paInt8
            self._max_bit_value = math.pow(2, depth - 1) - 1.0
        elif depth == 16:
            self._format =  pyaudio.paInt16
            self._max_bit_value = math.pow(2, depth - 1) - 1.0
        elif depth == 24:
            self._format =  pyaudio.paInt24
            self._max_bit_value = math.pow(2, depth - 1) - 1.0
        elif depth == 32:
            self._format =  pyaudio.paFloat32
            self._max_bit_value = 1.0
        else:
            raise Exception("Bit depth %s specified is not supported" % depth)

    def _wait_for_buffer(self,current_buffer_size):
        if current_buffer_size < self._buffer_size / 8.0:
            time.sleep(self._buffer_size * 1.0 / self._sample_rate * 1.0 / 8.0)

    def write_chunk(self, chunk):
        for audio in chunk:
            frames = self._to_frame(audio)
            buffer_size = self._outstream.get_write_available()
            self._wait_for_buffer(buffer_size)
            self._outstream.write(frames)


    def _to_frame(self, values):
        if (self._format == pyaudio.paFloat32):
            return values.astype(np.dtype('f4')).tostring()
        else:
            values = np.rint( values * self._max_bit_value)
            return  values.astype(np.dtype('<i2')).tostring()

    #TODO JT 2014-04-01 - Ctrl-C hook
    def close(self):
        self._outstream.stop_stream()
        self._pa.terminate()
