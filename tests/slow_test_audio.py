import hashlib
import tempfile
import wave

from skoolkittest import SkoolKitTestCase
from skoolkit import tap2sna, trace

class AudioTest(SkoolKitTestCase):
    def _test_audio(self, url, tapname, tapsum, tap2sna_options, trace_options, nsamples, samples_md5):
        with tempfile.TemporaryDirectory() as d:
            z80file = f'{d}/{tapname[:-4]}.z80'
            wavfile = f'{d}/{tapname[:-4]}.wav'
            tap2sna.main(('--tape-name', tapname, '--tape-sum', tapsum, *tap2sna_options, url, z80file))
            trace.main((*trace_options, '-M', '35000000', z80file, wavfile))
            with wave.open(wavfile, 'rb') as wav:
                self.assertEqual(wav.getnchannels(), 1)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertEqual(wav.getframerate(), 44100)
                self.assertEqual(wav.getnframes(), nsamples)
                md5sum = hashlib.md5(wav.readframes(nsamples)).hexdigest()
                self.assertEqual(md5sum, samples_md5)

    def test_agent_x_ii_128k(self):
        self._test_audio(
            'https://worldofspectrum.net/pub/sinclair/games/a/AgentXII.tzx.zip',
            'Agent X 2.tzx',
            '9a7503e49f703fe48148e37698a03752',
            ('--start', '32785', '-c', 'machine=128'),
            ('--ay', '--beeper'),
            435352,
            '6a95e402a862a21db20316be9beb2d08'
        )

    def test_chase_hq_128k(self):
        self._test_audio(
            'https://worldofspectrum.net/pub/sinclair/games/c/ChaseH.Q..tzx.zip',
            'Chase HQ - Side 1.tzx',
            '2bfca22594217e032d1a59d56f57179d',
            ('--start', '60623', '-c', 'machine=128'),
            ['--ay'],
            435352,
            '405c8e675f3331b02f7b4057fd1a71b9'
        )

    def test_fairlight(self):
        self._test_audio(
            'https://worldofspectrum.net/pub/sinclair/games/f/Fairlight48V1.tzx.zip',
            'Fairlight - 48k - Release 1.tzx',
            '1dba2ac53fd25f4cc1065e18e31a7b96',
            ('--start', '49164'),
            (),
            440988,
            '3b758cb08820883b5542e90fc119327d'
        )

    def test_manic_miner(self):
        self._test_audio(
            'https://worldofspectrum.org/pub/sinclair/games/m/ManicMiner.tzx.zip',
            'Manic Miner.tzx',
            '2750ccb6c240d14516c448e94f8d200e',
            ('--start', '37596'),
            (),
            440948,
            '57e1a2068caaa23247d2942a163374d5'
        )

    def test_raw_recruit_128k(self):
        self._test_audio(
            'https://worldofspectrum.net/pub/sinclair/games/r/RawRecruit.tzx.zip',
            'Raw Recruit.tzx',
            'de47e67945a6df7c58913bd7d4128be5',
            ('--start', '40627', '-c', 'machine=128'),
            ('--ay', '--beeper'),
            435352,
            'b7d10f4de0b27c9691f0e0851c69e81c'
        )

    def test_read_heat_128k(self):
        self._test_audio(
            'https://worldofspectrum.net/pub/sinclair/games/r/RedHeat.tzx.zip',
            'Red Heat - Side 1.tzx',
            'd527d8596b8c177b3299aeb1e8de5d38',
            ('--start', '23459', '-c', 'machine=128'),
            ('--ay', '--beeper'),
            433394,
            '769512f971921e25be836986ca05a27e'
        )

    def test_trantor_the_last_stormtrooper(self):
        self._test_audio(
            'https://worldofspectrum.net/pub/sinclair/games/t/Trantor-TheLastStormtrooper.tzx.zip',
            'TRANTOR.TZX',
            '1021cd71d3a594f39cd92cf4b382e9ff',
            ('--start', '50080'),
            (),
            440223,
            '0e9d27cf3c928148e7ea3b809207dc36'
        )
