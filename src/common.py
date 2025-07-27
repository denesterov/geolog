from collections import namedtuple

Point = namedtuple('Point', ['latitude', 'longitude', 'ts'])

TrackInfo = namedtuple('TrackInfo', ['length', 'duration', 'timestamp', 'points_total'])
