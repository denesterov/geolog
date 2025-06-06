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


short_idling = Case(
    track = [
        [
            test_utils.make_point(45.23797, 19.84223, "2025-05-11 20:10:00"), # 0.0 m
            test_utils.make_point(45.23864, 19.84186, "2025-05-11 20:10:30"), # 79.7 m
            test_utils.make_point(45.23930, 19.84120, "2025-05-11 20:11:00"), # 89.3 m
            test_utils.make_point(45.23935, 19.84125, "2025-05-11 20:11:30"), # idle
            test_utils.make_point(45.23937, 19.84127, "2025-05-11 20:12:00"), # idle
            test_utils.make_point(45.23996, 19.84185, "2025-05-11 20:12:30"), # 82.7 m
            test_utils.make_point(45.24060, 19.84200, "2025-05-11 20:13:00"), # 71.2 m
        ],
    ],
    expect_gpx_points = 5,
    expect_length = 79.7 + 89.3 + 82.7 + 71.2,
    expect_duration = 180.0,
    skip_points={(0, 3), (0, 4)},
)


async def help_test_gpx_data(context, c: Case):
    await test_utils.help_test_gpx_data(context, c.track, c.expect_gpx_points,
            c.expect_length, c.expect_duration, c.skip_segments, c.skip_points)
