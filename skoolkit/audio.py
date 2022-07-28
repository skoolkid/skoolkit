# Copyright 2013, 2014, 2022 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

import math

CLOCK_SPEED = 3500000
MAX_AMPLITUDE = 65536
SAMPLE_RATE = 44100

class AudioWriter:
    def write_audio(self, audio_file, delays, sample_rate=SAMPLE_RATE):
        samples = self._delays_to_samples(delays, sample_rate)
        self._write_wav(audio_file, samples, sample_rate)

    def _delays_to_samples(self, delays, sample_rate, max_amplitude=MAX_AMPLITUDE):
        sample_delay = CLOCK_SPEED / sample_rate
        samples = []
        direction = 1
        i = 0
        d0 = 0
        d1 = delays[i]
        t = 0
        while 1:
            while t >= d1:
                i += 1
                if i >= len(delays):
                    break
                d0 = d1
                d1 += delays[i]
                direction *= -1
            if i >= len(delays):
                break
            sample = direction * int(max_amplitude * math.sin(math.pi * (t - d0) / (d1 - d0)))
            if sample > 32767:
                sample = 32767
            elif sample < -32768:
                sample = 32768
            elif sample < 0:
                sample += 65536
            samples.append(sample)
            t += sample_delay
        return samples

    def _to_int32(self, num):
        return (num & 255, (num >> 8) & 255, (num >> 16) & 255, num >> 24)

    def _write_wav(self, audio_file, samples, sample_rate):
        data_length = 2 * len(samples)
        header = bytearray()
        header.extend(b'RIFF')
        header.extend(self._to_int32(36 + data_length))
        header.extend(b'WAVEfmt ')
        header.extend(self._to_int32(16))              # length of fmt chunk
        header.extend((1, 0))                          # format (1=PCM)
        header.extend((1, 0))                          # channels
        header.extend(self._to_int32(sample_rate))     # sample rate
        header.extend(self._to_int32(sample_rate * 2)) # byte rate
        header.extend((2, 0))                          # bytes per sample
        header.extend((16, 0))                         # bits per sample
        header.extend(b'data')
        header.extend(self._to_int32(data_length))     # length of data chunk
        audio_file.write(header)
        for sample in samples:
            audio_file.write(bytes((sample & 255, sample // 256)))
