import math

import pygame

from widgets import Knob, ValueBox, DropDownMenu, Button, Toggle
from settings import WIDTH, HEIGHT

class Font:
    '''Font object for setting font parameters used in rendering'''
    def __init__(self, path=None, fontsize=20):
        self.font = pygame.font.Font(path, fontsize)
        self.width = self.font.size("=")[0]
        self.height = self.font.size("=")[1]
        self.render = self.font.render

    def get_height(self):
        return self.height

    def make_text(self, text, x, y, t_color='white', b_color=None):
        '''help Function to make text surface and rect for rendering'''
        text = self.render(text, True, t_color, b_color)
        text_rect = text.get_rect()

        text_rect.centerx = x
        text_rect.y = y

        return [text, text_rect]

# ------ Piano
class PianoKey:
    def __init__(self, x, y, width, height, id_ = None, white_key=True, surface=None):
        super().__init__()
        self._id = id_
        self.active = False
        self.kb_has_control = False

        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        if surface != 'b':
            self.nonactive_surface = pygame.image.load(f"./images/wkey_{surface}.png").convert_alpha()
            self.active_surface = pygame.image.load(f"./images/wkey_{surface}_act.png").convert_alpha()
        else:
            self.nonactive_surface = pygame.image.load(f"./images/bkey.png").convert_alpha()
            self.active_surface = pygame.image.load(f"./images/bkey_act.png").convert_alpha()

    def draw(self):
        surface = pygame.display.get_surface()
        if self.active:
            surface.blit(self.active_surface, self.rect)
        else:
            surface.blit(self.nonactive_surface, self.rect)

# ==================================
def make_amp_adsr(amp_rect, adsr, controls, labels, value_boxes, font):
    knob_text = ['Attack', 'Decay', 'Sustain', 'Release']

    for i, text in enumerate(knob_text):
        knob = Knob(x=amp_rect.x+(i*100), y=amp_rect.y, radius=25, min_val=0)
        label = font.make_text(text, x=knob.rect.centerx, y=knob.rect.centery+30)
        t_format = '{:.3f} s' if text != 'Sustain' else '{:.1%}'
        value_box = ValueBox(
            knob.value,
            x=knob.rect.centerx,
            y=knob.rect.centery+50,
            font=font,
            width=7,
            format=t_format
        )

        knob.add_subscriber(method=value_box.update)
        knob.add_subscriber(obj=adsr, attr=text, is_dict=True)

        controls.append(knob)
        labels.append(label)
        value_boxes.append(value_box)

    knob = Knob(x=amp_rect.x-120, y=amp_rect.y, radius=25, min_val=0)
    label = font.make_text("Gain", x=knob.rect.centerx, y=knob.rect.centery+30)
    value_box = ValueBox(
        knob.value,
        x=knob.rect.centerx,
        y=knob.rect.centery+50,
        font=font,
        width=7,
        format='{:.1%}'
    )

    knob.add_subscriber(method=value_box.update) 
    knob.add_subscriber(obj=adsr, attr='gain', is_dict=True) 

    controls.append(knob)
    labels.append(label)
    value_boxes.append(value_box)

    return controls, labels, value_boxes
# ==================================
def make_lfo_panel(lfo_rect, lfo, controls, labels, value_boxes, font):

    lfo_toggle = Toggle(lfo_rect.x+20, lfo_rect.y+5, 20, 20) # make a toggle button
    lfo_toggle.add_subscriber(obj=lfo, attr='on')
    controls.append(lfo_toggle)

    # -- DropDown
    label = font.make_text("LFO:", x=lfo_rect.x+80, y=lfo_rect.y+5)
    labels.append(label)

    generator_list = ['sine', 'sawtooth', 'triangle', 'pulse']
    drop_menu2 = DropDownMenu(generator_list, lfo_rect.x+120, lfo_rect.y+5, font)
    drop_menu2.add_subscriber(obj=lfo, attr='lfo_func')
    controls.append(drop_menu2)

    # -- Rate
    knob = Knob(x=lfo_rect.x+40, y=lfo_rect.y+60, radius=15, min_val=0.01, max_val=30)
    value_box = ValueBox(knob.value, x=knob.rect.centerx, y=knob.rect.centery+50, font=font, width=8)
    knob.add_subscriber(method=value_box.update)
    knob.add_subscriber(obj=lfo, attr='rate')

    value_boxes.append(value_box)
    controls.append(knob)

    label = font.make_text("Rate", x=knob.rect.centerx, y=knob.rect.centery+30)
    labels.append(label)

    # -- Depth
    knob = Knob(x=lfo_rect.x+150, y=lfo_rect.y+60, radius=15, max_val=200)
    value_box = ValueBox(knob.value, x=knob.rect.centerx, y=knob.rect.centery+50, font=font, width=8)
    knob.add_subscriber(method=value_box.update)
    knob.add_subscriber(obj=lfo, attr='depth')

    value_boxes.append(value_box)
    controls.append(knob)

    label = font.make_text("Depth", x=knob.rect.centerx, y=knob.rect.centery+30)
    labels.append(label)

    # -- Duty
    knob = Knob(x=lfo_rect.x+255, y=lfo_rect.y+60, radius=15, min_val=0, max_val=1)
    value_box = ValueBox(
        knob.value,
        x=knob.rect.centerx,
        y=knob.rect.centery+50,
        font=font,
        width=7,
        format='{:.2%}'
    )
    knob.add_subscriber(method=value_box.update)
    knob.add_subscriber(obj=lfo, attr='duty')

    value_boxes.append(value_box)
    controls.append(knob)

    label = font.make_text("Duty", x=knob.rect.centerx, y=knob.rect.centery+30)
    labels.append(label)

    return controls, labels, value_boxes, lfo

# ==================================
'''Rename Filter LFO'''
def make_lfo2_panel(lfo_rect, lfo, controls, labels, value_boxes, font):

    lfo_toggle = Toggle(lfo_rect.x+20, lfo_rect.y+5, 25, 25) # make a toggle button
    lfo_toggle.add_subscriber(obj=lfo, attr='on')
    controls.append(lfo_toggle)

    # -- DropDown
    label = font.make_text("Filter LFO:", x=lfo_rect.x+110, y=lfo_rect.y+5)
    labels.append(label)

    generator_list = ['sine', 'sawtooth', 'triangle', 'pulse']
    drop_menu2 = DropDownMenu(generator_list, lfo_rect.x+170, lfo_rect.y+5, font)
    drop_menu2.add_subscriber(obj=lfo, attr='lfo_func')
    controls.append(drop_menu2)

    # -- Depth
    knob = Knob(x=lfo_rect.x+160, y=lfo_rect.y+60, radius=20, max_val=200)
    value_box = ValueBox(knob.value, x=knob.rect.centerx, y=knob.rect.centery+50, font=font)
    knob.add_subscriber(method=value_box.update)
    knob.add_subscriber(obj=lfo, attr='depth')

    lfo.depth = knob.value

    value_boxes.append(value_box)
    controls.append(knob)

    label = font.make_text("Depth", x=knob.rect.centerx, y=knob.rect.centery+30)
    labels.append(label)

    # -- Rate
    knob = Knob(x=lfo_rect.x+50, y=lfo_rect.y+60, radius=20, min_val=0.5, max_val=5,)
    value_box = ValueBox(knob.value, x=knob.rect.centerx, y=knob.rect.centery+50, font=font, width=7)
    knob.add_subscriber(method=value_box.update)
    knob.add_subscriber(obj=lfo, attr='rate')
    lfo.rate = knob.value

    value_boxes.append(value_box)
    controls.append(knob)

    label = font.make_text("Rate", x=knob.rect.centerx, y=knob.rect.centery+30)
    labels.append(label)

    return controls, labels, value_boxes, lfo


# ==================================

def make_piano_keys():
    """
    52 white keys
    36 shorter black keys (1/2 size of white keys)
    |  |w| |e|  |  |t| |y| |u|  |
    |a |_|s|_|d |f |_|g|_|h|_|j |
    |___|___|___|___|___|___|___|
    """
    WKEYLIST = ['a','s','d','f','g','h','j']
    BKEYLIST = ['w','e', '', 't','y','u']

    wkey_w = 24
    bkey_w = wkey_w*0.5 #30

    length_set = wkey_w * 7

    # Now make them buttons so they hilite when played
    white_key = pygame.Rect(WIDTH*0.0406, HEIGHT*0.72, wkey_w, 150)
    black_key = pygame.Rect(WIDTH*0.0406+wkey_w*0.75, HEIGHT*0.72, bkey_w, 100)

    is_white = [True, False, True, False, True, True, False, True, False, True, False, True]
    shape = ['left', 'b', 'center', 'b', 'right', 'left', 'b', 'center', 'b', 'center', 'b', 'right']

    wkeys = []
    bkeys = []
    piano_keys = []

    for batch in range(7):
        if batch in [0,6]:
            continue
        wi = 0
        bi = 0
        for i in range(12):
            if shape[i] != 'b': #is_white[i]: #i in [0,2,4,5,7,9,11
                rect = white_key.copy()
                rect.x = rect.x + wkey_w*wi + length_set*batch
                key = PianoKey(rect.x, rect.y, rect.w, rect.h, id_=i+batch*12, surface=shape[i])
                piano_keys.append(key)
                wkeys.append(key)
                wi += 1
                #print(i+batch*12)

            else: #if i in [1,3,6,8,10,11]:
                if bi == 2:
                    bi += 1
                rect = black_key.copy()
                rect.x = rect.x + 2*bkey_w*bi + length_set*batch
                key = PianoKey(
                    rect.x,
                    rect.y,
                    rect.w,
                    rect.h,
                    id_ = i+batch*12,
                    white_key = False,
                    surface=shape[i]
                )
                piano_keys.append(key)
                bkeys.append(key)
                bi += 1

    return wkeys, bkeys, piano_keys


# =================================

def make_osc1(osc, controls, labels, value_boxes, lfo1, font, font2):
    generator_list = ['sine', 'sawtooth', 'triangle', 'pulse', 'noise']

    label = font.make_text("OSC1:", x=osc.rect.x, y=osc.rect.y+5)
    labels.append(label)
    
    drop_menu = DropDownMenu(generator_list, osc.rect.x+40, osc.rect.y+5, font)
    controls.append(drop_menu)
    osc.menu = drop_menu

    knob_gain = Knob(x=osc.rect.x-15, y=osc.rect.centery-15, radius=15, min_val=0.0, max_val=1.0)
    label = font2.make_text("Gain", x=knob_gain.rect.centerx, y=knob_gain.rect.centery+30)
    value_box = ValueBox(
        knob_gain.value,
        x=knob_gain.rect.centerx,
        y=knob_gain.rect.centery+50,
        font=font2,
        width=7,
        format='{:.2%}'
    )
    
    knob_gain.add_subscriber(method=value_box.update)
    knob_gain.add_subscriber(obj=osc, attr='gain')
    
    controls.append(knob_gain)
    labels.append(label)
    value_boxes.append(value_box)
    
    knob = Knob(
        x=osc.rect.right-15, 
        y=osc.rect.centery-15, 
        radius=15, 
        min_val=-12, 
        max_val=12, 
        int_value=True,
        is_neg=True    
    )
    label = font2.make_text("Detune", x=knob.rect.centerx, y=knob.rect.centery+30)
    value_box = ValueBox(
        knob.value,
        x=knob.rect.centerx,
        y=knob.rect.centery+50,
        font=font2,
        width=7,
        format="{:d}"
    )
    
    knob.add_subscriber(method=value_box.update)
    knob.add_subscriber(obj=osc, attr='detune')
    
    controls.append(knob)
    labels.append(label)
    value_boxes.append(value_box)
    
    knobPW = Knob(x=osc.rect.centerx-15, y=osc.rect.centery-15, radius=15, min_val=0.0, max_val=1.0)
    label = font.make_text("Duty", x=knobPW.rect.centerx, y=knobPW.rect.centery+30)
    value_box = ValueBox(
        knobPW.value,
        x=knobPW.rect.centerx,
        y=knobPW.rect.centery+50,
        font=font,
        width=7,
        format='{:.2%}'
    )

    # need way to track control for adding/using later
    knobPW.add_subscriber(method=value_box.update)
    knobPW.add_subscriber(obj=lfo1, attr='pw')
    osc.pw_knob = knobPW

    controls.append(knobPW)
    labels.append(label)
    value_boxes.append(value_box)

    return controls, labels, value_boxes, lfo1, osc


def make_osc2(osc, controls, labels, value_boxes, lfo2, font, font2):
    generator_list = ['sine', 'sawtooth', 'triangle', 'pulse', 'noise']

    osc2_toggle = Toggle(osc.rect.x-35, osc.rect.y+5, 20, 20) # make a toggle button
    controls.append(osc2_toggle)
    osc.toggle = osc2_toggle
    
    label = font.make_text("OSC2:", x=osc.rect.x+22, y=osc.rect.y+5)
    labels.append(label)
    
    drop_menu_osc2 = DropDownMenu(generator_list, osc.rect.x+60, osc.rect.y+5, font)
    controls.append(drop_menu_osc2)
    osc.menu = drop_menu_osc2

    knob_gain = Knob(x=osc.rect.x-15, y=osc.rect.centery-15, radius=15, min_val=0.0, max_val=1.0)
    label = font2.make_text("Gain", x=knob_gain.rect.centerx, y=knob_gain.rect.centery+30)
    value_box = ValueBox(
        knob_gain.value,
        x=knob_gain.rect.centerx,
        y=knob_gain.rect.centery+50,
        font=font2,
        width=7,
        format='{:.2%}'
    )
    
    knob_gain.add_subscriber(method=value_box.update)
    knob_gain.add_subscriber(obj=osc, attr='gain')
    
    controls.append(knob_gain)
    labels.append(label)
    value_boxes.append(value_box)
    
    knob = Knob(
        x=osc.rect.right-15, 
        y=osc.rect.centery-15, 
        radius=15, 
        min_val=-12, 
        max_val=12, 
        int_value=True,
        is_neg=True    
    )
    label = font2.make_text("Detune", x=knob.rect.centerx, y=knob.rect.centery+30)
    value_box = ValueBox(
        knob.value,
        x=knob.rect.centerx,
        y=knob.rect.centery+50,
        font=font2,
        width=7,
        format="{:d}"
    )
    
    knob.add_subscriber(method=value_box.update)
    knob.add_subscriber(obj=osc, attr='detune')
    
    controls.append(knob)
    labels.append(label)
    value_boxes.append(value_box)
    
    knobPW2 = Knob(x=osc.rect.centerx-15, y=osc.rect.centery-15, radius=15, min_val=0.0, max_val=1.0)
    label = font.make_text("Duty", x=knobPW2.rect.centerx, y=knobPW2.rect.centery+30)
    value_box = ValueBox(
        knobPW2.value,
        x=knobPW2.rect.centerx,
        y=knobPW2.rect.centery+50,
        font=font,
        width=7,
        format='{:.2%}'
    )

    knobPW2.add_subscriber(method=value_box.update) # need way to track control for adding later
    knobPW2.add_subscriber(obj=lfo2, attr='pw')
    osc.pw_knob = knobPW2

    controls.append(knobPW2)
    labels.append(label)
    value_boxes.append(value_box)

    return controls, labels, value_boxes, lfo2, osc

# ===============================
def make_filter_box(filter_rect, filter_lfo, voice_filter, controls, labels, value_boxes, font):
    # ----- Filter
    label = font.make_text('Lowpass Filter', x=filter_rect.x+80, y=filter_rect.y+10)
    labels.append(label)

    knobF = Knob(x=filter_rect.x+60, y=filter_rect.y+50, radius=25, max_val=1500)
    value_box = ValueBox(knobF.value, x=knobF.rect.centerx, y=knobF.rect.centery+50, font=font, width=12)

    knobF.add_subscriber(method=value_box.update)
    knobF.add_subscriber(method=voice_filter.set_cutoff)

    label = font.make_text("Cutoff", x=knobF.rect.centerx, y=knobF.rect.centery+30)
    labels.append(label)

    value_boxes.append(value_box)
    controls.append(knobF)

    filter_toggle = Toggle(filter_rect.x+25, filter_rect.y+60, 25, 25) # make a toggle button
    controls.append(filter_toggle) # need to track this...

    # -- Filter LFO
    #filter_lfo = ControlOscillator()
    filter_lfo.control = knobF

    filter_lfo_rect = pygame.Rect(WIDTH*0.50, HEIGHT*0.10, 400, 150)
    filter_lfo.rect = filter_lfo_rect
    controls, labels, value_boxes, filter_lfo = make_lfo2_panel(filter_lfo_rect, filter_lfo,
                                                                controls, labels, value_boxes, font)

    # ---- Center freq knob
    knob = Knob(x=filter_lfo_rect.right-100, y=filter_lfo_rect.y+60, radius=15, max_val=750)
    value_box = ValueBox(
        knob.value,
        x=knob.rect.centerx,
        y=knob.rect.centery+50,
        font=font,
        width=10,
        format = "{:.2f} Hz"

    )

    knob.add_subscriber(obj=filter_lfo, attr='center_freq')
    knob.add_subscriber(method=value_box.update)
    filter_lfo.center_freq = knob.value

    label = font.make_text("Center Freq", x=knob.rect.centerx, y=knob.rect.centery+30)
    labels.append(label)

    value_boxes.append(value_box)
    controls.append(knob)

    return controls, labels, value_boxes, filter_lfo, voice_filter, filter_toggle


# ==============================================================================
def make_voice_controls(controls, labels, value_boxes, font):
    n_voices = {'val': 8}
    knob = Knob(x=110, y=HEIGHT*0.55, radius=20, min_val=1, max_val=16, int_value=True)
    knob.add_subscriber(obj=n_voices, attr='val', is_dict=True)
    n_voices['val'] = knob.value

    value_box = ValueBox(
        knob.value,
        x=knob.rect.centerx,
        y=knob.rect.centery+50,
        font=font,
        width=4,
        format = "{:d}"
        )

    knob.add_subscriber(method=value_box.update)

    label = font.make_text("Voices", x=knob.rect.centerx, y=knob.rect.centery+30)

    controls.append(knob)
    value_boxes.append(value_box)
    labels.append(label)

    retrigger = Toggle(knob.rect.right + 20, knob.rect.centery, 20, 20) # make a toggle button
    label = font.make_text("Retrigger", x=retrigger.rect.right+50, y=retrigger.rect.centery-10)
    retrigger.active = True

    controls.append(retrigger) # need to track this...
    labels.append(label)

    return controls, labels, value_boxes, retrigger, n_voices



#
