import common
import test_utils


class Case:
    def __init__(self,
                 track: list[list[common.Point]],
                 expect_gpx_points:int, expect_length:float, expect_duration:float,
                 skip_segments: set[int] = set(), skip_points: set[tuple[int, int]] = set()):
        self.track = track
        self.expect_gpx_points = expect_gpx_points
        self.expect_length = expect_length
        self.expect_duration = expect_duration
        self.skip_segments = skip_segments
        self.skip_points = skip_points


smoke = Case(
    track = [
        [
            test_utils.make_point(45.23930, 19.84120, "2025-05-17 16:20:00"), # 0.0 m
            test_utils.make_point(45.24060, 19.84200, "2025-05-17 16:20:30"), # 156.0 m
            test_utils.make_point(45.24122, 19.84237, "2025-05-17 16:21:10"), # 74.7 m
        ],
    ],
    expect_gpx_points = 3,
    expect_length = 156.0 + 74.7,
    expect_duration = 70.0,
)
