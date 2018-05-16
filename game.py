import random, logging, math, sys, os
from os import path
from datetime import datetime, timedelta
from expressions import Expression
from pygame.locals import Color
from collections import namedtuple
try:
    import pygame, pygame_textinput, ptext
except ImportError as e:
    if __name__ == '__main__':
        raise e
    pygame = None
    pygame_textinput = None
    ptext = None

WHITE = Color('white')
FOREGROUND_COLOR = (0, 255, 0)
BACKGROUND_COLOR = Color('black')
MUSIC_VOLUME = 0.75
QUESTION_LENGTH = 20
TWO_PI = math.pi * 2

def getfile(filename):
    if getattr(sys, 'frozen', False):
        datadir = os.path.dirname(sys.executable)
    else:
        datadir = os.path.dirname(__file__)

    return os.path.join(datadir, filename)

def removeif(pred, data):
    i = 0
    while i < len(data):
        if pred(data[i]):
            del data[i]
        else:
            i += 1
            
def distance(x, y, x2, y2):
    return math.hypot(x - x2, y - y2)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger('quickderiv-game')
disco_dech_chrome = getfile('discodeckchrome.ttf')
blood_dragon_theme = getfile('blood-dragon-theme.mp3')
Question = namedtuple('Question', 'y y_prime')

class Audio:
    def __init__(self):
        self.zap = pygame.mixer.Sound(getfile('zap.wav'))
        self.select = pygame.mixer.Sound(getfile('select.wav'))
        self.bad = pygame.mixer.Sound(getfile('bad.wav'))

class Star:
    def __init__(self, x, y, x_speed, y_speed, size=1):
        self.x = x
        self.y = y
        self.x_speed = x_speed
        self.y_speed = y_speed

    def draw(self, surface, color=FOREGROUND_COLOR):
        surface.set_at((int(self.x), int(self.y)), color)

    def update(self, surface_width, surface_height, correct_delta):
        mul = max(4 - correct_delta.total_seconds(), 0)
        self.x += self.x_speed * mul / 3
        self.y -= mul * surface_height / abs(surface_height - self.y)
        return self.y < 0 or self.y > surface_height or self.x < 0 or self.x > surface_width

class HorizontalLine:
    def __init__(self, y, size=1):
        self.y = y

    def draw(self, surface, color=FOREGROUND_COLOR):
        pygame.draw.line(surface, FOREGROUND_COLOR, (0, self.y), (surface.get_width(), self.y))

    def update(self, surface_height, last_correct):
        if self.y >= surface_height:
            self.y = surface_height / 2
        self.y += max(4 - last_correct.total_seconds(),
                      0) * surface_height / abs(surface_height - self.y) / 2

class Fade:
    def __init__(self, resolution):
        self.surface = pygame.Surface(resolution)
        self.surface.convert_alpha()
        self.surface.fill(BACKGROUND_COLOR)

    def reset(self, showing=False):
        self.surface.set_alpha(0 if showing else 255)

    def fade_in(self, speed=5):
        self.surface.set_alpha(max(self.surface.get_alpha() - 5, 0))

    def fade_out(self, speed=5):
        self.surface.set_alpha(min(self.surface.get_alpha() + 5, 255))

    def is_complete(self, showing=False):
        alpha = self.surface.get_alpha()
        return alpha == 0 if showing else alpha == 255

    def blit_onto(self, surface):
        alpha = self.surface.get_alpha()
        if alpha == 255:
            surface.fill(BACKGROUND_COLOR)
        elif alpha > 0:
            surface.blit(self.surface, (0, 0))

class State:
    def __init__(self, label, previous_state, audio):
        self.label = label
        self.previous_state = previous_state
        self.audio = audio

    def initialize(self):
        pass
        
    def update(self, events, screen, width, height):
        raise NotImplemented()

    def __str__(self):
        return self.label

class MenuState(State):
    QUALITY_HIGH = 'Quality: High'
    QUALITY_LOW = 'Quality: Low'
    MUSIC_ON = 'Music: ON'
    MUSIC_OFF = 'Music: OFF'
    
    def __init__(self, resolution, audio):
        State.__init__(self, 'Menu', None, audio)
        self.title_overlay = pygame.transform.scale(
            pygame.image.load(getfile('quickderiv-title.png')),
            resolution).convert_alpha()
        self.title_gradient = pygame.transform.scale(
            pygame.image.load(getfile('quickderiv-title-gradient.png')),
            (resolution[0], int(194 * (resolution[1] / 720)))).convert_alpha()
        self.fade = Fade(resolution)
        self.state_options = [PlayingState(self, resolution, self.audio),
                              self.QUALITY_HIGH,
                              self.MUSIC_ON,
                              self.previous_state]
        self.initialize()

    def initialize(self):
        self.selection = 0
        self.menu_offset = 0
        self.modtick = 0
        self.closing = False
        self.update_state_options()
        self.fade.reset()

    def update_state_options(self):
        self.state_options[1] = self.QUALITY_LOW if self.state_options[0].low_graphics\
                                else self.QUALITY_HIGH
        self.state_options[2] = self.MUSIC_ON if pygame.mixer.music.get_volume() == MUSIC_VOLUME\
                                else self.MUSIC_OFF

    def get_selection(self):
        return self.state_options[self.selection]
        
    def update(self, events, screen, width, height):
        selected_item = self.get_selection()
        
        if not self.closing:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    self.audio.select.play()
                    if event.key == pygame.K_RETURN:
                        if selected_item in (self.QUALITY_HIGH, self.QUALITY_LOW):
                            self.state_options[0].low_graphics = not self.state_options[0].low_graphics
                            self.update_state_options()
                        elif selected_item == self.MUSIC_ON:
                            pygame.mixer.music.set_volume(0)
                            self.update_state_options()
                        elif selected_item == self.MUSIC_OFF:
                            pygame.mixer.music.set_volume(MUSIC_VOLUME)
                            self.update_state_options()
                        else:
                            self.closing = True
                    elif event.key == pygame.K_UP:
                        self.selection = (self.selection - 1) % len(self.state_options)
                    elif event.key == pygame.K_DOWN:
                        self.selection = (self.selection + 1) % len(self.state_options)

        half_width = int(width / 2)
        half_height = int(height / 2)

        screen.fill(BACKGROUND_COLOR)
        screen.blit(self.title_gradient, (0, int(263 * (height / 720))))

        selected_str = str(selected_item) if selected_item is not None else 'Exit'
        sine = math.sin(self.modtick) * 5
        ptext.draw(f'>  {2 * len(selected_str) * " "}',
                   fontname=disco_dech_chrome,
                   fontsize=90,
                   strip=False,
                   color=FOREGROUND_COLOR,
                   center=(half_width - sine, half_height),
                   surf=screen)
        ptext.draw(f'{2 * len(selected_str) * " "}  <',
                   fontname=disco_dech_chrome,
                   fontsize=90,
                   strip=False,
                   color=FOREGROUND_COLOR,
                   center=(half_width + sine, half_height),
                   surf=screen)
        for i, option in enumerate(self.state_options):
            ptext.draw(str(option) if option is not None else 'Exit',
                       center=(half_width, half_height + (i * 90) - self.menu_offset),
                       fontname=disco_dech_chrome,
                       fontsize=90,
                       color=FOREGROUND_COLOR,
                       surf=screen)
            
        screen.blit(self.title_overlay, (0, 0))
        self.fade.blit_onto(screen)
        if self.closing:
            self.fade.fade_out()
            if self.fade.is_complete():
                if selected_item is not None:
                    selected_item.initialize()
                return selected_item
        else:
            self.fade.fade_in()

        self.modtick = (self.modtick + 0.1) % TWO_PI
        self.menu_offset += ((self.selection * 90) - self.menu_offset) * 0.25
        return self

class GameOverState(State):
    def __init__(self, score, questions, menu_state, resolution, audio):
        State.__init__(self, 'Game Over', menu_state, audio)
        self.questions = questions
        self.questions.reverse()
        self.score = score
        self.side_gradient = pygame.transform.scale(
            pygame.image.load(getfile('quickderiv-side-gradient.png')),
            resolution).convert_alpha()
        self.fade = Fade(resolution)
        self.initialize()

    def initialize(self):
        self.question_index = 0
        self.question_offset = 0
        self.modtick = 0
        self.closing = False
        self.fade.reset()

    def update(self, events, screen, width, height):
        if not self.closing:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    self.audio.select.play()
                    if event.key == pygame.K_RETURN:
                        self.closing = True
                    elif event.key == pygame.K_LEFT:
                        self.question_index = (self.question_index - 1) % len(self.questions)
                    elif event.key == pygame.K_RIGHT:
                        self.question_index = (self.question_index + 1) % len(self.questions)

        half_width = int(width / 2)
        half_height = int(height / 2)
        sine = math.sin(self.modtick) * 5

        screen.fill(BACKGROUND_COLOR)

        ptext.draw('Game Over',
                   midbottom=(half_width, half_height / 2),
                   fontname=disco_dech_chrome,
                   fontsize=90,
                   color=FOREGROUND_COLOR,
                   surf=screen)
        ptext.draw(f'Score: {self.score}',
                   midbottom=(half_width, (half_height / 2) + 45),
                   fontsize=54,
                   color=FOREGROUND_COLOR,
                   surf=screen)
        ptext.draw(f'Review ({self.question_index + 1}/{len(self.questions)})',
                   midtop=(half_width, (half_height / 2) + 70),
                   fontsize=24,
                   color=FOREGROUND_COLOR,
                   surf=screen)

        for i, question in enumerate(self.questions):
            x = half_width + (i * half_width) - self.question_offset
            if x > width:
                continue
            text = f'y = {question.y}\ny\' = {question.y_prime}'
            if i == 0:
                text = 'The correct answer was:\n' + text
            ptext.draw(text,
                       center=(x, half_height),
                       fontsize=48,
                       color=FOREGROUND_COLOR,
                       surf=screen)

        screen.blit(self.side_gradient, (0, 0))

        if self.question_index < len(self.questions) - 1:
            ptext.draw('>',
                       fontname=disco_dech_chrome,
                       fontsize=90,
                       color=FOREGROUND_COLOR,
                       midright=(width - sine - 30, half_height),
                       surf=screen)
        if self.question_index > 0:
            ptext.draw('<',
                       fontname=disco_dech_chrome,
                       fontsize=90,
                       color=FOREGROUND_COLOR,
                       center=(sine + 30, half_height),
                       surf=screen)

        self.fade.blit_onto(screen)
        if self.closing:
            self.fade.fade_out()
            if self.fade.is_complete():
                return self.previous_state
        else:
            self.fade.fade_in()
        
        self.modtick = (self.modtick + 0.1) % TWO_PI
        self.question_offset += ((self.question_index * half_width) - self.question_offset) * 0.25
        return self

class PlayingState(State):
    def __init__(self, previous_state, resolution, audio):
        State.__init__(self, 'Play', previous_state, audio)
        self.stars = list()
        self.lines = list()
        self.low_graphics = False
        self.inputbox = pygame_textinput.TextInput(
            before_string="y' = ",
            cursor_color=WHITE,
            text_color=WHITE)
        self.fade = Fade(resolution)
        self.initialize()

    def _make_next_time(self, seconds=15, now=None):
        if now is None:
            now = datetime.now()
        return now + timedelta(seconds=seconds)

    def _make_question_part(self):
        part = random.randint(0, 5)
        if part == 0:
            return str(random.randint(1, 20))
        elif part == 1:
            return f'{random.randint(2, 20)} * x'
        elif part == 2:
            return f'{random.randint(2, 10)} * x ^ {random.randint(2, 5)}'
        elif part == 3:
            return 'x'
        else:
            return f'x ^ {random.randint(2, 5)}'

    def _make_question(self):
        exp = Expression(parse=' + '.join([self._make_question_part() for i in range(3)]))
        der = exp.differentiate()
        der.collect_terms()
        return Question(exp, der)

    def initialize(self):
        self.score = 0
        self.question_length = QUESTION_LENGTH
        self.questions = [None]
        self.stars.clear()
        self.lines.clear()
        self.inputbox.clear_text()
        self.fade.reset()
        self.opening = True
        self.closing = False
        self.reset_times()

    def reset_times(self, now=None):
        if now is None:
            now = datetime.now()
        self.next_time = self._make_next_time(self.question_length, now)
        self.last_correct = now

    def update(self, events, screen, width, height):
        if not self.closing and not self.opening\
           and self.inputbox.update(events) and self.questions[-1]:
            try:
                entered = Expression(parse=self.inputbox.get_text())
                entered.collect_terms()
            except:
                entered = None
            self.inputbox.clear_text()
            if entered == self.questions[-1].y_prime:
                self.score += 1
                logger.info(f"Answer correct: y' = {self.questions[-1][1]}")
                self.questions.append(None)
                self.next_time = self._make_next_time(self.question_length)
                logger.info(f'Timer reset to {self.question_length} seconds')
                self.question_length = max(self.question_length - 0.5, 5)
                self.audio.zap.play()
                self.last_correct = datetime.now()
            else:
                logger.info(f'Answer incorrect')
                self.audio.bad.play()

        if not self.closing and not self.opening and self.next_time < datetime.now():
            logger.info(f"Timed out, the correct answer was: y' = {self.questions[-1][1]}")
            self.closing = True

        if not self.questions[-1]:
            self.questions[-1] = self._make_question()
            logger.info(f'Question presented: y = {self.questions[-1][0]}')

        half_width = int(width / 2)
        half_height = int(height / 2 - 1)

        screen.fill(BACKGROUND_COLOR)

        now = datetime.now()
        correct_delta = now - self.last_correct

        # Draw stars
        for star in self.stars:
            star.draw(screen)
            
        removeif(lambda x: x.update(width, height, now - self.last_correct), self.stars)

        # X grid
        if not self.lines:
            self.lines.append(HorizontalLine(half_height, width))
            self.lines.append(HorizontalLine(half_height + (half_height / 2), width))
            self.lines.append(HorizontalLine(half_height + (half_height / 4), width))
            self.lines.append(HorizontalLine(half_height + (half_height / 8), width))
        for line in self.lines:
            line.draw(screen)
            line.update(height, correct_delta)

        # Y grid
        for i in range(-width * 100, half_width, 1000):
            pygame.draw.line(screen, FOREGROUND_COLOR, (half_width, half_height), (i, height))
            pygame.draw.line(screen, FOREGROUND_COLOR,
                             (half_width, half_height), (width - i, height))

        # Horizon
        pygame.draw.line(screen, FOREGROUND_COLOR, (0, half_height), (width, half_height))

        # Time left
        bar_length = width if self.opening else width * (
            self.next_time - datetime.now()).total_seconds() / self.question_length
        screen.fill(FOREGROUND_COLOR, pygame.Rect(0, height - 10, int(bar_length), 10))

        # Question 'glitchy' text
        if not self.low_graphics:
            for i in range(3):
                ptext.draw(f'y = {self.questions[-1].y}',
                           midtop=(half_width + random.randint(-5, 5),
                                   (half_height / 2) + random.randint(-5, 5)),
                           alpha=0.2,
                           fontsize=54,
                           surf=screen)
                
        # Question text
        ptext.draw(f'y = {self.questions[-1].y}',
                   midtop=(half_width, half_height / 2),
                   fontsize=54,
                   surf=screen)

        # Score text
        ptext.draw(f'Score: {self.score}',
                   midbottom=(half_width, (half_height / 2) - 10),
                   surf=screen)

        # Input text
        intext = self.inputbox.get_surface()
        screen.blit(intext, intext.get_rect(center=(width / 2, height / 2 - 30)))

        # Add stars
        for i in range(int((0.5 if self.low_graphics else 2) *
                           max(4 - correct_delta.total_seconds(), 0))):
            x_speed = random.uniform(-40, 40)
            y_speed = random.uniform(2, 10)
            self.stars.append(Star(half_width,
                                   half_height,
                                   x_speed,
                                   abs(y_speed - abs(x_speed / 2)) + 1,
                                   self))

        self.fade.blit_onto(screen)
        if self.opening:
            self.fade.fade_in()
            if self.fade.is_complete(True):
                self.opening = False
                self.reset_times()
        elif self.closing:
            self.fade.fade_out()
            if self.fade.is_complete():
                return GameOverState(self.score, self.questions, self.previous_state,
                                     (width, height), self.audio)
                
        return self

def is_playable():
    return pygame and pygame_textinput and ptext

def play(resolution=(1080, 720), flags=0):
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption('ex0dus quickderiv')
    WIDTH, HEIGHT = resolution
    CENTER = (WIDTH / 2, HEIGHT / 2)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    screen.set_alpha(None)
    pygame.key.set_repeat(100, 100)
    clock = pygame.time.Clock()
    audio = Audio()
    pygame.mixer.music.load(blood_dragon_theme)
    pygame.mixer.music.set_volume(MUSIC_VOLUME)
    pygame.mixer.music.play(-1)
    state = MenuState(resolution, audio)
    logger.info('Game started')
    while state:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                state = None
                break
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                logger.info(f'Escaped state: {state} -> {state.previous_state}')
                audio.bad.play()
                state = state.previous_state
                if state is not None:
                    state.initialize()
                break
            
        else:
            update = state.update(events, screen, WIDTH, HEIGHT)
            if state is not update:
                logger.info(f'State: {state} -> {update}')
                state = update
                if state is not None:
                    state.initialize()
            if update:
                pygame.display.update()
                clock.tick_busy_loop(60)

    pygame.mixer.quit()
    pygame.quit()
    logger.info('Game ended')

def install_dependencies():
    if not is_playable():
        import pip
        pip.main(['install', 'pygame'])
        
if __name__ == '__main__':
    install_dependencies()
    play()
