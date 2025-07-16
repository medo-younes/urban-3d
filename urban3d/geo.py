import geopandas as gpd
import numpy as np
import string
from shapely.geometry import box
from shapely import wkt 

def tiles_from_bbox(bbox, crs=4236, tile_dims=(4,4)):
    """Generates polygon tiles subdividing a given bounding box based on the given dimensions
    
    Args:
        bbox (list): Bounding box coordinates in format [x1,y1,x2,y2]
        tile_dims (tuple): How many tiles to sub-section the bounding box with the dimensions (width, length). With tile_dims == (4,4) the function will return 16 (4 x 4) tile polygons

    Returns:
        GeoDataFrame: GeoPandas GeoDataFrame of generated tiles as Shapely Polygons
    """

    x1,y1,x2,y2=bbox # Get left, top, right, bottom from bounding box

    x_rg = x2 - x1
    y_rg = y2 - y1

    x_inc=x_rg / (tile_dims[0])
    y_inc=y_rg / (tile_dims[1])


    xx=np.arange(x1, x2, x_inc)
    xx=np.append(xx,x2)
    yy=np.arange(y1, y2, y_inc)
    yy=np.append(yy,y2)

    xx,yy=np.meshgrid(xx, yy, indexing='ij')
    yy=yy.transpose()
 
    xx1=xx[:-1]
    xx2=xx[1:]
    yy1=yy[:-1]
    yy2=yy[1:]

    bounds=list()
    

    for lon1, lon2 in zip(xx1, xx2):    
        for lat1,lat2 in zip(yy1,yy2):
            bounds.extend([box(*(x1,y1,x2,y2)) for x1,y1,x2,y2 in zip(lon1,lat1,lon2,lat2)])
       

    tiles=gpd.GeoDataFrame( geometry=bounds, crs=crs).drop_duplicates("geometry").reset_index(drop=True)

    letters = list(string.ascii_uppercase)[0:tile_dims[0]]
    numbers = list(range(1, tile_dims[1] + 1))
    numbers.reverse()

    return tiles



def pdal_hexbin_gdf(p):
    metadata = p.metadata['metadata']
    wkt_str = metadata['filters.hexbin']['boundary']
    crs = metadata['filters.info']['srs']['wkt']
    wkt_geom = wkt.loads(wkt_str)
    return gpd.GeoDataFrame(geometry=[wkt_geom], crs= crs)


def pdal_get_crs(p):
    return p.metadata['metadata']['filters.info']['srs']['compoundwkt']
