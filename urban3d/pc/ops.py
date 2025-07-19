
'''
POINT CLOUD OPERATIONS

'''
import sys
sys.path.append("../../urban-3d")
import pdal 
import json
import os
import geopandas as gpd
from shapely import wkt
import shapely
import laspy

def run_pdal_pipeline(pipeline_dict):
    
    pipeline_json = json.dumps(pipeline_dict)
    pdal_pipeline = pdal.Pipeline(pipeline_json)
    pdal_pipeline.execute()


def pdal_merge(in_las, out_merged):
        
        pipeline_list = in_las.copy()
        pipeline_list.extend([{"type": "filters.merge"}, {"type" : "writers.las", "filename" : out_merged}])
        pipeline_dict = dict(pipeline = pipeline_list)
        
        run_pdal_pipeline(pipeline_dict=pipeline_dict)



def clip_laz_files(laz_dir, bbox_gdf, merge = False, merged_fp=None):

    laz_fps = [f'{laz_dir}/{laz_fp}' for laz_fp in os.listdir(laz_dir) if '.laz' in laz_fp]
    las_crs = [laspy.read(laz_fp).header.parse_crs() for laz_fp in laz_fps]
    bbox_wkts = [shapely.force_2d(bbox_gdf.to_crs(crs).geometry.iloc[0]).wkt for crs in las_crs]
    pipeline = list()
    
    if merge:
        for laz_fp, wkt in zip(laz_fps, bbox_wkts):
            pipeline.extend([{"type" : "readers.las", "filename" : laz_fp}, 
                            {"type" : "filters.crop", "polygon" : wkt}])
            
        pipeline.extend([{"type" :"filters.merge",}, {"type" :"writers.las", "filename": merged_fp}])
    else:
        for laz_fp in laz_fps:
            pipeline.extend([{"type" : "readers.las", "filename" : laz_fp}, 
                            {"type" : "filters.crop", "polygon" : wkt},
                            {"type" :"writers.las", "filename": laz_fp}])
            
    pipeline_dict = dict(pipeline = pipeline)
    run_pdal_pipeline(pipeline_dict=pipeline_dict)



def pdal_hexbin_gdf(p):
    metadata = p.metadata['metadata']
    wkt_str = metadata['filters.hexbin']['boundary']
    crs = metadata['filters.info']['srs']['wkt']
    wkt_geom = wkt.loads(wkt_str)
    return gpd.GeoDataFrame(geometry=[wkt_geom], crs= crs)


def pdal_get_crs(p):
    return p.metadata['metadata']['filters.info']['srs']['compoundwkt']

