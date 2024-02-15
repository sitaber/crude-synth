import numpy as np

from dsp import (
    sine_wave,
    sawtooth_wave,
    trianlge_wave,
    pulse_wave,
    noise,
    ADSEnvelope,
    release_envelope
)

SAMPLE_RATE = 44100
BUFFER_SIZE = 256*4
# -----------------------------
class OSC:
    def __init__(self):
        self.rect=None
        self.pw_knob = None
        self.menu = None
        self.toggle = None
        self.detune = 0
        self.gain = 0.5

class LFO:
    def __init__(self):
        self.on = False
        self.rate = 15
        self.depth = 100
        self.lfo_func = 'sine'
        self.duty = 0.5
        self.pwm_on = False
        self.pw_mod = 0.25
        self.pulse_depth_on = False
        
class ControlOscillator:
    mod_funcs = {
    'sine': sine_wave,
    'sawtooth': sawtooth_wave,
    'triangle': trianlge_wave,
    'pulse': pulse_wave
    }

    def __init__(self): #, control, depth, rate, center_value):
        self.on = False
        self._rate = None #rate
        self.depth = None #depth
        self.lfo_func = 'sine'
        self.center_freq = None #center_value
        self._gen = None
        self.control = None #control

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, value):
        self._rate = value
        self.set_gen()
        return

    @property
    def lfo_func(self):
        return self._lfo_func

    @lfo_func.setter
    def lfo_func(self, value):
        self._lfo_func = value
        self.set_gen()

    def set_gen(self):
        self._gen = self.mod_funcs[self.lfo_func](self.rate)
        return

    def update_control(self):
        mod_ = [next(self._gen) for _ in range(BUFFER_SIZE)][-1]
        new_value = self.center_freq + self.depth * mod_
        self.control.automated_update(new_value)
        return
      
class Voice:
    def __init__(self, generator, osc2=None, envelope=None, g1=1, g2=1, sample_rate=SAMPLE_RATE):
        self._osc1 = generator
        self._osc2 = osc2
        self._envelope = envelope
        self.sample_rate = sample_rate
        self._release = False
        self._gain1 = 0.1 * g1
        self._gain2 = 0.1 * g2
        
    def release(self, adsr):
        release = adsr["Release"]
        self._envelope = release_envelope(
            release_time = release,
            start_amp = next(self._envelope),
            sample_rate = self.sample_rate
        )
        self._release = True
        return

    def get_audio_data(self, frames):
        samples = np.zeros(frames)

        if self._osc2:
            samples += [
                next(self._osc1) * self._gain1 + next(self._osc2) * self._gain2 
                for _ in range(frames)
            ]
        else:
            samples += [next(self._osc1) * self._gain1 for _ in range(frames)]
                
        samples *= [next(self._envelope) for _ in range(frames)]
        
        return samples 
   
 
# ----------------------------------

























#
