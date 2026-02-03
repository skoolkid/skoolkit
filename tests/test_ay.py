from io import BytesIO
from struct import pack

from skoolkittest import SkoolKitTestCase
from skoolkit.ay import SAMPLE_RATE, AYAudioWriter, Options

class AudioWriterTest(SkoolKitTestCase):
    def _get_audio_data(self, audio_writer, records, options):
        audio_stream = BytesIO()
        audio_writer.write_audio(audio_stream, records, options)
        audio_bytes = bytearray(audio_stream.getvalue())
        audio_stream.close()
        return audio_bytes

    def _check_header(self, audio_bytes, options, config=None):
        length = len(audio_bytes)
        sample_rate = config.get(SAMPLE_RATE, 44100) if config else 44100
        channels = 2
        bits_per_sample = 16
        bytes_per_sample = (bits_per_sample // 8) * channels
        byte_rate = bytes_per_sample * sample_rate
        self.assertEqual(audio_bytes[:4], b'RIFF')
        self.assertEqual(audio_bytes[4:8], pack('<I', length - 8))
        self.assertEqual(audio_bytes[8:12], b'WAVE')
        self.assertEqual(audio_bytes[12:16], b'fmt ')
        self.assertEqual(audio_bytes[16:20], pack('<I', 16)) # fmt chunk length
        self.assertEqual(audio_bytes[20:22], bytes((1, 0)))  # format
        self.assertEqual(audio_bytes[22:24], bytes((channels, 0)))
        self.assertEqual(audio_bytes[24:28], pack('<I', sample_rate))
        self.assertEqual(audio_bytes[28:32], pack('<I', byte_rate))
        self.assertEqual(audio_bytes[32:34], bytes((bytes_per_sample, 0)))
        self.assertEqual(audio_bytes[34:36], bytes((bits_per_sample, 0)))
        self.assertEqual(audio_bytes[36:40], b'data')
        self.assertEqual(audio_bytes[40:44], pack('<I', length - 44))
        return audio_bytes[44:]

    def test_default_options(self):
        options = Options()
        records = (
            (0, 7, 0b11111000), # Mixer (enable tone for channels A, B, C)
            (4, 0, 0xFC),       # Channel A fine pitch
            (8, 8, 0x0F),       # Channel A volume (maximum)
            (12, 2, 0xFD),      # Channel B fine pitch
            (16, 9, 0x0F),      # Channel B volume (maximum)
            (20, 4, 0xFE),      # Channel C fine pitch
            (24, 10, 0x0F),     # Channel C volume (maximum)
            (70908, 8, 0x00),   # Channel A volume (off)
        )
        audio_bytes = self._get_audio_data(AYAudioWriter(), records, options)
        samples = self._check_header(audio_bytes, options)
        self.assertEqual(len(samples), 3528)
        self.assertEqual(samples[:8], b'\x00\x80\x00\x80\x00\x80\x00\x80')
        self.assertEqual(samples[3520:], b'\xff\x3f\xff\x3f\xff\x3f\xff\x3f')

    def test_beeper_starts_before_ay(self):
        options = Options(beeper=True)
        log = {
            70908: (7, 0b11111110), # Mixer (enable tone for channel A)
            70912: (0, 0xFC),       # Channel A fine pitch
            70916: (8, 0x0F),       # Channel A volume (maximum)
            141816: (8, 0x00),      # Channel A volume (off)
        }
        for i in range(0, 71000, 1000):
            log[i] = (255, 0)
        records = [(t, *log[t]) for t in sorted(log)]
        audio_bytes = self._get_audio_data(AYAudioWriter(), records, options)
        samples = self._check_header(audio_bytes, options)
        self.assertEqual(len(samples), 7056)
        self.assertEqual(samples[:8], b'\x00\x80\x00\x80\x00\x80\x00\x80')
        self.assertEqual(samples[7048:], b'\x00\x80\x00\x80\x00\x80\x00\x80')

    def test_beeper_starts_after_ay(self):
        options = Options(beeper=True)
        log = {
            0: (7, 0b11111110), # Mixer (enable tone for channel A)
            4: (0, 0xFC),       # Channel A fine pitch
            8: (8, 0x0F),       # Channel A volume (maximum)
            70908: (8, 0x00),   # Channel A volume (off)
        }
        for i in range(500, 71000, 500):
            log[i] = (255, 0)
        records = [(t, *log[t]) for t in sorted(log)]
        audio_bytes = self._get_audio_data(AYAudioWriter(), records, options)
        samples = self._check_header(audio_bytes, options)
        self.assertEqual(len(samples), 3528)
        self.assertEqual(samples[:8], b'\x00\x80\x00\x80\x00\x80\x00\x80')
        self.assertEqual(samples[3520:], b'\x00\xc0\x00\x80\x00\xc0\x00\x80')

    def test_ay_res(self):
        options = Options(ay_res=2000)
        log = {
            0: (7, 0b11111110), # Mixer (enable tone for channel A)
            4: (0, 0xFC),       # Channel A fine pitch
            8: (8, 0x0F),       # Channel A volume (maximum)
            70908: (8, 0x00),   # Channel A volume (off)
        }
        for i in range(2000, 70000, 2000):
            log[i] = (13, (i // 2000) % 16) # Envelope
        records = [(t, *log[t]) for t in sorted(log)]
        audio_bytes = self._get_audio_data(AYAudioWriter(), records, options)
        samples = self._check_header(audio_bytes, options)
        self.assertEqual(len(samples), 3480)
        self.assertEqual(samples[:8], b'\x00\x80\x00\x80\x00\x80\x00\x80')
        self.assertEqual(samples[3472:], b'\x00\x00\x00\x80\x00\x00\x00\x80')

    def test_sample_rate(self):
        config = {SAMPLE_RATE: 11025}
        options = Options()
        records = (
            (0, 7, 0b11111110), # Mixer (enable tone for channel A)
            (4, 0, 0xFC),       # Channel A fine pitch
            (8, 8, 0x0F),       # Channel A volume (maximum)
            (70908, 8, 0x00),   # Channel A volume (off)
        )
        audio_bytes = self._get_audio_data(AYAudioWriter(config), records, options)
        samples = self._check_header(audio_bytes, options, config)
        self.assertEqual(len(samples), 880)
        self.assertEqual(samples[:8], b'\x00\x80\x00\x80\x00\x80\x00\x80')
        self.assertEqual(samples[872:], b'\x00\x80\x00\x80\x00\x80\x00\x80')

    def test_invalid_sample_rate(self):
        ay_audio_writer = AYAudioWriter({SAMPLE_RATE: 'NaN'})
        self.assertEqual(ay_audio_writer.options[SAMPLE_RATE], 44100)
