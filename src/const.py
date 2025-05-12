
MIN_GEO_DELTA = 25.0 # Minimal delta in meters for next track point to be recorded
MAX_SPEED = 10.0 # Maximum speed, m/s
AFTER_PAUSE_TIME = 180.0 # Timeout after wich track is paused, if there is no movement 
DEFAULT_BASE_DIR = './geolog-bot-images' # Default map images path

MIN_POINTS_FOR_MAP = 5 # Minimal points num to generate a map
MIN_ANGULAR_SIZE_FOR_MAP = 0.003 # Minimal angular size of track to have a map

MAP_ANGULAR_SIZE_THRESHOLD1 = 0.006 # Threshold of hi/lo map detail
MAP_ANGULAR_SIZE_THRESHOLD2 = 0.012 # Threshold of hi/lo map detail
MAP_DETAIL_LVL1 = 18
MAP_DETAIL_LVL2 = 16
MAP_DETAIL_LVL3 = 15