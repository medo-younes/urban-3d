import pdal
import json
import os
import geopandas as gpd
from shapely import wkt

from config import *
# COORDINATE REFERENCE SYSTEM
crs_h = "EPSG:26917"
crs_v = "6647"
crs = f'{crs_h}+{crs_v}'

# INPUT FILE PATHS
folder = os.path.join( RAW, "GTA_2023/20250705_150719/LAZ" )
las_name = "ON_TRCA2023_20230511_NAD83CSRS_UTMZ17_1km_E6300_N48340_CLASS.copc.laz"
filename = os.path.join(folder, las_name)

# OUTPUT FILEPATHS
resampled_fp = "../data/processed/resampled.copc.laz"


pp = {
        "pipeline" :
            [   

                {
                    "type" : "readers.las",
                    "filename": filename
                },
                # REPROJECT TO INCLUDE VERTICAL DATUM
                {
                    "type":"filters.reprojection",
                    "in_srs":"EPSG:26917",
                    "out_srs":"EPSG:26917+6647"
                },
                # REMOVED POINTS CLASSIFIIED AS NOISE
                {
                    "type" :"filters.expression",
                    "expression" : "Classification != 7 && Classification != 18"
                },
                # RESAMPLE TO 0.3 m 
                {
                    "type" : "filters.sample",
                    "cell" : 0.3
                },
                # REMOVE STATISTICAL OUTLIERS
                {
                    "type":"filters.outlier",
                    "method":"statistical",
                    "mean_k":12,
                    "multiplier":2.2
                },
                #  COMPUTE SURFACE NORMALS USING K = 16
                {
                    "type":"filters.normal",
                    "knn": 16
                },
                # Write LAS
                {
                    "type" : "writers.las",
                    "filename": resampled_fp,
                    "extra_dims": "all",
                },
        ]
}

# Initialize Pipelines
pp = pdal.Pipeline(json.dumps(pp))

# Run Pipelines
pp.execute()

# ==========================================================================================================================

# tree_labels_fp = '../data/labelled/tree_labels.las'
# cropped_fp = os.path.join(LABELLED, "cropped.copc.las")
# merged_fp = os.path.join(LABELLED, "merged.copc.las") 
# train_bbox_fp  ="../data/labelled/training_bbox/training_bbox.shp"

# crop = {

#     "pipeline" : [
        
#         filename,
      
#         {
#             "type" :"filters.expression",
#             "expression" : "Classification != 7 && Classification != 18"
#         },
#         {
#             "type" : "filters.sample",
#             "cell" : 0.3
#         },
#         {
#             "type":"filters.outlier",
#             "method":"statistical",
#             "mean_k":12,
#             "multiplier":2.2
#         },
#         # {   
#         #     "type" : "filters.overlay",
#         #     "dimension" : "Classification",
#         #     "datasource" : train_bbox_fp,
#         #     "column" : "CLS"
#         # },
#         # {
#         #     "type" : "filters.expression",
#         #     "expression": "Classification != 99"
#         # },
#         # {
#         #     "type" : "filters.assign",
#         #     "value" : "Classification = 1"
#         # },
#         cropped_fp
#     ]
# }




# hexbins= {
    
#     "pipeline" :[
#             {
#                 "type": "readers.las",
#                 "filename": clean_fp
#             },
#             {
#                 "type": "filters.range",
#                 "limits": "Classification[5:5]"
#             },
#             {
#                 "type": "filters.hexbin",
#                 "edge_length": 2,
#             }
#             ]
# }

# merge = {

#     "pipeline" : [
        
#         cropped_fp,
#         clean_fp,
#         {   
#             "type" : "filters.merge"
#         },
#         {
#             "type" : "filters.sample",
#             "radius" : 2
#         },
#         {
#             "type":"filters.normal",
#             "knn": 16
#         },
#         {
#             "type": "writers.las",
#             "filename": merged_fp,
#             "extra_dims": "all",
            
#         }
#     ]
# }


# bbox_pp.execute()

# # Export HexBin as Shapefile
# wkt_str = bbox_pp.metadata['metadata']['filters.hexbin']['boundary']

# wkt_geom = wkt.loads(wkt_str)
# gdf = gpd.GeoDataFrame(geometry=[wkt_geom], crs = crs)
# gdf['CLS'] = 99
# gdf.to_file(train_bbox_fp)

# # Rin Crop and Merge
# crop_pp = pdal.Pipeline(json.dumps(crop))
# merge_pp = pdal.Pipeline(json.dumps(merge))
# crop_pp.execute()
# merge_pp.execute()





# with open("metadata.json", "w") as out:
#     json.dump(metadata, out)