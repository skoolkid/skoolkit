from io import BytesIO

from skoolkittest import SkoolKitTestCase
from skoolkit.audio import AudioWriter

def _int32(num):
    return bytes((num & 255, (num >> 8) & 255, (num >> 16) & 255, num >> 24))

class AudioWriterTest(SkoolKitTestCase):
    def _get_audio_data(self, audio_writer, delays):
        audio_stream = BytesIO()
        audio_writer.write_audio(audio_stream, delays)
        audio_bytes = bytearray(audio_stream.getvalue())
        audio_stream.close()
        return audio_bytes

    def _check_header(self, audio_bytes):
        length = len(audio_bytes)
        self.assertEqual(audio_bytes[:4], b'RIFF')
        self.assertEqual(audio_bytes[4:8], _int32(length - 8))
        self.assertEqual(audio_bytes[8:12], b'WAVE')
        self.assertEqual(audio_bytes[12:16], b'fmt ')
        self.assertEqual(audio_bytes[16:20], _int32(16))     # fmt chunk length
        self.assertEqual(audio_bytes[20:22], bytes((1, 0)))  # format
        self.assertEqual(audio_bytes[22:24], bytes((1, 0)))  # channels
        self.assertEqual(audio_bytes[24:28], _int32(44100))  # sample rate
        self.assertEqual(audio_bytes[28:32], _int32(88200))  # byte rate
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
