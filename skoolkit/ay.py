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

from skoolkit.audio import (CLOCK_SPEED, FRAME_DURATION, SAMPLE_RATE,
                            moving_average_filter, write_wav)
from skoolkit.simutils import CLOCK_SPEEDS, FRAME_DURATIONS

AY_CLOCK_RATE = 1773400
AY_DAC_TABLE = tuple(v / 0xFFFF for v in (
    0x0000, 0x0385, 0x053D, 0x0770, 0x0AD7, 0x0FD5, 0x15B0, 0x230C,
    0x2B4C, 0x43C1, 0x5A4B, 0x732F, 0x9204, 0xAFF1, 0xD921, 0xFFFF
))
SLIDE_DOWN = (-1, 31)
SLIDE_UP = (1, 0)
HOLD_BOTTOM = (0, 0)
HOLD_TOP = (0, 31)
ENVELOPES = (
    (SLIDE_DOWN, HOLD_BOTTOM),
    (SLIDE_DOWN, HOLD_BOTTOM),
    (SLIDE_DOWN, HOLD_BOTTOM),
    (SLIDE_DOWN, HOLD_BOTTOM),
    (SLIDE_UP, HOLD_BOTTOM),
    (SLIDE_UP, HOLD_BOTTOM),
    (SLIDE_UP, HOLD_BOTTOM),
    (SLIDE_UP, HOLD_BOTTOM),
    (SLIDE_DOWN, SLIDE_DOWN),
    (SLIDE_DOWN, HOLD_BOTTOM),
    (SLIDE_DOWN, SLIDE_UP),
    (SLIDE_DOWN, HOLD_TOP),
    (SLIDE_UP, SLIDE_UP),
    (SLIDE_UP, HOLD_TOP),
    (SLIDE_UP, SLIDE_DOWN),
    (SLIDE_UP, HOLD_BOTTOM)
)

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

class AY:
    def __init__(self):
        self.channels = (Channel(0.5), Channel(0.5), Channel(0.5))

    def frames(self, ay_log, ay_res):
        ay = [0] * 16
        frame = -1
        for tstates, reg, value in ay_log:
            if frame >= 0:
                nframe = tstates // ay_res
                while nframe > frame:
                    yield ay
                    nframe -= 1
            frame = tstates // ay_res
            ay[reg] = value

    def render(self, ay_log, sample_rate, frame_duration, ay_res, volume):
        samples = []
        frame_rate = 50 * frame_duration / ay_res
        fstep = frame_rate / sample_rate
        fcounter = 1
        frames = self.frames(ay_log, ay_res)
        x = 0
        step = AY_CLOCK_RATE / (sample_rate * 64)
        left, right = 0, 0
        channels = self.channels
        i_channels = tuple(enumerate(channels))
        noise = 1
        noise_counter = 0
        noise_period = 1
        envelope_counter = 0
        envelope_period = 1
        envelope_shape = 0
        envelope_segment = 0
        envelope = 31
        while True:
            fcounter += fstep
            while fcounter >= 1:
                # Load next frame of data to AY registers
                fcounter -= 1
                r = next(frames, None)
                if r is None:
                    break
                for i, channel in i_channels:
                    channel.tone_period = ((r[2 * i] + 256 * r[2 * i + 1]) & 0x0FFF) or 1
                    channel.t_off = (r[7] >> i) & 1
                    channel.n_off = (r[7] >> (i + 3)) & 1
                    channel.e_on = r[8 + i] & 16
                    channel.volume = r[8 + i] % 16
                noise_period = (r[6] & 0x1F) or 1
                envelope_period = (r[11] + 256 * r[12]) or 1
                if r[13] >= 0:
                    envelope_shape = r[13] % 16
                    envelope_counter = 0
                    envelope_segment = 0
                    envelope = ENVELOPES[envelope_shape][0][1]
                    r[13] = -1
            if r is None:
                break

            # Generate and store next sample
            for i in range(8):
                x += step
                if x >= 1:
                    x -= 1
                    noise_counter += 1
                    if noise_counter >= noise_period * 2:
                        noise_counter = 0
                        noise = (noise // 2) | (((noise ^ (noise // 8)) & 1) * 65536)
                    n = noise & 1
                    envelope_counter += 1
                    if envelope_counter >= envelope_period:
                        envelope_counter = 0
                        envelope += ENVELOPES[envelope_shape][envelope_segment][0]
                        if envelope < 0 or envelope > 31:
                            envelope_segment ^= 1
                            envelope = ENVELOPES[envelope_shape][envelope_segment][1]
                    left, right = 0, 0
                    for channel in channels:
                        channel.tone_counter += 1
                        if channel.tone_counter >= channel.tone_period:
                            channel.tone_counter = 0
                            channel.tone ^= 1
                        if channel.e_on:
                            outv = AY_DAC_TABLE[((channel.tone | channel.t_off) & (n | channel.n_off)) * (envelope // 2)]
                        else:
                            outv = AY_DAC_TABLE[((channel.tone | channel.t_off) & (n | channel.n_off)) * channel.volume]
                        left += outv * channel.pan_left
                        right += outv * channel.pan_right

            samples.append(left * volume)
            samples.append(right * volume)

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
        ay = AY()
        frame_duration = self.options[FRAME_DURATION]
        ay_res = options.ay_res or 622 # 70908/622=114 (5700Hz)
        ay_samples = ay.render(ay_log, self.options[SAMPLE_RATE], frame_duration, ay_res, ay_volume)
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
