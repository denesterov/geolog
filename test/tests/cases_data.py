import common
import test_utils


class Case:
    def __init__(self,
                 track: list[list[common.Point]],
                 expect_gpx_points:int, expect_length:float, expect_duration:float,
                 skip_segments: set[int] = set(), skip_points: set[tuple[int, int]] = set(),
                 additional_dirty_fields = set()):
        self.track = track
        self.expect_gpx_points = expect_gpx_points
        self.expect_length = expect_length
        self.expect_duration = expect_duration
        self.skip_segments = skip_segments
        self.skip_points = skip_points
        self.expected_dirty_fields = {'track_segm_len', 'last_lat', 'last_long', 'last_update', 'length', 'duration'} | additional_dirty_fields


# fixme: it is a wrong place for this function; It is leaking dependency
# Unit tests should not know about general tests; But we can not move it to test_utils - this module itself depends on test_utils
async def help_test_gpx_data(context, c: Case):
    await test_utils.help_test_gpx_data(context, c.track, c.expect_gpx_points,
            c.expect_length, c.expect_duration, c.skip_segments, c.skip_points)


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


general_idling = Case(
    track = [
        [
            test_utils.make_point(45.23797, 19.84223, "2025-05-11 20:10:00"), # 0.0 m
            test_utils.make_point(45.23864, 19.84186, "2025-05-11 20:10:30"), # 79.7 m
            test_utils.make_point(45.23930, 19.84120, "2025-05-11 20:11:00"), # 89.3 m
        ],
        [ # Idling points
            test_utils.make_point(45.23935, 19.84125, "2025-05-11 20:11:30"),
            test_utils.make_point(45.23937, 19.84127, "2025-05-11 20:12:00"),
            test_utils.make_point(45.23939, 19.84129, "2025-05-11 20:13:00"),
            test_utils.make_point(45.23937, 19.84125, "2025-05-11 20:14:00"),
            test_utils.make_point(45.23935, 19.84127, "2025-05-11 20:14:45"),
        ],
        [
            test_utils.make_point(45.23996, 19.84185, "2025-05-11 20:15:00"), # 0.0 m
            test_utils.make_point(45.24060, 19.84200, "2025-05-11 20:15:30"), # 71.2 m
            test_utils.make_point(45.24122, 19.84237, "2025-05-11 20:16:00"), # 74.7 m
        ],
    ],
    expect_gpx_points = 6,
    expect_length = 79.7 + 89.0 + 71.2 + 74.7,
    expect_duration = 60.0 + 60.0,
    skip_segments={1},
    additional_dirty_fields = {'track_segm_idx'}
)


speeding = Case(
    track = [
        [
            test_utils.make_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_point(45.24128, 19.84262, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [ # Speeding points
            test_utils.make_point(45.23612, 19.84651, "2025-05-11 21:45:50"), # 652.8 m (78.3 km/h)
            test_utils.make_point(45.23110, 19.85335, "2025-05-11 21:46:20"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_point(45.23076, 19.85294, "2025-05-11 21:46:50"), # 0.0 m (from speeding end)
            test_utils.make_point(45.23037, 19.85230, "2025-05-11 21:47:20"), # 66.2 m
        ],
    ],
    expect_gpx_points = 5,
    expect_length = 71.2 + 74.7 + 66.2,
    expect_duration = 60.0 + 30.0,
    skip_segments={1},
    additional_dirty_fields = {'track_segm_idx'}
)


speeding_then_idling = Case(
    track = [
        [
            test_utils.make_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_point(45.24122, 19.84237, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [
            # Speeding points
            test_utils.make_point(45.23612, 19.84651, "2025-05-11 21:45:50"), # 652.8 m (78.3 km/h)
            test_utils.make_point(45.23110, 19.85335, "2025-05-11 21:46:20"), # 774.0 m (92.9 km/h)
        ],
        [
            # First point after speeding, but it is very close to where speeding ended
            test_utils.make_point(45.23111, 19.85326, "2025-05-11 21:46:50"),
            test_utils.make_point(45.23104, 19.85330, "2025-05-11 21:47:20"),
        ],
        [
            test_utils.make_point(45.23076, 19.85294, "2025-05-11 21:47:50"), # 0 m (from idling end)
            test_utils.make_point(45.23037, 19.85230, "2025-05-11 21:48:20"), # 66.2 m
        ],
    ],
    expect_gpx_points = 5,
    expect_length = 71.2 + 74.7 + 66.2,
    expect_duration = 60.0 + 30.0,
    skip_segments={1, 2},
    additional_dirty_fields = {'track_segm_idx'}
)


# edge case https://github.com/denesterov/geolog/issues/20
idling_then_speeding = Case(
    track = [
        [
            test_utils.make_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_point(45.24122, 19.84237, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [
            # Idling points
            test_utils.make_point(45.24124, 19.84244, "2025-05-11 21:45:50"),
            test_utils.make_point(45.24126, 19.84257, "2025-05-11 21:46:20"),
            test_utils.make_point(45.24130, 19.84273, "2025-05-11 21:46:50"),
        ],
        [
            # Speeding points
            test_utils.make_point(45.23612, 19.84651, "2025-05-11 21:47:20"), # 652.8 m (78.3 km/h)
            test_utils.make_point(45.23110, 19.85335, "2025-05-11 21:47:50"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_point(45.23076, 19.85294, "2025-05-11 21:48:20"), # 0 m (from idling end)
            test_utils.make_point(45.23037, 19.85230, "2025-05-11 21:48:50"), # 66.2 m
        ],
    ],
    expect_gpx_points = 5,
    expect_length = 71.2 + 74.7 + 66.2,
    expect_duration = 60.0 + 30.0,
    skip_segments={1, 2},
    additional_dirty_fields = {'track_segm_idx'}
)


# edge case https://github.com/denesterov/geolog/issues/22
right_away_speeding = Case(
    track = [
        [
            # Speeding points
            test_utils.make_point(45.23612, 19.84651, "2025-05-11 21:49:50"), # 652.8 m (78.3 km/h)
            test_utils.make_point(45.23110, 19.85335, "2025-05-11 21:50:20"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_point(45.23076, 19.85294, "2025-05-11 21:50:50"), # 0 m (from idling end)
            test_utils.make_point(45.23037, 19.85230, "2025-05-11 21:51:20"), # 66.2 m
        ],
    ],
    expect_gpx_points = 2,
    expect_length = 66.2,
    expect_duration = 30.0,
    skip_segments={0, 1},
    additional_dirty_fields = {'track_segm_idx'}
)


# edge case https://github.com/denesterov/geolog/issues/22
long_idling_then_speeding = Case(
    track = [
        [
            test_utils.make_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_point(45.24122, 19.84237, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [
            # Idling points
            test_utils.make_point(45.24124, 19.84244, "2025-05-11 21:45:50"),
            test_utils.make_point(45.24126, 19.84257, "2025-05-11 21:46:20"),
            test_utils.make_point(45.24130, 19.84273, "2025-05-11 21:47:20"),
            test_utils.make_point(45.24131, 19.84273, "2025-05-11 21:48:20"),
            test_utils.make_point(45.24130, 19.84274, "2025-05-11 21:48:50"),
            test_utils.make_point(45.24131, 19.84272, "2025-05-11 21:49:20"),
        ],
        [
            # Speeding points
            test_utils.make_point(45.23612, 19.84651, "2025-05-11 21:49:50"), # 652.8 m (78.3 km/h)
            test_utils.make_point(45.23110, 19.85335, "2025-05-11 21:50:20"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_point(45.23076, 19.85294, "2025-05-11 21:50:50"), # 0 m (from idling end)
            test_utils.make_point(45.23037, 19.85230, "2025-05-11 21:51:20"), # 66.2 m
        ],
    ],
    expect_gpx_points = 5,
    expect_length = 71.2 + 74.7 + 66.2,
    expect_duration = 60.0 + 30.0,
    skip_segments={1, 2},
    additional_dirty_fields = {'track_segm_idx'}
)

