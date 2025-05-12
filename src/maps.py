import logging
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import db


logger = logging.getLogger('geobot-maps')

async def convert_map():
    logger.info(f'convert_map.')
    sess_id = db.acquire_maps_job()
    if sess_id is None:
        return
    
    _, segments = db.get_track(sess_id)

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

    fig = plt.figure(figsize=(10, 10))
    ax = plt.axes(projection=mercator)

    MARGIN = 0.02
    lon_sz = lon_max - lon_min
    lat_sz = lat_max - lat_min
    lon_min -= lon_sz * MARGIN
    lon_max += lon_sz * MARGIN
    lat_min -= lat_sz * MARGIN
    lat_max += lat_sz * MARGIN

    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

    ax.add_image(tiler, 14)  # число 14 — уровень масштабирования (чем больше, тем детальнее)

    for points in segments:
        lons = []
        lats = []
        for pnt in points:
            lons.append(float(pnt.lon))
            lats.append(float(pnt.lat))
        ax.plot(lons, lats, color='blue', linewidth=2, transform=ccrs.Geodetic())

    logger.info(f'convert_map. saving image. sess_id={sess_id}')
    sess_id_split = sess_id.split(':')
    assert len(sess_id_split) == 2
    assert sess_id_split[0] == 'session'
    fname = f'map_{sess_id_split[1]}.jpg' 
    plt.savefig(fname, dpi=300, format='jpg')
    logger.info(f'convert_map. saved. sess_id={sess_id}, filename={fname}')
    db.finish_maps_job(sess_id)
