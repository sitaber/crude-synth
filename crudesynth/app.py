import sys
import math as math
import uuid

import numpy as np
import sounddevice as sd

import pygame

import gui
from core import OSC, LFO, ControlOscillator, Voice 

from dsp import (
    sine_wave,
    sawtooth_wave,
    trianlge_wave,
    pulse_wave,
    noise,
    ADSEnvelope,
    release_envelope,
    RBJFilter
)

WIDTH = 1280
HEIGHT = 720
FPS = 120
SAMPLE_RATE = 44100
BUFFER_SIZE = 256*4

# ---------------------------
def check_piano_click(mouse_rect, event, rects):
    idx = mouse_rect.collidelist(rects)
    if idx != -1:
        control = rects[idx]
        return control
    else:
        return None

def build_voice(osc1, lfo1, osc2, lfo2, note, freqs, adsr, gen_funcs, mod_funcs):
    kwargs = {'frequency': freqs[note+osc1.detune]} 
    gen1 = gen_funcs[osc1.menu.menu_text]
    
    if lfo1.on == True:
        mod_gen = mod_funcs[lfo1.lfo_func] # get lfo func

        if lfo1.lfo_func == 'pulse':
            # set duty and use depth to modulate frequency
            kwargs['modulator'] = mod_gen(lfo1.rate, duty_cycle=lfo1.duty)
            kwargs['depth'] = lfo1.depth
        else:
            # NO special settigns
            kwargs['modulator'] = mod_gen(lfo1.rate)
            kwargs['depth'] = lfo1.depth # used in main osc generator with modulator (is freq)
    else:
        kwargs['modulator'] = None
        kwargs['depth'] = None

    if osc1.menu.menu_text == 'pulse': # applies to OSC
        kwargs['duty_cycle'] = osc1.pw_knob.value

    if osc2.toggle.active:
        kwargs2 = {'frequency': freqs[note+osc2.detune]}
        gen2 = gen_funcs[osc2.menu.menu_text]
        # Build modulator if on
        if lfo2.on == True:
            mod_gen = mod_funcs[lfo2.lfo_func] # get lfo func

            if lfo2.lfo_func == 'pulse':
                # set duty and use depth to modulate frequency
                kwargs2['modulator'] = mod_gen(lfo2.rate, duty_cycle=lfo2.duty)
                kwargs2['depth'] = lfo2.depth
            else:
                # NO special settigns
                kwargs2['modulator'] = mod_gen(lfo2.rate)
                kwargs2['depth'] = lfo2.depth # used in main osc generator with modulator (is freq)
        else:
            kwargs2['modulator'] = None
            kwargs2['depth'] = None

        if osc2.menu.menu_text == 'pulse': # applies to OSC
            kwargs2['duty_cycle'] = osc2.pw_knob.value

        osc2_gen = gen2(**kwargs2)
    else:
        osc2_gen=None

    voice = Voice(
        generator = gen1(**kwargs),
        osc2 = osc2_gen,
        envelope = ADSEnvelope(
            attack_time = adsr['Attack'],
            decay_time = adsr['Decay'],
            sustain = adsr['Sustain'],
            sample_rate = SAMPLE_RATE
        ),
        g1 = osc1.gain,
        g2 = osc2.gain
    )

    return voice

def add_voice(voice, retrigger, note, voices_to_release, voices):
    voice_id = None
    if retrigger.active and note in voices_to_release.keys():
        # note previously generated a voice
        voice_id = voices_to_release[note]

    # check if voice is still active/exists, override is so
    if voice_id in voices.keys():
        voices.pop(voice_id)
        voices[voice_id] = voice

    else:
        # Voice no longer active or never existed, generate one
        voice_id = uuid.uuid4()
        voices[voice_id] = voice
        voices_to_release[note] = voice_id

    # check number of voices | remove oldest / steal voice
    if len(voices) > n_voices['val']: #never passed...
        voices = dict(list(voices.items())[-n_voices['val']:])

    return voices


# -----------------------
# -- general setup / init
# -----------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption('Crude Synth')
clock = pygame.time.Clock()

gen_funcs = {
    'sine': sine_wave,
    'sawtooth': sawtooth_wave,
    'triangle': trianlge_wave,
    'noise': noise,
    'pulse': pulse_wave
}

mod_funcs = {
    'sine': sine_wave,
    'sawtooth': sawtooth_wave,
    'triangle': trianlge_wave,
    'pulse': pulse_wave,
}

adsr = {
    'Attack': 0.5,
    'Decay': 0.5,
    'Sustain': 0.5,
    'Release': 0.5,
    'gain': 0.5
}

# Stream SoundDevice
devices = sd.query_hostapis()
device = devices[0]['default_output_device']

stream = sd.OutputStream(
    samplerate = int(SAMPLE_RATE),
    blocksize = 0,
    device = device,
    channels = 1,
    dtype = 'float32'
)

# ------------------
# -- Build GUI
# ------------------
font = gui.Font(None, 30)
font2 = gui.Font(None, 15)

controls = []
labels = []
value_boxes = []

# =================
# ------- Amp
amp_rect = pygame.Rect(WIDTH*0.65, HEIGHT*0.55, 400, 75)

results = gui.make_amp_adsr(amp_rect, adsr, controls, labels, value_boxes, font)
controls, labels, value_boxes  = results
# =================
# ------ Osc1
osc1 = OSC()
osc1.rect = pygame.Rect(WIDTH*0.35, HEIGHT*0.10, 150, 150)

lfo1 = LFO()
results = gui.make_osc1(osc1, controls, labels, value_boxes, lfo1, font, font2)
controls, labels, value_boxes, lfo1, osc1 = results
# ============
# ------- Osc2
osc2 = OSC()
osc2.rect = pygame.Rect(WIDTH*0.35, HEIGHT*0.10+160, 150, 150)

lfo2 = LFO()
results = gui.make_osc2(osc2, controls, labels, value_boxes, lfo2, font, font2)
controls, labels, value_boxes, lfo2, osc2 = results
# =========
# ----- LFOs
lfo_rect = pygame.Rect(WIDTH*0.02, HEIGHT*0.10, 350, 150)
lfo_rect2 = pygame.Rect(WIDTH*0.02, HEIGHT*0.10+160, 350, 150)

results = gui.make_lfo_panel(lfo_rect, lfo1, controls, labels, value_boxes, font)
controls, labels, value_boxes, lfo1 = results 

results = gui.make_lfo_panel(lfo_rect2, lfo2, controls, labels, value_boxes, font)
controls, labels, value_boxes, lfo2 = results
# ============
# ----- Filter
voice_filter = RBJFilter(250)
filter_lfo = ControlOscillator()
filter_rect = pygame.Rect(WIDTH*0.82, HEIGHT*0.10, 200, 150)

results = gui.make_filter_box(filter_rect, filter_lfo, voice_filter, controls, labels, value_boxes, font)
controls, labels, value_boxes, filter_lfo, voice_filter, filter_toggle = results

# =================
# --- Voice Control
results = gui.make_voice_controls(controls, labels, value_boxes, font)
controls, labels, value_boxes, retrigger, n_voices = results

# ---------- Piano Keys
wkeys, bkeys, piano_keys = gui.make_piano_keys()


# -------- RENDER
screen.fill((90,91,107))

#pygame.draw.rect(screen, 'black', amp_rect, width=5) #
#pygame.draw.rect(screen, 'black', osc1.rect, width=5) # 
pygame.draw.rect(screen, 'black', (WIDTH*0.32, HEIGHT*0.10, 225, 150), width=5)
#pygame.draw.rect(screen, 'black', osc2.rect, width=5)
pygame.draw.rect(screen, 'black', (WIDTH*0.32, HEIGHT*0.10+160, 225, 150), width=5)
pygame.draw.rect(screen, 'black', filter_rect, width=5)
pygame.draw.rect(screen, 'black', lfo_rect, width=5)
pygame.draw.rect(screen, 'black', lfo_rect2, width=5)
pygame.draw.rect(screen, 'black', filter_lfo.rect, width=5)

pygame.draw.line(screen, 'black', (0,HEIGHT*0.05), (WIDTH, HEIGHT*0.05), 3)
pygame.draw.line(screen, 'black', (0,HEIGHT*0.70), (WIDTH, HEIGHT*0.70), 3)

screen.blits(labels)

for control in controls:
    control.draw()

for value_box in value_boxes:
    value_box.draw()

for k in piano_keys:
    k.draw()

was_under = False
load_led = pygame.Rect((10,HEIGHT*0.72,8,8))
pygame.draw.circle(screen, (0,0,0), (load_led.x, load_led.y), 6, 1)

# ----------------
#      MAIN
# ----------------
KEYLIST = ['a','w','s','e','d','f','t','g','y','h','u','j']
octave = 2
freqs = [round(440.0 * math.pow(2, (i-49)/12), 4) for i in range(4,89)]

mouse_held = None 
active_control = None

voices_to_release = {}
voices = {}

base_gain = 0.4

stream.start()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            stream.stop()
            stream.close()
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx,my = event.pos[0], event.pos[1]
            mouse_rect = pygame.Rect((mx,my),(1,1))

            if active_control:
                active_control.handle_input(event)
                if active_control.active == False:
                    active_control = None
            else:
                # Body section / main area
                idx = mouse_rect.collidelist(controls)
                if idx != -1:
                    control = controls[idx]
                    control.handle_input(event)

                    if control.active and control.updatable:
                        active_control = control

            # --- Piano section
            button_clicked = check_piano_click(mouse_rect, event, bkeys)
            if button_clicked is None:
                button_clicked = check_piano_click(mouse_rect, event, wkeys)

            if button_clicked:
                if button_clicked.active == False:
                    button_clicked.active = True
                    mouse_held = piano_keys[button_clicked._id-12]
                    note = button_clicked._id #-12

                    voice = build_voice(osc1, lfo1, osc2, lfo2, note, freqs, adsr, gen_funcs, mod_funcs)
                    voices = add_voice(voice, retrigger, note, voices_to_release, voices)
                    button_clicked.draw()

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if mouse_held:
                mouse_held.active = False
                voice_id = voices_to_release[mouse_held._id]

                # Check that voice is still active (i.e.not stolen) and release it
                if voice_id in voices.keys():
                    voices[voice_id].release(adsr)

                mouse_held.draw()
                mouse_held = None

            elif active_control:
                active_control.handle_input(event)
                if active_control.active == False:
                    active_control = None

        elif event.type == pygame.MOUSEMOTION:
            if active_control:
                active_control.handle_input(event)

                if active_control.active == False:
                    active_control = None

        elif event.type == pygame.KEYDOWN:
            key = str(event.unicode)

            if key in KEYLIST:
                note = KEYLIST.index(key) + octave*12
                button = piano_keys[note]
                note = button._id

                if button.active == False:
                    button.active = True
                    button.kb_has_control = True
                    
                    voice = build_voice(osc1, lfo1, osc2, lfo2, note, freqs, adsr, gen_funcs, mod_funcs)
                    voices = add_voice(voice,retrigger, note, voices_to_release, voices)
                    button.draw()

            elif event.key == pygame.K_DOWN:
                octave -= 1
                if octave < 0:
                    octave = 0
            elif event.key == pygame.K_UP:
                octave += 1
                if octave > 4:
                    octave = 4

        elif event.type == pygame.KEYUP:
            key = str(event.unicode)

            if key in KEYLIST:
                note = KEYLIST.index(key) + octave*12
                button = piano_keys[note]
                note = button._id
                # Should be active; only need to check kb control...
                if button.active and button.kb_has_control:
                    button.active = False
                    button.kb_has_control = False

                    voice_id = voices_to_release[note]
                    # Check that voice is still active (i.e. not stolen) and release it
                    if voice_id in voices.keys():
                        voices[voice_id].release(adsr)

                    button.draw()

    # ---------
    # -- Update
    if voices:
        if filter_lfo.on and filter_lfo._gen:
            filter_lfo.update_control()

        temp_voices = {}
        samples = np.zeros(BUFFER_SIZE)
        for key, voice in voices.items():
            data = voice.get_audio_data(BUFFER_SIZE)

            if voice._release == False:
                samples += data
                temp_voices[key] = voice

            elif voice._release == True:
                if data.sum() != 0:
                    samples += data
                    temp_voices[key] = voice

        voices = temp_voices

        if filter_toggle.active:
            samples = voice_filter.process(samples)

        samples = np.float32(samples*base_gain*adsr['gain'])
        underflow = stream.write(samples)
    else:
        samples = np.float32(np.zeros(BUFFER_SIZE))
        underflow = stream.write(samples)

    if was_under:
        pygame.draw.circle(screen, (255,255,255), (load_led.x, load_led.y), 5)
        was_under = False

    if underflow:
        was_under = True
        pygame.draw.circle(screen, (255,0,0), (load_led.x, load_led.y), 5)


    pygame.display.update()
    clock.tick(FPS)


# eof
