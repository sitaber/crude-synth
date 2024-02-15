import math

import pygame

# -----------------------------
class ValueBox:
    def __init__(self, value, x, y, font, width=9, format="{:.2f} Hz"):
        self.font = font
        self.x = x
        self.y = y
        self.rect = pygame.Rect(0, y, font.width*width, font.height)
        self.rect.centerx = x
        self.text_formatter = format
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.update(value)

    def update(self, value):
        text = self.text_formatter.format(value)
        self.text_surf, self.text_rect = self.font.make_text(str(text), self.x, self.y)
        self.draw()

    def draw(self):
        surface = pygame.display.get_surface()
        surface.fill('Black', self.rect)
        surface.blit(self.text_surf, self.text_rect)


# ----------------------------
class Publisher:
    def __init__(self):
        self._subscribers = []
        self.value = None
        self.active = False
        self.updatable = True

    def add_subscriber(self, obj=None, attr=None, method=None, is_dict=False, value=True):
        self._subscribers.append(
            dict(obj=obj, attr=attr, method=method, is_dict=is_dict, value=value)
        )
        return

    def notify_subscribers(self):
        """A bit nicer, can just pass method/function"""
        for subscriber in self._subscribers:

            if subscriber["is_dict"]:
                #subscriber['obj'][subscriber['attr']] = self.value
                dict_ = subscriber.get('obj')
                key = subscriber.get('attr')
                dict_[key] = self.value

            elif subscriber["method"]:
                to_execute = subscriber.get("method")

                if subscriber['value']:
                    to_execute(self.value)
                else:
                    to_execute()
            else:
                setattr(subscriber['obj'], subscriber['attr'], self.value)

        return

# ---------------------------
#           BUTTONS
# ---------------------------
class Button(Publisher):
    def __init__(self, x, y, width, height): 
        super().__init__()
        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = True
        elif event.type == pygame.MOUSEBUTTONUP and self.active:
            self.active = False

        self.draw()

    def update(self):
        pass

    def draw(self):
        surface = pygame.display.get_surface()
        if self.active:
            pygame.draw.rect(surface, 'gray49', self.rect)
        else:
            pygame.draw.rect(surface, 'gray19', self.rect)

class Toggle(Publisher):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.updatable = False
        self.value = False
        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = not self.active
            self.value = self.active

        self.notify_subscribers()
        self.draw()

    def update(self):
        pass

    def draw(self):
        surface = pygame.display.get_surface()
        if self.active:
            pygame.draw.rect(surface, 'red', self.rect)
        else:
            pygame.draw.rect(surface, 'gray19', self.rect)


# ---------------------------
#     Other GUI Widgets
# ---------------------------
class DropDownMenu(Publisher):
    def __init__(self, entries, x, y, font, width=100):
        super().__init__()
        self.active = False
        self.x = x
        self.y = y
        self.font = font

        FONT_HEIGHT = font.get_height()
        self.MENU_HEIGHT = (FONT_HEIGHT+5)*len(entries)
        self.MENU_WIDTH = width

        self.rect = pygame.Rect((x, y, self.MENU_WIDTH, FONT_HEIGHT))
        self.down_rect = pygame.Rect(x, y+FONT_HEIGHT, self.MENU_WIDTH, self.MENU_HEIGHT)
        self.hilite = None

        self.menu = {}
        self.menu_text = entries[0]
        self.value = self.menu_text

        self.under_surf = None

        for idx, text in enumerate(entries):
            result = self.make_text(text, x=self.x, y=(self.y+FONT_HEIGHT)+((FONT_HEIGHT+5)*idx))
            self.menu[text] = result

    def make_text(self, text, x = 10, y = 10, color='White'):
	        text_surf = self.font.render(str(text), True, color)
	        text_rect = text_surf.get_rect(topleft=(x,y))
	        text_rect.width = self.MENU_WIDTH
	        return [text_surf, text_rect]

    def handle_input(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN and self.active == False:
            self.active = True
            surface = pygame.display.get_surface()
            self.under_surf = surface.copy()


        elif event.type == pygame.MOUSEBUTTONDOWN and self.active: # Check for click on menu item
            mouse_rect = pygame.Rect((event.pos),(1,1))
            for text, blits in self.menu.items():
                if mouse_rect.colliderect(blits[1]):
                    self.menu_text = text
                    self.value = self.menu_text

            self.notify_subscribers()
            self.active = False
            self.hilite = None
            self.clear_draw()

        elif event.type == pygame.MOUSEMOTION and self.active:
            mouse_rect = pygame.Rect((event.pos),(1,1))
            # hilite if hovering
            self.hilite = None
            for text, blits in self.menu.items():
                if mouse_rect.colliderect(blits[1]):
                    self.hilite = self.make_text(text, x=blits[1].x, y=blits[1].y, color="Blue")

        self.draw()
        return

    def update(self):
        pass

    def clear_draw(self):
        surface = pygame.display.get_surface()
        surface.blit(self.under_surf, self.down_rect, self.down_rect) 


    def draw(self):
        surface = pygame.display.get_surface()

        pygame.draw.rect(surface, (75,75,75), self.rect) # -- Selected item background
        surface.blit(self.menu[self.menu_text][0], self.rect) # -- The selected menu item text

        if self.active:
            # If drop down button was clicked, show menu items
            pygame.draw.rect(surface, 'Black', self.down_rect)
            surface.blits(list(self.menu.values()))

            if self.hilite:
                pygame.draw.rect(surface, 'grey', self.hilite[1])
                surface.blit(self.hilite[0], self.hilite[1])

        return

# ------------------------------------
class Knob(Publisher):
    def __init__(self, x, y, radius=25, min_val=0.01, max_val=1.0, int_value=False, is_neg=False):
        super().__init__()
        #self.name = name #not used currently
        self.is_neg = is_neg
        self.int_value = int_value
        self.active = False
        self.x = x
        self.y = y

        self.width = radius*2
        self.height = radius*2
        self.radius = radius
        self.circle_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.rect = self.circle_rect

        self.degree = 120+150 # (sets to center)
        self.max_angle = 420 
        self.min_angle = 120 
        self.angle_range = self.max_angle - self.min_angle

        self.max_val = max_val
        self.min_val = min_val
        self.degree_to_value()
        self._make_line()

    def degree_to_value(self):
        self.value = self.max_val * round((self.degree-self.min_angle) / self.angle_range, 4)

        if self.is_neg:
            self.value =  self.value*2 - self.max_val
        if self.int_value:
            self.value = int(self.value)
            
        return

    def _clamp_value(self):
        if self.value > self.max_val:
            self.value = self.max_val
        elif self.value < self.min_val:
            self.value = self.min_val

    def value_to_degree(self):
        self.degree = (self.angle_range *  self.value / self.max_val) + self.min_angle
        return

    def _clamp_angle(self):
        if self.degree >= self.max_angle:
            self.degree = self.max_angle
        elif self.degree <= self.min_angle:
            self.degree = self.min_angle
        return

    def automated_update(self, mod_value):
        self.value = mod_value
        self._clamp_value()
        self.value_to_degree()
        self._clamp_angle()
        self._make_line()
        self.draw()
        self.notify_subscribers()
        return

    def update(self):
        _, my = pygame.mouse.get_pos() 
        delta_y = self.start_y - my
        self.start_y = my
        self.degree = self.degree+delta_y
        self._clamp_angle()
        self.degree_to_value()
        self._clamp_value()

        self._make_line()
        self.draw()
        self.notify_subscribers()
        return

    def _make_line(self, delta_y=0):
        rad = math.radians(self.degree)
        self.line_x = self.circle_rect.centerx + self.radius * math.cos(rad)
        self.line_y = self.circle_rect.centery + self.radius * math.sin(rad)
        self.degree = math.degrees(rad)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.active == False:
            self.start_y = event.pos[1]
            self.active = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.active = False

        elif event.type == pygame.MOUSEMOTION and self.active:
            self.update()

    def draw(self):
        surface = pygame.display.get_surface()
        pygame.draw.rect(surface, 'gray49', self.rect)
        pygame.draw.circle(surface, 'Black', self.circle_rect.center, self.radius)
        pygame.draw.line(surface, 'White', self.circle_rect.center, (self.line_x, self.line_y), 3)

        return

#
