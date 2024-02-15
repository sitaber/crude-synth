import math
from random import uniform

import numpy as np

from settings import SAMPLE_RATE

MOOG_PI  = 3.14159265358979323846264338327950288

def hz_to_rad(f):
    return 2*MOOG_PI * f 
    
# =========================================================
#                    Sine
# =========================================================
def sine_wave(frequency, modulator=None, depth=0):
    modulator = modulator
    depth = depth
    phasor_ = 0
    vib = 0

    while True:
        if modulator:
            mod_ = next(modulator)
            vib = mod_ * depth

        yield math.sin(2*math.pi*phasor_)
        phasor_ += (frequency+vib)/SAMPLE_RATE


# =========================================================
#                    Saw Tooth
# =========================================================
def sawtooth_wave(frequency, modulator=None, depth=0):
    modulator = modulator
    depth = depth
    t_p = 0
    vib = 0

    while True:
        if modulator:
            mod_ = next(modulator)
            vib = mod_ * depth

        signal = 2 * (t_p - math.floor(0.5+t_p))
        yield signal
        t_p += (frequency+vib)/SAMPLE_RATE #/1/440

# =========================================================
#                    Triangle
# =========================================================
def trianlge_wave(frequency, modulator=None, depth=0):
    modulator = modulator
    depth = depth
    phasor_ = 0
    vib = 0

    while True:
        if modulator:
            mod_ = next(modulator)
            vib = mod_ * depth

        sinv = math.sin(2*math.pi*phasor_)
        signal = 2/math.pi * math.asin(sinv)
        yield signal
        phasor_ += (frequency+vib)/SAMPLE_RATE

# ===============================================
#               PULSE WAVE
# ===============================================
def pulse_wave(frequency, modulator=None, depth=0, duty_cycle=0.5, depth_D=0, d_mod=None):
    modulator = modulator
    depth = depth
    phasor_ = 0

    duty_cycle = duty_cycle
    d_mod = d_mod
    depth_D = depth_D # cannot go less than 0.05% or greater than 0.95

    vib_F = 0
    vib_D = 0
    
    while True:
        if modulator:
            mod_ = next(modulator)
            vib_F = mod_ * depth
        
        if d_mod:
            mod_d = next(d_mod)
            vib_D = mod_d * depth_D # check if duty + vib exceeds
        
        if duty_cycle + vib_D > 0.95 or duty_cycle + vib_D < 0.05:
            vib_D = 0

        if phasor_ < (duty_cycle + vib_D):
            sample = 1
        elif phasor_ < 1.0:
            sample = -1

        yield sample

        phasor_ += (frequency+vib_F)/44100 # steps += step_size
        if phasor_ > 1.0:
            phasor_ = 0

# ===============================================
#               Noise
# ===============================================
#white_noise
def noise(frequency, modulator=None, depth=None):
    while True:
        yield uniform(-1, 1)

# ========================= #
# -- Envelope Generators -- #
# ========================= #
def ADSEnvelope(attack_time, decay_time, sustain=0.5, sample_rate=SAMPLE_RATE):
        # max frames is 44100 == 1 sec
        sustain = max(min(1.0, sustain), 0)

        attack_frames = int(sample_rate * attack_time)
        attack = np.linspace(0.0, 1.0, attack_frames)

        decay_frames = int(sample_rate * decay_time)
        decay = np.linspace(1.0, sustain, decay_frames)

        for value in attack:
            yield value

        for value in decay:
            yield value

        while True:
            yield sustain

def release_envelope(release_time, start_amp=0.5, sample_rate=SAMPLE_RATE):
        release_frames = int(sample_rate * release_time)
        release = np.linspace(start_amp, 0, release_frames)

        for value in release:
            yield value

        while True:
            yield 0

# ==================================================

class BiQuadBase:
    def __init__(self):
        self.bCoef = np.array([0.0, 0.0, 0.0])
        self.aCoef = np.array([0.0, 0.0])
        self.w = np.array([0.0, 0.0])
        
        
    def process(self, samples):
        out = 0
        for s in range(len(samples)):
            out = self.bCoef[0] * samples[s] + self.w[0]
            self.w[0] = self.bCoef[1] * samples[s] - self.aCoef[0] * out + self.w[1]
            self.w[1] = self.bCoef[2] * samples[s] - self.aCoef[1] * out
            samples[s] = out

        return samples
	
    def tick(self, sample):
        out = self.bCoef[0] * s + self.w[0]
        self.w[0] = self.bCoef[1] * s - self.aCoef[0] * out + self.w[1]
        self.w[1] = self.bCoef[2] * s - self.aCoef[1] * out

        return out
	
    def set_coefs(self, b, a):
        self.bCoef = b
        self.aCoef = a
    
class RBJFilter(BiQuadBase):
    def __init__(self, cutoff = 1, sampleRate = 44100):
        super().__init__()
        self.cutoff = 0
        self.sampleRate = sampleRate
        self.Q = 0.707 # 0.707 seems to make it flat
        self.A = 1

        self.a = np.array([0.0, 0.0, 0.0])
        self.b = np.array([0.0, 0.0, 0.0])

        self.set_cutoff(cutoff)

    def update_coefficients(self):
        cosOmega = math.cos(self.omega)
        sinOmega = math.sin(self.omega)

        alpha = sinOmega / (2.0 * self.Q)
        self.b[0] = (1 - cosOmega) / 2;
        self.b[1] = 1 - cosOmega
        self.b[2] = self.b[0]
        self.a[0] = 1 + alpha
        self.a[1] = -2 * cosOmega
        self.a[2] = 1 - alpha

        #// Normalize filter coefficients
        factor = 1.0 / self.a[0]

        aNorm = np.zeros(2)
        bNorm = np.zeros(3)

        aNorm[0] = self.a[1] * factor;
        aNorm[1] = self.a[2] * factor;

        bNorm[0] = self.b[0] * factor;
        bNorm[1] = self.b[1] * factor;
        bNorm[2] = self.b[2] * factor;

        self.set_coefs(bNorm, aNorm)

    def set_cutoff(self, cutoff):	
        #// In Hertz, 0 to Nyquist
        self.omega = hz_to_rad(cutoff) / self.sampleRate;
        self.update_coefficients()
        self.cutoff = cutoff

    def get_cutoff(self):
        return self.cutoff    







#
