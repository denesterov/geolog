from collections import namedtuple

Point = namedtuple('Point', ['lat', 'long', 'ts'])

TrackInfo = namedtuple('TrackInfo', ['length', 'duration', 'timestamp', 'points_total'])
