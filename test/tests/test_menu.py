import pytest
import geobot
import test_utils
import const


@pytest.mark.asyncio
async def test_cmd_start_deeplink(mock_update_factory, mock_context):
    track = [
        [
            test_utils.make_point(45.23996, 19.84185, "2025-05-11 21:44:20"),
            test_utils.make_point(45.24060, 19.84200, "2025-05-11 21:44:50"),
        ],
    ]

    expected_gpx, start_upd, session_id = await test_utils.help_test_gpx_data(mock_context, track, 2, 71.2, 30.0)
    assert mock_context.bot.send_message.call_count == 2

    deep_link = geobot.form_deep_link(session_id)
    assert deep_link.startswith(f'https://t.me/{const.GEOLOG_BOT_NAME}?start=')
    payload = deep_link.split('start=')[1]
    mock_context.args = [payload]

    start_update = mock_update_factory()
    start_update.message.from_user.id = start_upd.effective_user.id
    await geobot.cmd_start(start_update, mock_context)

    assert mock_context.bot.send_message.call_count == 3
    assert mock_context.bot.deleteMessage.call_count == 1
    assert mock_context.bot.send_document.call_count == 1

    gpx_from_deeplink = mock_context.bot.send_document.call_args[0][1].input_file_content.decode('utf-8')
    assert gpx_from_deeplink == expected_gpx

    track_info = mock_context.bot.send_message.call_args[1]['text']
    assert 'Here is the track' in track_info
    assert 'Length' in track_info
    assert 'duration' in track_info
    assert deep_link in track_info
