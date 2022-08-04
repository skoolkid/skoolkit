from io import BytesIO

from skoolkittest import SkoolKitTestCase
from skoolkit.audio import AudioWriter

def _int32(num):
    return bytes((num & 255, (num >> 8) & 255, (num >> 16) & 255, num >> 24))

def _flatten(elements):
    f = []
    for e in elements:
        if isinstance(e, list):
            f.extend(_flatten(e))
        else:
            f.append(e)
    return f

class TestAudioWriter(AudioWriter):
    def _delays_to_samples(self, delays, max_amplitude=0):
        self.delays = delays

    def _write_wav(self, audio_file, samples):
        return

class AudioWriterTest(SkoolKitTestCase):
    def _get_audio_data(self, audio_writer, delays):
        audio_stream = BytesIO()
        audio_writer.write_audio(audio_stream, delays)
        audio_bytes = bytearray(audio_stream.getvalue())
        audio_stream.close()
        return audio_bytes

    def _check_header(self, audio_bytes, sample_rate=44100):
        length = len(audio_bytes)
        byte_rate = sample_rate * 2
        self.assertEqual(audio_bytes[:4], b'RIFF')
        self.assertEqual(audio_bytes[4:8], _int32(length - 8))
        self.assertEqual(audio_bytes[8:12], b'WAVE')
        self.assertEqual(audio_bytes[12:16], b'fmt ')
        self.assertEqual(audio_bytes[16:20], _int32(16))     # fmt chunk length
        self.assertEqual(audio_bytes[20:22], bytes((1, 0)))  # format
        self.assertEqual(audio_bytes[22:24], bytes((1, 0)))  # channels
        self.assertEqual(audio_bytes[24:28], _int32(sample_rate))
        self.assertEqual(audio_bytes[28:32], _int32(byte_rate))
        self.assertEqual(audio_bytes[32:34], bytes((2, 0)))  # bytes per sample
        self.assertEqual(audio_bytes[34:36], bytes((16, 0))) # bits per sample
        self.assertEqual(audio_bytes[36:40], b'data')
        self.assertEqual(audio_bytes[40:44], _int32(length - 44))
        return audio_bytes[44:]

    def test_samples(self):
        audio_writer = AudioWriter()
        audio_bytes = self._get_audio_data(audio_writer, [100] * 4)
        samples = self._check_header(audio_bytes)
        self.assertEqual(samples, b'\x00\x00\xff\x7f\x00\x80\xff\x7f\x00\x80\x83\xe6')

    def test_contention(self):
        audio_writer = TestAudioWriter()
        delays_in = _flatten([13000, [1000] * 31, 500])
        audio_writer.write_audio(None, delays_in, True)
        exp_delays_out = _flatten([13000, 1000, 1337, [1512] * 27, 1369, 1000, 500])
        self.assertEqual(exp_delays_out, audio_writer.delays)

    def test_interrupts(self):
        audio_writer = TestAudioWriter()
        delays_in = [10000] * 8
        audio_writer.write_audio(None, delays_in, False, True)
        exp_delays_out = _flatten([[10000] * 6, 10942, 10000])
        self.assertEqual(exp_delays_out, audio_writer.delays)

    def test_invalid_option_values(self):
        audio_writer = AudioWriter({
            'ClockSpeed': 'x',
            'SampleRate': 'NaN'
        })
        self.assertEqual(audio_writer.options['ClockSpeed'], 3500000)
        self.assertEqual(audio_writer.options['SampleRate'], 44100)

    def test_custom_clock_speed(self):
        clock_speed = 7000000
        audio_writer = AudioWriter({'ClockSpeed': clock_speed})
        audio_bytes = self._get_audio_data(audio_writer, [100] * 4)
        samples = self._check_header(audio_bytes)
        self.assertEqual(samples, b'\x00\x00\x00\x80\x00\x80')

    def test_custom_sample_rate(self):
        sample_rate = 22050
        audio_writer = AudioWriter({'SampleRate': sample_rate})
        audio_bytes = self._get_audio_data(audio_writer, [100] * 4)
        samples = self._check_header(audio_bytes, sample_rate)
        self.assertEqual(samples, b'\x00\x00\x00\x80\x00\x80')
