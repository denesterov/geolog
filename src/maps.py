import os
import logging
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import const
import db


logger = logging.getLogger('geobot-maps')

def get_filename(sess_id: str):
    base = os.environ.get('MAP_IMAGES_DIR', const.DEFAULT_BASE_DIR)

    sess_id_split = sess_id.split(':')
    assert len(sess_id_split) == 2
    assert sess_id_split[0] == 'session'
    fname = f'map-{sess_id_split[1]}.jpg'

    return os.path.join(base, fname)


async def try_create_map():
    logger.info(f'try_create_map.')
    sess_id = db.acquire_map_job()
    if sess_id is None:
        return
    
    logger.info(f'try_create_map. Creating map for track. sess_id={sess_id}')
    track_info, segments = db.get_track(sess_id)
    # if track_info.points_total < const.MIN_POINTS_FOR_MAP:
    #     db.finish_map_job(sess_id)
    #     return

    base_path = os.environ.get('MAP_IMAGES_DIR', const.DEFAULT_BASE_DIR)
    os.makedirs(base_path, exist_ok=True)

    tiler = cimgt.OSM()
    mercator = tiler.crs

    lon_min = None
    lon_max = None
    lat_min = None
    lat_max = None
    for points in segments:
        for pnt in points:
            lat = float(pnt.lat)
            lon = float(pnt.lon)
            lon_min = lon if lon_min is None else min(lon_min, lon)
            lon_max = lon if lon_max is None else max(lon_max, lon)
            lat_min = lat if lat_min is None else min(lat_min, lat)
            lat_max = lat if lat_max is None else max(lat_max, lat)

    lat_delta = lat_max - lat_min
    lon_delta = lon_max - lon_min
    if lat_delta < const.MIN_ANGULAR_SIZE_FOR_MAP:
        mid = 0.5 * (lat_max + lat_min)
        lat_min = mid - 0.5 * const.MIN_ANGULAR_SIZE_FOR_MAP
        lat_max = mid + 0.5 * const.MIN_ANGULAR_SIZE_FOR_MAP
    if lon_delta < const.MIN_ANGULAR_SIZE_FOR_MAP:
        mid = 0.5 * (lon_max + lon_min)
        lon_min = mid - 0.5 * const.MIN_ANGULAR_SIZE_FOR_MAP
        lon_max = mid + 0.5 * const.MIN_ANGULAR_SIZE_FOR_MAP

    aspect = 1.0
    aspect = lon_delta / lat_delta
    aspect = max(aspect, 0.33)
    aspect = min(aspect, 3.0)

    BASE_FIG_SIZE = 10.0
    fig_size = None
    if aspect > 1.0:
        fig_size = (BASE_FIG_SIZE, BASE_FIG_SIZE / aspect)
    else:
        fig_size = (BASE_FIG_SIZE * aspect, BASE_FIG_SIZE)
    fig = plt.figure(figsize=fig_size, frameon=False)
    ax = plt.axes(projection=mercator)

    MARGIN = 0.04
    lon_sz = lon_max - lon_min
    lat_sz = lat_max - lat_min
    lon_min -= lon_sz * MARGIN
    lon_max += lon_sz * MARGIN
    lat_min -= lat_sz * MARGIN
    lat_max += lat_sz * MARGIN

    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

    detail_lvl = const.MAP_HI_DETAIL_LVL if max(lat_delta, lon_delta) < const.MAP_ANGULAR_SIZE_THRESHOLD else const.MAP_LO_DETAIL_LVL
    ax.add_image(tiler, detail_lvl)

    for points in segments:
        lons = []
        lats = []
        for pnt in points:
            lons.append(float(pnt.lon))
            lats.append(float(pnt.lat))
        ax.plot(lons, lats, color='blue', linewidth=2, transform=ccrs.Geodetic())

    logger.debug(f'try_create_map. saving image. sess_id={sess_id}')
    fname = get_filename(sess_id) 
    plt.savefig(fname, dpi=300, format='jpg', bbox_inches='tight', pad_inches=0)
    logger.info(f'try_create_map. saved. sess_id={sess_id}, filename={fname}')

    db.finish_map_job(sess_id)


def get_map(sess_id: str):
    if not db.is_map_available(sess_id):
        logger.info(f'get_map. not available. sess_id={sess_id}')
        return None
    logger.info(f'get_map. loading file. sess_id={sess_id}')
    fname = get_filename(sess_id)
    if os.path.exists(fname):
        with open(fname, 'rb') as f:
            return f.read(), fname
    logger.info(f'get_map. map file does not exist. sess_id={sess_id}, filename={fname}')
    return None
