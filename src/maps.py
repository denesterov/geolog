import logging
import db

logger = logging.getLogger('geobot-maps')

async def convert_map():
    logger.info(f'convert_map.')
    sess_id = db.acquire_maps_job()
    if sess_id is None:
        return
