from io import BytesIO
from struct import pack
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import audio
from skoolkit.audio import AudioWriter

def _flatten(elements):
    f = []
    for e in elements:
        if isinstance(e, list):
            f.extend(_flatten(e))
        else:
            f.append(e)
    return f

def mock_write_wav(audio_file, samples, sample_rate):
    return

def mock_moving_average_filter(delays, *args):
    global uf_delays
    uf_delays = delays

class AudioWriterTest(SkoolKitTestCase):
    def _get_audio_data(self, audio_writer, delays, is128k=False):
        audio_stream = BytesIO()
        audio_writer.write_audio(audio_stream, delays, is128k=is128k)
        audio_bytes = bytearray(audio_stream.getvalue())
        audio_stream.close()
        return audio_bytes

    def _check_header(self, audio_bytes, sample_rate=44100):
        length = len(audio_bytes)
        byte_rate = sample_rate * 2
        self.assertEqual(audio_bytes[:4], b'RIFF')
        self.assertEqual(audio_bytes[4:8], pack('<I', length - 8))
        self.assertEqual(audio_bytes[8:12], b'WAVE')
        self.assertEqual(audio_bytes[12:16], b'fmt ')
        self.assertEqual(audio_bytes[16:20], pack('<I', 16)) # fmt chunk length
        self.assertEqual(audio_bytes[20:22], bytes((1, 0)))  # format
        self.assertEqual(audio_bytes[22:24], bytes((1, 0)))  # channels
        self.assertEqual(audio_bytes[24:28], pack('<I', sample_rate))
        self.assertEqual(audio_bytes[28:32], pack('<I', byte_rate))
        self.assertEqual(audio_bytes[32:34], bytes((2, 0)))  # bytes per sample
        self.assertEqual(audio_bytes[34:36], bytes((16, 0))) # bits per sample
        self.assertEqual(audio_bytes[36:40], b'data')
        self.assertEqual(audio_bytes[40:44], pack('<I', length - 44))
        return audio_bytes[44:]

    def test_samples_48k(self):
        audio_writer = AudioWriter()
        audio_bytes = self._get_audio_data(audio_writer, [100] * 4)
        samples = self._check_header(audio_bytes)
        self.assertEqual(samples, b'\x00\x80\x30\x3f\x33\x03\x54\xba\xff\x7f')

    def test_samples_128k(self):
        audio_writer = AudioWriter()
        audio_bytes = self._get_audio_data(audio_writer, [100] * 4, is128k=True)
        samples = self._check_header(audio_bytes)
        self.assertEqual(samples, b'\x00\x80\x32\x43\x42\xfb\x66\xc6')

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_contention_48k(self):
        audio_writer = AudioWriter()
        delays_in = _flatten([13000, [1000] * 31, 500])
        audio_writer.write_audio(None, delays_in, True)
        exp_delays = _flatten([13000, 1000, 1339, [1510] * 27, 1384, 1000, 500])
        self.assertEqual(exp_delays, uf_delays)

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_contention_128k(self):
        audio_writer = AudioWriter()
        delays_in = _flatten([13000, [1000] * 32, 500])
        audio_writer.write_audio(None, delays_in, True, is128k=True)
        exp_delays = _flatten([13000, 1000, 1325, [1510] * 28, 1146, 1000, 500])
        self.assertEqual(exp_delays, uf_delays)

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_interrupts_48k(self):
        audio_writer = AudioWriter()
        delays_in = [10000] * 8
        audio_writer.write_audio(None, delays_in, False, True)
        exp_delays = _flatten([[10000] * 6, 10895, 10000])
        self.assertEqual(exp_delays, uf_delays)

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_interrupts_128k(self):
        audio_writer = AudioWriter()
        delays_in = [10000] * 15
        audio_writer.write_audio(None, delays_in, False, True, is128k=True)
        exp_delays = _flatten([[10000] * 6, 11565, [10000] * 6, 11385, 10000])
        self.assertEqual(exp_delays, uf_delays)

    def test_invalid_option_values(self):
        audio_writer = AudioWriter({
            'ClockSpeed': 'x',
            'ContentionBegin': '@',
            'ContentionEnd': '#',
            'ContentionFactor': '!',
            'FrameDuration': '&',
            'InterruptDelay': '*',
            'SampleRate': 'NaN'
        })

        self.assertEqual(audio_writer.options[0]['ClockSpeed'], 3500000)
        self.assertEqual(audio_writer.options[0]['ContentionBegin'], 14335)
        self.assertEqual(audio_writer.options[0]['ContentionEnd'], 57245)
        self.assertEqual(audio_writer.options[0]['ContentionFactor'], 51)
        self.assertEqual(audio_writer.options[0]['FrameDuration'], 69888)
        self.assertEqual(audio_writer.options[0]['InterruptDelay'], (895,))
        self.assertEqual(audio_writer.options[0]['SampleRate'], 44100)

        self.assertEqual(audio_writer.options[1]['ClockSpeed'], 3546900)
        self.assertEqual(audio_writer.options[1]['ContentionBegin'], 14361)
        self.assertEqual(audio_writer.options[1]['ContentionEnd'], 58035)
        self.assertEqual(audio_writer.options[1]['ContentionFactor'], 51)
        self.assertEqual(audio_writer.options[1]['FrameDuration'], 70908)
        self.assertEqual(audio_writer.options[1]['InterruptDelay'], (1385, 1565))
        self.assertEqual(audio_writer.options[1]['SampleRate'], 44100)

    def test_custom_clock_speed(self):
        audio_writer = AudioWriter({'ClockSpeed': '7000000'})
        audio_bytes = self._get_audio_data(audio_writer, [200] * 4)
        samples = self._check_header(audio_bytes)
        self.assertEqual(samples, b'\x00\x80\xfc\x3d\x06\x04\xb5\xb8\xff\x7f')

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_custom_contention_period(self):
        audio_writer = AudioWriter({'ContentionBegin': '10000', 'ContentionEnd': '20000'})
        delays_in = _flatten([8500, [1000] * 10, 500])
        audio_writer.write_audio(None, delays_in, True)
        exp_delays = _flatten([8500, 1000, 1255, [1510] * 6, 1063, 1000, 500])
        self.assertEqual(exp_delays, uf_delays)

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_custom_contention_factor(self):
        audio_writer = AudioWriter({'ContentionFactor': '62'})
        delays_in = _flatten([13000, [1000] * 29, 500])
        audio_writer.write_audio(None, delays_in, True)
        exp_delays = _flatten([13000, 1000, 1412, [1620] * 25, 1511, 1000, 500])
        self.assertEqual(exp_delays, uf_delays)

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_custom_frame_duration(self):
        audio_writer = AudioWriter({'FrameDuration': '30000'})
        delays_in = [10000] * 4
        audio_writer.write_audio(None, delays_in, False, True)
        exp_delays = [10000, 10000, 10895, 10000]
        self.assertEqual(exp_delays, uf_delays)

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_custom_interrupt_delay(self):
        audio_writer = AudioWriter({'InterruptDelay': '1050,2000'})
        delays_in = [10000] * 15
        audio_writer.write_audio(None, delays_in, False, True)
        exp_delays = _flatten([[10000] * 6, 12000, [10000] * 6, 11050, 10000])
        self.assertEqual(exp_delays, uf_delays)

    def test_custom_sample_rate(self):
        sample_rate = 22050
        audio_writer = AudioWriter({'SampleRate': str(sample_rate)})
        audio_bytes = self._get_audio_data(audio_writer, [200] * 4)
        samples = self._check_header(audio_bytes, sample_rate)
        self.assertEqual(samples, b'\x00\x80\xfc\x3d\x06\x04\xb5\xb8\xff\x7f')

    @patch.object(audio, 'moving_average_filter', mock_moving_average_filter)
    @patch.object(audio, 'write_wav', mock_write_wav)
    def test_offset(self):
        audio_writer = AudioWriter()
        delays_in = [10000] * 3
        offset = 50000
        audio_writer.write_audio(None, delays_in, False, True, offset)
        exp_delays = [10000, 10895, 10000]
        self.assertEqual(exp_delays, uf_delays)
