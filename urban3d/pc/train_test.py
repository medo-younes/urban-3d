import pdal
import json
import geopandas as gpd
from sklearn.model_selection import train_test_split
from shapely import wkt
from config import *
from shapely.geometry import box
from geo import tiles_from_bbox,pdal_hexbin_gdf, pdal_get_crs
import numpy as np




training_pc = os.path.join(LABELLED, "merged.copc.las")
target_pc =  os.path.join(LABELLED, "tree_labels_cleaned.copc.las")
out_dir = os.path.join(LABELLED, "hexbins")

hexbin1_fp = os.path.join(out_dir, "hexbin1.geojson")
hexbin2_fp = os.path.join(out_dir, "hexbin2.geojson")

# cmd1 = f"pdal density {training_pc} -o {hexbin1_fp}" 

reader = {
            "type" : "readers.las",
            "filename" : training_pc,
        }
EDGE_LENGTH = 5

info  = {

    "pipeline":[
        
            {
                "type" : "readers.las",
                "filename" : training_pc,
            }, 
            {
                "type" : "filters.info"
            }
        
    ]
}
p1 = {

    "pipeline" : [

        {
            "type" : "readers.las",
            "filename" : training_pc,
        },     
        # {
        #     "type" : "filters.hexbin",
        #     "edge_length" : EDGE_LENGTH,
        #     "density" : hexbin1_fp,
        # },
        # {
        #     "type": "filters.splitter",
        #     "length": "100"
        # },
         
        {
            "type":"filters.chipper",
            "capacity":"400",
        },
        # {
        #     "type": "filters.hexbin",
        #     "edge_length": EDGE_LENGTH, # in meters (adjust as needed)
        #     "density" : hexbin2_fp
        # },
        # {
        #     "type" : "filters.info"
        # },
        {
            "type" : "writers.las",
            "filename" : os.path.join(DATA, 'train', 'train_#.laz' ),
            "extra_dims" : "all"
        }
        
        ]
}

# Get Hexbin of Entire Area
# Define Pipeline 

p  = pdal.Pipeline(json.dumps(p1))
p.execute()


# crs= p.metadata['metadata']['filters.info']['srs']['horizontal']
# boundary = p.metadata['metadata']['filters.hexbin']['boundary']

# gdf = gpd.GeoDataFrame(geometry=[wkt.loads(boundary)], crs = crs)
# gdf = gdf.explode().reset_index(drop=True)
# Get GeoDataFrame of pipeline hexbins
# hxb_gdf = gpd.read_file(hexbin2_fp).set_crs(crs, allow_override=True)

# # Classify Target Point Count based on 50% Quartile
# q50 = np.percentile(hxb_gdf.COUNT, q = 50)
# hxb_gdf['majority'] = ["yes" if above else "no" for above in hxb_gdf.COUNT > q50]

# # 70/30 split for training and validation
# train, val = train_test_split(gdf, train_size=0.7)

# train.to_file(os.path.join(out_dir, "train.shp"))
# val.to_file(os.path.join(out_dir, "val.shp"))

# # Clip Point Cloud into Batches from Traing and Test Hexbins

# train_dr = os.path.join('../practice/train', 'raw')
# test_dr = os.path.join('../practice/test', 'raw')

# clip_pipeline = dict(

#     pipeline = list()
# )

# for idx,row in train.iterrows():
#     clip_pipeline['pipeline'].append(reader)

#     clip_pipeline['pipeline'].append(dict(
#         type = "filters.crop",
#         polygon = row.geometry.wkt,
#     ))
#     clip_pipeline['pipeline'].append(dict(
#         type="writers.las",
#         filename = os.path.join(train_dr, f'{str(idx).zfill(4)}.laz'),
#         extra_dims = "all"
#     ))

# for idx,row in val.iterrows():
#     clip_pipeline['pipeline'].append(reader)

#     clip_pipeline['pipeline'].append(dict(
#         type = "filters.crop",
#         polygon = row.geometry.wkt,
#     ))

#     clip_pipeline['pipeline'].append(dict(
#         type="writers.las",
#         filename = os.path.join(test_dr, f'{str(idx).zfill(4)}.laz'),
#         extra_dims = "all"
#     ))


# clip_pipeline = pdal.Pipeline(json.dumps(clip_pipeline))
# clip_pipeline.execute()
    

