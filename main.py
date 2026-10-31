# Flappy Bird - Pygame version (works on desktop and in the browser with pygbag)
# Controls: SPACE or left mouse click / tap = flap, ESC = quit (desktop only)
# Images must be inside a folder named "images" next to this file.
# Sounds (.ogg) must be inside a folder named "sounds" next to this file.

import asyncio
import os
import random

import pygame

pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass   # no sound device: the game still works without sound

# ---------- Settings ----------
WIDTH = 400           # same size as the first version
HEIGHT = 600
FPS = 60

GRAVITY = 0.5
FLAP_STRENGTH = -8
PIPE_WIDTH = 80       # width of the pipe head (in pixels)
PIPE_GAP = 170
PIPE_SPEED = 3
PIPE_DISTANCE = 230   # horizontal distance between two pipes
BIRD_X = 80
SKY_SPEED = 0.15      # the sky is slower than the clouds

MUSIC_VOLUME = 0.2    # background music volume while playing (0.0 - 1.0)
MENU_MUSIC_VOLUME = 0.08   # quieter music before the game starts
VOLUME_FADE_SPEED = 0.08   # how fast the music volume changes (per second)
GAMEOVER_FADE_MS = 1500    # the game over sound fades out in this time on restart
RESTART_DELAY_MS = 700     # after losing, wait a bit so you can see what you hit

BIRD_FRAME_MS = 40         # how long each frame of the bird animation is shown
GAME_OVER_FRAME = 0        # the bird freezes on this frame after losing (wings down)
SFX_VOLUME = 0.8      # volume of the sound effects
FLAP_VOLUME = 0.25    # volume of the wing flap sound
GAMEOVER_VOLUME = 0.45  # the game over sound is quieter than the other effects
SCORE_SOUND_EVERY = 10  # play the score sound every 10 points

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

# the default pygame font works everywhere (also in the browser)
font_big = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 32)
font_small = pygame.font.Font(None, 30)

# ---------- Load images ----------
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = "."


def load_image(name, width):
    # load a png and resize it to the given width (keeps the ratio)
    path = os.path.join(BASE_DIR, "images", name)
    image = pygame.image.load(path).convert_alpha()
    height = round(image.get_height() * width / image.get_width())
    return pygame.transform.smoothscale(image, (width, height))


# the sky is a wide picture (800x600) that moves slowly and repeats
sky_img = pygame.image.load(os.path.join(BASE_DIR, "images", "sky.png")).convert()
SKY_W = sky_img.get_width()

ground_img = pygame.image.load(os.path.join(BASE_DIR, "images", "ground.png")).convert_alpha()
GROUND_TILE_W = ground_img.get_width()
GRASS_OFFSET = 17    # distance from the top of the ground image to the grass line
# the bird dies when it touches the grass line
GROUND_HEIGHT = ground_img.get_height() - GRASS_OFFSET

# the bird is an animation (converted from a gif): all frames are in one
# picture, next to each other. Every frame is 48 pixels wide.
BIRD_FRAME_W = 48
bird_sheet = pygame.image.load(os.path.join(BASE_DIR, "images", "bird_sheet.png")).convert_alpha()
BIRD_FRAME_H = bird_sheet.get_height()
bird_frames = [
    bird_sheet.subsurface((i * BIRD_FRAME_W, 0, BIRD_FRAME_W, BIRD_FRAME_H)).copy()
    for i in range(bird_sheet.get_width() // BIRD_FRAME_W)
]
pygame.display.set_icon(bird_frames[0])   # small bird icon in the window corner
cloud_files = ["cloud1.png", "cloud2.png"]

# The pipe images are long, but the gap position changes every time.
# So we cut each pipe image into two parts:
#   1) the head (the wide part at the end of the pipe)
#   2) a thin strip of the body which we stretch to any height
pipe_top_full = load_image("pipe_top.png", PIPE_WIDTH)
pipe_bottom_full = load_image("pipe_bottom.png", PIPE_WIDTH)

# numbers measured from the original images (image width = 192 px)
HEAD_H = round(83 * PIPE_WIDTH / 192)      # height of the head
BODY_X = round(18 * PIPE_WIDTH / 192)      # body starts a bit inside the head
BODY_W = round(156 * PIPE_WIDTH / 192)     # body is narrower than the head

# top pipe: head is at the bottom of the image
top_head_img = pipe_top_full.subsurface(
    (0, pipe_top_full.get_height() - HEAD_H, PIPE_WIDTH, HEAD_H)).copy()
top_strip = pipe_top_full.subsurface((BODY_X, 50, BODY_W, 6)).copy()

# bottom pipe: head is at the top of the image
bottom_head_img = pipe_bottom_full.subsurface((0, 0, PIPE_WIDTH, HEAD_H)).copy()
bottom_strip = pipe_bottom_full.subsurface((BODY_X, 70, BODY_W, 6)).copy()


# ---------- Sounds ----------
def load_sound(name, volume=SFX_VOLUME):
    # returns None if the sound can not be loaded, so the game never crashes
    try:
        sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "sounds", name))
        sound.set_volume(volume)
        return sound
    except Exception:
        return None


def play_sound(sound):
    if sound is not None:
        sound.play()


score_sound = load_sound("score.ogg")
hit_sound = load_sound("hit.ogg")
gameover_sound = load_sound("gameover.ogg", GAMEOVER_VOLUME)
flap_sound = load_sound("flap.ogg", FLAP_VOLUME)


def fade_out_sound(sound, ms):
    # slowly lower the volume of a sound until it stops
    if sound is not None:
        try:
            sound.fadeout(ms)
        except Exception:
            pass


music_volume = 0.0    # the volume the music has right now
music_target = 0.0    # the volume the music is moving towards


def start_music(target):
    # background music loops forever; it starts silent and fades in to "target"
    global music_volume, music_target
    try:
        pygame.mixer.music.load(os.path.join(BASE_DIR, "sounds", "music.ogg"))
        music_volume = 0.0
        music_target = target
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)
    except Exception:
        pass


def set_music_target(target):
    global music_target
    music_target = target


def update_music(dt):
    # move the music volume a little bit towards the target (smooth fade)
    global music_volume
    if music_volume == music_target:
        return
    step = VOLUME_FADE_SPEED * dt
    if music_volume < music_target:
        music_volume = min(music_target, music_volume + step)
    else:
        music_volume = max(music_target, music_volume - step)
    try:
        pygame.mixer.music.set_volume(music_volume)
    except Exception:
        pass


def stop_music():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


# ---------- Best score (saved between runs) ----------
def score_file():
    # On Windows the game can be installed in a folder where it is not allowed
    # to write files, so the score is saved in the user's AppData folder.
    # Anywhere else (or if that fails) it is saved next to main.py.
    appdata = os.environ.get("APPDATA")
    if appdata:
        try:
            folder = os.path.join(appdata, "FlappyBird")
            os.makedirs(folder, exist_ok=True)
            return os.path.join(folder, "highscore.txt")
        except Exception:
            pass
    return os.path.join(BASE_DIR, "highscore.txt")


def load_high_score():
    # in the browser we use localStorage, on desktop a small text file
    try:
        import platform
        value = platform.window.localStorage.getItem("flappy_best")
        return int(value) if value else 0
    except Exception:
        pass
    try:
        with open(score_file()) as f:
            return int(f.read())
    except Exception:
        return 0


def save_high_score(value):
    try:
        import platform
        platform.window.localStorage.setItem("flappy_best", str(value))
        return
    except Exception:
        pass
    try:
        with open(score_file(), "w") as f:
            f.write(str(value))
    except Exception:
        pass


# ---------- Bird class ----------
class Bird:
    def __init__(self):
        self.x = BIRD_X
        self.y = HEIGHT // 2
        self.radius = 16      # hitbox is a bit smaller than the image
        self.velocity = 0
        self.anim_time = 0    # milliseconds, decides which animation frame we show
        self.frozen = False   # True after losing: the wings stop moving

    def animate(self, dt):
        if not self.frozen:
            self.anim_time += dt * 1000

    def flap(self):
        self.velocity = FLAP_STRENGTH

    def update(self):
        # gravity pulls the bird down every frame
        self.velocity += GRAVITY
        self.y += self.velocity

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

    def draw(self):
        # tilt the bird: up when flapping, down when falling
        angle = -self.velocity * 3
        if self.frozen:
            frame = GAME_OVER_FRAME
        else:
            frame = int(self.anim_time / BIRD_FRAME_MS) % len(bird_frames)
        rotated = pygame.transform.rotate(bird_frames[frame], angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated, rect)


# ---------- Pipe class ----------
class Pipe:
    def __init__(self, x):
        self.x = x
        # random position of the gap
        self.gap_y = random.randint(160, HEIGHT - GROUND_HEIGHT - 160)
        self.passed = False   # used for scoring

        self.gap_top = self.gap_y - PIPE_GAP // 2
        self.gap_bottom = self.gap_y + PIPE_GAP // 2

        # stretch the body strips to the height we need
        self.top_body_h = self.gap_top - HEAD_H
        self.bottom_body_y = self.gap_bottom + HEAD_H
        self.bottom_body_h = HEIGHT - self.bottom_body_y
        self.top_body = pygame.transform.scale(top_strip, (BODY_W, self.top_body_h))
        self.bottom_body = pygame.transform.scale(bottom_strip, (BODY_W, self.bottom_body_h))

    def update(self):
        self.x -= PIPE_SPEED

    def get_rects(self):
        # 4 rectangles: head + body for the top and the bottom pipe
        top_head = pygame.Rect(self.x, self.gap_top - HEAD_H, PIPE_WIDTH, HEAD_H)
        top_body = pygame.Rect(self.x + BODY_X, 0, BODY_W, self.top_body_h)
        bottom_head = pygame.Rect(self.x, self.gap_bottom, PIPE_WIDTH, HEAD_H)
        bottom_body = pygame.Rect(self.x + BODY_X, self.bottom_body_y, BODY_W, self.bottom_body_h)
        return [top_head, top_body, bottom_head, bottom_body]

    def draw(self):
        screen.blit(self.top_body, (self.x + BODY_X, 0))
        screen.blit(top_head_img, (self.x, self.gap_top - HEAD_H))
        screen.blit(self.bottom_body, (self.x + BODY_X, self.bottom_body_y))
        screen.blit(bottom_head_img, (self.x, self.gap_bottom))

    def is_off_screen(self):
        return self.x + PIPE_WIDTH < 0


# ---------- Cloud class ----------
class Cloud:
    def __init__(self, x):
        # pick a random cloud image and a random size
        self.image = load_image(random.choice(cloud_files), random.randint(80, 140))
        self.x = x
        self.y = random.randint(20, 250)
        self.speed = random.uniform(0.3, 1.0)

    def update(self):
        self.x -= self.speed
        # when the cloud leaves the screen, put it back on the right side
        if self.x + self.image.get_width() < 0:
            self.x = WIDTH + random.randint(0, 100)
            self.y = random.randint(20, 250)

    def draw(self):
        screen.blit(self.image, (self.x, self.y))


# ---------- Helper functions ----------
def draw_ground(ground_x):
    # draw the same tile several times next to each other
    y = HEIGHT - ground_img.get_height()
    x = ground_x
    while x < WIDTH:
        screen.blit(ground_img, (x, y))
        x += GROUND_TILE_W


def draw_text(text, font, color, center=None, topleft=None):
    # draw a dark shadow first so the text is readable on top of clouds
    shadow = font.render(text, True, BLACK)
    surface = font.render(text, True, color)
    if center is not None:
        rect = surface.get_rect(center=center)
    else:
        rect = surface.get_rect(topleft=topleft)
    screen.blit(shadow, (rect.x + 2, rect.y + 2))
    screen.blit(surface, rect)


def check_collision(bird, pipes):
    bird_rect = bird.get_rect()

    # hit the ground or fly out of the top
    if bird.y + bird.radius >= HEIGHT - GROUND_HEIGHT:
        return True
    if bird.y - bird.radius <= 0:
        return True

    # hit a pipe
    for pipe in pipes:
        for rect in pipe.get_rects():
            if bird_rect.colliderect(rect):
                return True
    return False


def reset_game():
    bird = Bird()
    pipes = [Pipe(WIDTH + 100)]
    return bird, pipes, 0


# ---------- Main game ----------
# The loop is async because pygbag (browser version) needs it.
# On a normal PC it works the same way.
async def main():
    bird, pipes, score = reset_game()
    clouds = [Cloud(random.randint(0, WIDTH)) for _ in range(4)]
    ground_x = 0
    sky_x = 0
    high_score = load_high_score()
    state = "start"   # "start", "playing", "game_over"
    game_over_time = 0
    dt = 0
    start_music(MENU_MUSIC_VOLUME)   # quiet music on the start screen

    while True:
        # ----- Events -----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            flap_pressed = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_SPACE:
                    flap_pressed = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                flap_pressed = True

            if flap_pressed:
                if state == "start":
                    state = "playing"
                    bird.flap()
                    play_sound(flap_sound)
                    set_music_target(MUSIC_VOLUME)   # music gets louder
                elif state == "playing":
                    bird.flap()
                    play_sound(flap_sound)
                elif state == "game_over":
                    # ignore clicks for a short time, so the scene stays visible
                    if pygame.time.get_ticks() - game_over_time >= RESTART_DELAY_MS:
                        bird, pipes, score = reset_game()
                        state = "start"
                        fade_out_sound(gameover_sound, GAMEOVER_FADE_MS)
                        start_music(MENU_MUSIC_VOLUME)

        # ----- Update -----
        update_music(dt)

        # clouds move in every state
        for cloud in clouds:
            cloud.update()

        # the sky moves slowly in every state
        sky_x -= SKY_SPEED
        if sky_x <= -SKY_W:
            sky_x += SKY_W

        # the bird flaps its wings before the game and while playing
        # (after losing it stays frozen)
        if state != "game_over":
            bird.animate(dt)

        if state == "playing":
            # the ground scrolls only while the bird is alive
            ground_x -= PIPE_SPEED
            if ground_x <= -GROUND_TILE_W:
                ground_x += GROUND_TILE_W

            bird.update()

            for pipe in pipes:
                pipe.update()

                # bird passed the pipe -> +1 score
                if not pipe.passed and pipe.x + PIPE_WIDTH < bird.x:
                    pipe.passed = True
                    score += 1
                    if score % SCORE_SOUND_EVERY == 0:
                        play_sound(score_sound)
                    # the best score is updated live
                    if score > high_score:
                        high_score = score

            # add a new pipe when the last one is far enough
            if pipes[-1].x < WIDTH - PIPE_DISTANCE:
                pipes.append(Pipe(WIDTH))

            # remove pipes that left the screen
            pipes = [p for p in pipes if not p.is_off_screen()]

            if check_collision(bird, pipes):
                state = "game_over"
                game_over_time = pygame.time.get_ticks()
                bird.frozen = True
                save_high_score(high_score)
                stop_music()
                play_sound(hit_sound)
                play_sound(gameover_sound)

        # ----- Draw -----
        # order matters: sky -> clouds -> pipes -> ground -> bird
        screen.blit(sky_img, (int(sky_x), 0))
        screen.blit(sky_img, (int(sky_x) + SKY_W, 0))

        for cloud in clouds:
            cloud.draw()
        for pipe in pipes:
            pipe.draw()
        draw_ground(ground_x)
        bird.draw()

        if state == "start":
            draw_text("Flappy Bird", font_big, WHITE, center=(WIDTH // 2, 200))
            draw_text("Press SPACE or click to start", font_medium, WHITE, center=(WIDTH // 2, 270))
            # the best score is shown only here, before the game starts
            draw_text("Best Score: " + str(high_score), font_medium, WHITE, center=(WIDTH // 2, 320))

        elif state == "playing":
            draw_text(str(score), font_big, WHITE, center=(WIDTH // 2, 60))

        elif state == "game_over":
            draw_text("Game Over", font_big, WHITE, center=(WIDTH // 2, 200))
            draw_text("Score: " + str(score), font_medium, WHITE, center=(WIDTH // 2, 260))
            draw_text("Best Score: " + str(high_score), font_medium, WHITE, center=(WIDTH // 2, 300))
            if score > 0 and score == high_score:
                draw_text("New best score!", font_medium, WHITE, center=(WIDTH // 2, 340))
            if pygame.time.get_ticks() - game_over_time >= RESTART_DELAY_MS:
                draw_text("Press SPACE or click to restart", font_medium, WHITE, center=(WIDTH // 2, 395))

        pygame.display.flip()
        dt = min(clock.tick(FPS) / 1000, 0.1)
        await asyncio.sleep(0)   # very important for pygbag, keep it 0


asyncio.run(main())
