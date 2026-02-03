# © 2026 Richard Dymond (rjdymond@gmail.com)
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

from math import ceil
from struct import pack

from skoolkit.audio import SAMPLE_RATE
from skoolkit.simutils import FRAME_DURATIONS

AY_CLOCK_RATE = 1773400
AY_DAC_TABLE = tuple(v / 0xFFFF for v in (
    0x0000, 0x0385, 0x053D, 0x0770, 0x0AD7, 0x0FD5, 0x15B0, 0x230C,
    0x2B4C, 0x43C1, 0x5A4B, 0x732F, 0x9204, 0xAFF1, 0xD921, 0xFFFF
))
CLOCK_SPEED = 3546900
FRAME_DURATION = FRAME_DURATIONS[1]

class Channel:
    def __init__(self, pan):
        self.volume = 0
        self.tone = 0
        self.tone_counter = 0
        self.tone_period = 1
        self.t_off = 0
        self.n_off = 0
        self.e_on = 0
        self.pan_left = 1 - pan
        self.pan_right = pan

class Interpolator:
    def __init__(self):
        self.c = [0] * 4
        self.y = [0] * 4

class AY:
    def __init__(self, sample_rate):
        self.interpolator_left = Interpolator()
        self.interpolator_right = Interpolator()
        self.x = 0
        self.step = AY_CLOCK_RATE / (sample_rate * 64)
        self.noise = 1
        self.noise_counter = 0
        self.noise_period = 0
        self.left = 0
        self.right = 0
        self.envelope = 0
        self.envelope_shape = 0
        self.envelope_counter = 0
        self.envelope_segment = 0
        self.envelope_period = 1
        self.sample_rate = sample_rate
        slide_down = (self.slide_down, 31)
        slide_up = (self.slide_up, 0)
        hold_bottom = (self.hold_bottom, 0)
        hold_top = (self.hold_top, 31)
        self.envelopes = (
            (slide_down, hold_bottom),
            (slide_down, hold_bottom),
            (slide_down, hold_bottom),
            (slide_down, hold_bottom),
            (slide_up, hold_bottom),
            (slide_up, hold_bottom),
            (slide_up, hold_bottom),
            (slide_up, hold_bottom),
            (slide_down, slide_down),
            (slide_down, hold_bottom),
            (slide_down, slide_up),
            (slide_down, hold_top),
            (slide_up, slide_up),
            (slide_up, hold_top),
            (slide_up, slide_down),
            (slide_up, hold_bottom)
        )
        self.channels = (Channel(0.0), Channel(0.5), Channel(1.0))
        self.update_state([0] * 16)

    def update_mixer(self):
        self.noise_counter += 1
        if self.noise_counter >= self.noise_period * 2:
            self.noise_counter = 0
            self.noise = (self.noise // 2) | (((self.noise ^ (self.noise // 8)) & 1) * 65536)
        noise = self.noise & 1

        self.envelope_counter += 1
        if self.envelope_counter >= self.envelope_period:
            self.envelope_counter = 0
            self.envelopes[self.envelope_shape][self.envelope_segment][0]()

        self.left = 0
        self.right = 0

        for channel in self.channels:
            channel.tone_counter += 1
            if channel.tone_counter >= channel.tone_period:
                channel.tone_counter = 0
                channel.tone ^= 1
            out = (channel.tone | channel.t_off) & (noise | channel.n_off)
            out *= self.envelope // 2 if channel.e_on else channel.volume
            self.left += AY_DAC_TABLE[out] * channel.pan_left
            self.right += AY_DAC_TABLE[out] * channel.pan_right

    def update_state(self, r):
        for i, channel in enumerate(self.channels):
            channel.tone_period = ((r[2 * i] + 256 * r[2 * i + 1]) & 0x0FFF) or 1
            channel.t_off = (r[7] >> i) & 1
            channel.n_off = (r[7] >> (i + 3)) & 1
            channel.e_on = r[8 + i] & 16
            channel.volume = r[8 + i] % 16

        self.noise_period = (r[6] & 0x1F) or 1
        self.envelope_period = (r[11] + 256 * r[12]) or 1

        if r[13] >= 0:
            self.envelope_shape = r[13] % 16
            self.envelope_counter = 0
            self.envelope_segment = 0
            self.envelope = self.envelopes[self.envelope_shape][0][1]
            r[13] = -1

    def frames(self, ay_log, ay_res):
        ay = [0] * 16
        frame = -1
        t0 = ay_log[0][0]
        for tstates, reg, value in ay_log:
            if frame >= 0:
                nframe = tstates // ay_res
                while nframe > frame:
                    yield ay
                    nframe -= 1
            frame = tstates // ay_res
            ay[reg] = value

    def slide_up(self):
        self.envelope += 1
        if self.envelope > 31:
            self.envelope_segment ^= 1
            self.envelope = self.envelopes[self.envelope_shape][self.envelope_segment][1]

    def slide_down(self):
        self.envelope -= 1
        if self.envelope < 0:
            self.envelope_segment ^= 1
            self.envelope = self.envelopes[self.envelope_shape][self.envelope_segment][1]

    def hold_top(self):
        pass

    def hold_bottom(self):
        pass

    def render(self, ay_log, ay_res, volume):
        samples = []
        frame_rate = 50 * FRAME_DURATION / ay_res
        fstep = frame_rate / self.sample_rate
        fcounter = 1
        frames = self.frames(ay_log, ay_res)
        while True:
            fcounter += fstep
            while fcounter >= 1:
                # Load next frame of data to AY registers
                fcounter -= 1
                frame = next(frames, None)
                if frame:
                    self.update_state(frame)
                else:
                    break
            if frame is None:
                break

            # Generate and store next sample
            for i in range(8):
                self.x += self.step;
                if self.x >= 1:
                    self.x -= 1
                    self.update_mixer()
            samples.append((self.left * volume, self.right * volume))

        return samples

class Options:
    def __init__(self, volume=75, ay_res=FRAME_DURATION, beeper=False):
        self.volume = volume
        self.ay_res = ay_res
        self.beeper = beeper

class AYAudioWriter:
    def __init__(self, config=None):
        self.options = {SAMPLE_RATE: 44100}
        if config:
            for k, v in config.items():
                try:
                    self.options[k] = int(v)
                except ValueError:
                    pass

    def write_audio(self, audio_file, audio_log, options):
        volume = min(max(0, options.volume), 100) / 100
        ay_volume = volume * 2 / 3
        ay_log, beeper_log = self._parse_log(audio_log)
        if options.beeper and beeper_log:
            # Synchronise log start times
            if ay_log[0][0] < beeper_log[0]:
                beeper_log.insert(0, ay_log[0][0])
            elif beeper_log[0] < ay_log[0][0]:
                ay_log.insert(0, (beeper_log[0], 0, 0))
        ay = AY(self.options[SAMPLE_RATE])
        ay_samples = ay.render(ay_log, options.ay_res, ay_volume)
        if options.beeper and beeper_log:
            delays = [t1 - t0 for t0, t1 in zip(beeper_log, beeper_log[1:])]
            beeper_samples = self._render_beeper(delays, volume)
            samples = self._combine(ay_samples, beeper_samples)
        else:
            samples = ay_samples
        self._write_wav(audio_file, samples)

    def _parse_log(self, audio_log):
        ay_log = []
        beeper_log = []
        for record in audio_log:
            if record[1] < 16:
                ay_log.append(record)
            else:
                beeper_log.append(record[0])
        return ay_log, beeper_log

    def _render_beeper(self, delays, volume):
        # Apply a moving average filter
        sample_delay = CLOCK_SPEED / self.options[SAMPLE_RATE]
        s0, s1 = 0, sample_delay
        t, t1 = 0, ceil(s1)
        bit = bits = 0
        samples = []
        for d in delays:
            while True:
                if t + d < t1:
                    if bit:
                        bits += d
                    t += d
                    break
                i = t1 - t
                if bit:
                    bits += i
                d -= i
                samples.append(volume * bits / (t1 - s0))
                s0 = t = t1
                s1 += sample_delay
                t1 = ceil(s1)
                bits = 0
            bit = 1 - bit
        return samples

    def _combine(self, ay_samples, beeper_samples):
        samples = []
        ay_len = len(ay_samples)
        beeper_len = len(beeper_samples)
        max_len = max(ay_len, beeper_len)
        ay_samples.extend([(0, 0)] * (max_len - ay_len))
        beeper_samples.extend([0] * (max_len - beeper_len))
        for i in range(max_len):
            left = (ay_samples[i][0] + beeper_samples[i]) / 2
            right = (ay_samples[i][1] + beeper_samples[i]) / 2
            samples.append((left, right))
        return samples

    def _write_wav(self, audio_file, samples):
        sample_rate = self.options[SAMPLE_RATE]
        channels = 2
        bits_per_sample = 16
        bytes_per_sample = (bits_per_sample // 8) * channels
        byte_rate = bytes_per_sample * sample_rate
        data_length = bytes_per_sample * len(samples)
        header = bytearray()
        header.extend(b'RIFF')
        header.extend(pack('<I', 36 + data_length))
        header.extend(b'WAVEfmt ')
        header.extend(pack('<IH', 16, 1)) # length of fmt chunk, format (PCM)
        header.extend(pack('<HIIHH', channels, sample_rate, byte_rate, bytes_per_sample, bits_per_sample))
        header.extend(b'data')
        header.extend(pack('<I', data_length))
        audio_file.write(header)
        for left, right in samples:
            audio_file.write(pack('<hh', round(left * 0xFFFF) - 0x8000, round(right * 0xFFFF) - 0x8000))
