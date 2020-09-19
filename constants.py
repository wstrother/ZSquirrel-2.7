# app defaults

# controller defaults
CONTROLLER_FRAME_DEPTH = 120
INIT_DELAY = 15
HELD_DELAY = 5
STICK_DEAD_ZONE = .05
AXIS_MIN = .9

# mappings
K_ = "K_"
ID_NUM = "id_num"
MAP_TYPE = "map_type"
MAPPING = "mapping"
JOY_DEVICE = "joy_device"
SIGN = "sign"
DIAGONAL = "diagonal"
BUTTON_MAP_KEY = "button_map_key"
BUTTON_MAP_BUTTON = "button_map_button"
BUTTON_MAP_AXIS = "button_map_axis"
BUTTON_MAP_HAT = "button_map_hat"
AXIS_MAP = "axis_map"

# devices
BUTTON = "button"
AXIS = "axis"
X_AXIS = "x_axis"
Y_AXIS = "y_axis"
AXES = X_AXIS, Y_AXIS
DEVICE_TRIGGER = "trigger"
DPAD = "dpad"
THUMB_STICK = "thumb_stick"
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
UDLR = UP, DOWN, LEFT, RIGHT

# command inputs
COMMANDS = "command_inputs"
STEPS = "command_steps"
CONDITIONS = "command_conditions"

# objects
CONTEXT = "context"
GAME = "game"
ENVIRONMENT = "environment"

# context.populate API
SET_ = "set_"
CLASS = "class"
GROUP = "group"
GROUPS = "groups"
SPRITES = "sprites"
LAYERS = "layers"

INIT_ORDER = "init_order"
INIT_DATA = "init_data"
INTERFACE_DATA = "interface_data"

# general variable keys
DT = "dt"
NAME = "name"
PARENT_LAYER = "parent_layer"
SUB_LAYERS = "sub_layers"
POSITION = "position"
SIZE = "size"
CONTROLLERS = "controllers"

# Pygame.draw methods API
PYGAME_RECT = "rect"
PYGAME_LINE = "line"
PYGAME_CIRCLE = "circle"

# Resource directories
RESOURCES = "resources"
JSON = "json"
IMAGES = "images"
SOUNDS = "sounds"

# File extensions
IMAGE_EXT = "gif", "jpg", "bmp", "png"
SOUND_EXT = "wav", "ogg", "mp3", "flac", "aac"

# Event keys
DURATION = "duration"
TIMER = "timer"
LERP = "lerp"
LINK = "link"

# Event listener keys
TARGET = "target"
RESPONSE = "response"
TEMP = "temp"
TRIGGER = "trigger"

# Event names
ON_ = "on_"
SPAWN = "spawn"
DEATH = "death"
DEAD = "dead"

# Geometry
RECT = "rect"
ORIGIN = "origin"
RADIUS = "radius"
LINE = "line"
VECTOR = "vector"
WALL = "wall"

# Style
CORNER_CHOICES = "abcd"
SIDE_CHOICES = "tlrb"
ALIGNS = "aligns"
ALPHA_COLOR = "alpha_color"
FONT_COLOR = "font_color"
FONT_SIZE = "font_size"
FONT_NAME = "font_name"
TEXT_CUTOFF = "text_cutoff"
TEXT_NEWLINE = "text_newline"
TEXT_BUFFER = "text_buffer"
BOLD = "bold"
ITALIC = "italic"
BG_IMAGE = "bg_image"
BG_COLOR = "bg_color"
BORDER = "border"
BORDER_CORNERS = "border_corners"
BORDER_IMAGES = "border_images"
BORDER_SIZE = "border_size"
BORDER_SIDES = "border_sides"
BUFFERS = "buffers"
SELECTED = "selected_color"
NORMAL = "normal_color"

# default style
DEFAULT_BORDER_SIZE = [5, 5]
DEFAULT_ALIGNS = ["c", "c"]
DEFAULT_SELECT_COLOR = [0, 255, 0]
DEFAULT_BG_COLOR = [0, 55, 55]
DEFAULT_ALPHA_COLOR = [255, 0, 0]
DEFAULT_FONT_COLOR = [255, 255, 255]
DEFAULT_FONT_SIZE = 16
DEFAULT_FONT_NAME = "courier-new"
DEFAULT_TEXT_CUTOFF = 100
