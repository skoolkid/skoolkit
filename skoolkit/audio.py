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

CLOCK_SPEED = 'ClockSpeed'
CONTENTION_BEGIN = 'ContentionBegin'
CONTENTION_END = 'ContentionEnd'
CONTENTION_FACTOR = 'ContentionFactor'
FRAME_DURATION = 'FrameDuration'
INTERRUPT_DELAY = 'InterruptDelay'
SAMPLE_RATE = 'SampleRate'

class AudioWriter:
    def __init__(self, config=None):
        self.options = {
            CLOCK_SPEED: 3500000,
            CONTENTION_BEGIN: 14334,
            CONTENTION_END: 57248,
            CONTENTION_FACTOR: 51,
            FRAME_DURATION: 69888,
            INTERRUPT_DELAY: 942,
            SAMPLE_RATE: 44100
        }
        if config:
            for k, v in config.items():
                try:
                    self.options[k] = int(v)
                except ValueError:
                    pass

    def write_audio(self, audio_file, delays, contention=False, interrupts=False, offset=0):
        if contention or interrupts:
            self._add_contention(delays, contention, interrupts, offset)
        samples = self._delays_to_samples(delays)
        self._write_wav(audio_file, samples)

    def formats(self):
        return ('.wav',)

    def _add_contention(self, delays, contention, interrupts, cycle):
        c_begin, c_end = self.options[CONTENTION_BEGIN], self.options[CONTENTION_END]
        c_factor = 1 + self.options[CONTENTION_FACTOR] / 100
        i_delay = self.options[INTERRUPT_DELAY]
        f_duration = self.options[FRAME_DURATION]

        for i in range(len(delays)):
            d_offset = 0
            while 1:
                if interrupts and cycle == 0:
                    cycle = i_delay
                    if i:
                        delays[i] += i_delay
                        d_offset += i_delay
                d_remaining = delays[i] - d_offset
                if contention and cycle < c_end:
                    if cycle < c_begin:
                        gap = c_begin - cycle
                        if d_offset + gap >= delays[i]:
                            # Delay ends before next contended interval starts
                            cycle += d_remaining
                            break
                        # Delay crosses into contended interval
                        d_offset += gap
                        cycle = c_begin
                    else:
                        c_period = c_end - cycle
                        d_rem_contended = int(d_remaining * c_factor)
                        if d_rem_contended < c_period:
                            # Delay ends within contended interval
                            delays[i] = d_offset + d_rem_contended
                            cycle += d_rem_contended
                            break
                        # Delay crosses into uncontended interval
                        cd_cycles = int(c_period / c_factor)
                        delays[i] += c_period - cd_cycles
                        d_offset += cd_cycles
                        cycle = c_end
                else:
                    if d_remaining < f_duration - cycle:
                        # Delay ends before frame boundary
                        cycle += d_remaining
                        break
                    # Delay crosses frame boundary
                    d_offset += f_duration - cycle
                    cycle = 0

    def _delays_to_samples(self, delays):
        sample_delay = self.options[CLOCK_SPEED] / self.options[SAMPLE_RATE]
        samples = []
        direction = 1
        i = 0
        d = delays[0]
        t = 0
        while 1:
            while t >= d:
                i += 1
                if i >= len(delays):
                    break
                d += delays[i]
                direction *= -1
            if i >= len(delays):
                break
            if direction > 0:
                samples.append(32767)
            else:
                samples.append(32768)
            t += sample_delay
        return samples

    def _to_int32(self, num):
        return (num & 255, (num >> 8) & 255, (num >> 16) & 255, num >> 24)

    def _write_wav(self, audio_file, samples):
        sample_rate = self.options[SAMPLE_RATE]
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
