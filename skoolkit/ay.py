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

from skoolkit.audio import (CLOCK_SPEED, FRAME_DURATION, SAMPLE_RATE,
                            moving_average_filter, write_wav)
from skoolkit.simutils import CLOCK_SPEEDS, FRAME_DURATIONS

AY_CLOCK_RATE = 1773400
AY_DAC_TABLE = tuple(v / 0xFFFF for v in (
    0x0000, 0x0385, 0x053D, 0x0770, 0x0AD7, 0x0FD5, 0x15B0, 0x230C,
    0x2B4C, 0x43C1, 0x5A4B, 0x732F, 0x9204, 0xAFF1, 0xD921, 0xFFFF
))

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
        self.channels = (Channel(0.5), Channel(0.5), Channel(0.5))
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

    def render(self, ay_log, frame_duration, ay_res, volume):
        samples = []
        frame_rate = 50 * frame_duration / ay_res
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
            samples.append(self.left * volume)
            samples.append(self.right * volume)

        return samples

class Options:
    def __init__(self, volume=100, ay_res=None, beeper=False):
        self.volume = volume
        self.ay_res = ay_res
        self.beeper = beeper

class AYAudioWriter:
    def __init__(self, config=None):
        self.options = {
            CLOCK_SPEED: CLOCK_SPEEDS[1],
            FRAME_DURATION: FRAME_DURATIONS[1],
            SAMPLE_RATE: 44100
        }
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
            if ay_log and ay_log[0][0] < beeper_log[0]:
                beeper_log.insert(0, ay_log[0][0])
            else:
                ay_log.insert(0, (beeper_log[0], 0, 0))
        ay = AY(self.options[SAMPLE_RATE])
        frame_duration = self.options[FRAME_DURATION]
        ay_res = options.ay_res or 622 # 70908/622=114 (5700Hz)
        ay_samples = ay.render(ay_log, frame_duration, ay_res, ay_volume)
        if options.beeper and beeper_log:
            delays = [t1 - t0 for t0, t1 in zip(beeper_log, beeper_log[1:])]
            beeper_samples = moving_average_filter(delays, self.options, volume)
            samples = self._combine(ay_samples, beeper_samples)
        else:
            samples = ay_samples
        write_wav(audio_file, samples[::2], self.options[SAMPLE_RATE])

    def _parse_log(self, audio_log):
        ay_log = []
        beeper_log = []
        for record in audio_log:
            if record[1] < 16:
                ay_log.append(record)
            else:
                beeper_log.append(record[0])
        return ay_log, beeper_log

    def _combine(self, ay_samples, beeper_samples):
        samples = []
        ay_len = len(ay_samples) // 2
        beeper_len = len(beeper_samples)
        max_len = max(ay_len, beeper_len)
        ay_samples.extend([0] * ((max_len - ay_len) * 2))
        beeper_samples.extend([0] * (max_len - beeper_len))
        for i in range(max_len):
            left = (ay_samples[2 * i] + beeper_samples[i]) / 2
            right = (ay_samples[2 * i + 1] + beeper_samples[i]) / 2
            samples.append(left)
            samples.append(right)
        return samples
