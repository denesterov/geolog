import pytest
from unittest.mock import patch
import geobot
import db
import conftest
import test_utils


@pytest.mark.asyncio
async def test_speeding_then_idling(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            test_utils.make_track_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_track_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_track_point(45.24122, 19.84237, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [
            # Speeding points
            test_utils.make_track_point(45.23612, 19.84651, "2025-05-11 21:45:50"), # 652.8 m (78.3 km/h)
            test_utils.make_track_point(45.23110, 19.85335, "2025-05-11 21:46:20"), # 774.0 m (92.9 km/h)
        ],
        [
            # First point after speeding, but it is very close to where speeding ended
            test_utils.make_track_point(45.23111, 19.85326, "2025-05-11 21:46:50"),
            test_utils.make_track_point(45.23104, 19.85330, "2025-05-11 21:47:20"),
        ],
        [
            test_utils.make_track_point(45.23076, 19.85294, "2025-05-11 21:47:50"), # 0 m (from idling end)
            test_utils.make_track_point(45.23037, 19.85230, "2025-05-11 21:48:20"), # 66.2 m
        ],
    ]

    await test_utils.help_test_gpx_data(mock_context, track, 5, 71.2 + 74.7 + 66.2, 60.0 + 30.0, skip_segments={1, 2})
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
@pytest.mark.skip(reason="https://github.com/denesterov/geolog/issues/20")
async def test_idling_then_speeding(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            test_utils.make_track_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_track_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_track_point(45.24122, 19.84237, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [
            # Idling points
            test_utils.make_track_point(45.24124, 19.84244, "2025-05-11 21:45:50"),
            test_utils.make_track_point(45.24126, 19.84257, "2025-05-11 21:46:20"),
            test_utils.make_track_point(45.24130, 19.84273, "2025-05-11 21:46:50"),
        ],
        [
            # Speeding points
            test_utils.make_track_point(45.23612, 19.84651, "2025-05-11 21:47:20"), # 652.8 m (78.3 km/h)
            test_utils.make_track_point(45.23110, 19.85335, "2025-05-11 21:47:50"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_track_point(45.23076, 19.85294, "2025-05-11 21:48:20"), # 0 m (from idling end)
            test_utils.make_track_point(45.23037, 19.85230, "2025-05-11 21:48:50"), # 66.2 m
        ],
    ]

    await test_utils.help_test_gpx_data(mock_context, track, 5, 71.2 + 74.7 + 66.2, 60.0 + 30.0, skip_segments={1, 2})
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_long_idling_then_speeding(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            test_utils.make_track_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_track_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_track_point(45.24122, 19.84237, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [
            # Idling points
            test_utils.make_track_point(45.24124, 19.84244, "2025-05-11 21:45:50"),
            test_utils.make_track_point(45.24126, 19.84257, "2025-05-11 21:46:20"),
            test_utils.make_track_point(45.24130, 19.84273, "2025-05-11 21:47:20"),
            test_utils.make_track_point(45.24131, 19.84273, "2025-05-11 21:48:20"),
            test_utils.make_track_point(45.24130, 19.84274, "2025-05-11 21:48:50"),
            test_utils.make_track_point(45.24131, 19.84272, "2025-05-11 21:49:20"),
        ],
        [
            # Speeding points
            test_utils.make_track_point(45.23612, 19.84651, "2025-05-11 21:49:50"), # 652.8 m (78.3 km/h)
            test_utils.make_track_point(45.23110, 19.85335, "2025-05-11 21:50:20"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_track_point(45.23076, 19.85294, "2025-05-11 21:50:50"), # 0 m (from idling end)
            test_utils.make_track_point(45.23037, 19.85230, "2025-05-11 21:51:20"), # 66.2 m
        ],
    ]

    await test_utils.help_test_gpx_data(mock_context, track, 5, 71.2 + 74.7 + 66.2, 60.0 + 30.0, skip_segments={1, 2})
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_right_away_speeding(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            # Speeding points
            test_utils.make_track_point(45.23612, 19.84651, "2025-05-11 21:49:50"), # 652.8 m (78.3 km/h)
            test_utils.make_track_point(45.23110, 19.85335, "2025-05-11 21:50:20"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_track_point(45.23076, 19.85294, "2025-05-11 21:50:50"), # 0 m (from idling end)
            test_utils.make_track_point(45.23037, 19.85230, "2025-05-11 21:51:20"), # 66.2 m
        ],
    ]

    await test_utils.help_test_gpx_data(mock_context, track, 5, 66.2, 30.0, skip_segments={0, 1})
    assert mock_context.bot.send_message.call_count == 2
