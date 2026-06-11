SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60

GROUND_Y = SCREEN_HEIGHT - 20          # floor top-edge y

# physics
GRAVITY          = 0.9
PLAYER_JUMP_VEL  = -18                  # upward velocity on first jump
DOUBLE_JUMP_VEL  = -15                  # weaker second jump

# animation
ANIM_INTERVAL = 4                       # update run frame every N ticks  (~15 fps)

# obstacles
OBSTACLE_BASE_SPEED    = 5
OBSTACLE_BASE_INTERVAL = 90             # frames between spawns at game start

# difficulty progression (applied per SPEED_LEVEL_INTERVAL frames outside boss fights)
SPEED_LEVEL_INTERVAL  = 300
SPEED_INCREMENT       = 0.4             # added to obstacle speed each level
INTERVAL_DECREMENT    = 4               # fewer frames between spawns each level
MIN_SPAWN_INTERVAL    = 40
MAX_OBSTACLE_SPEED    = 15.0

# hitbox inset (pixels shaved off each side for collision — more forgiving feel)
HITBOX_INSET_X = 8
HITBOX_INSET_Y = 5

# boss
BOSS_INITIAL_HP       = 300
SKILL_DAMAGE          = 30
SKILL_POINT_THRESHOLD = 5
