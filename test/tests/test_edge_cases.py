import pytest
import cases_data


@pytest.mark.asyncio
async def test_speeding_then_idling(mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.speeding_then_idling)
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
@pytest.mark.skip(reason="https://github.com/denesterov/geolog/issues/20")
async def test_idling_then_speeding(mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.idling_then_speeding)
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.skip(reason="https://github.com/denesterov/geolog/issues/22")
@pytest.mark.asyncio
async def test_right_away_speeding(mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.right_away_speeding)
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.skip(reason="https://github.com/denesterov/geolog/issues/22")
@pytest.mark.asyncio
async def test_long_idling_then_speeding(mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.long_idling_then_speeding)
    assert mock_context.bot.send_message.call_count == 2
