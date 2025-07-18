
# Create an LAZ Dataset Pyramid from LiDAR Point Clouds - CanElevation Series


'''
Refer to the Government of Canada Website for more Information: https://open.canada.ca/data/en/dataset/7069387e-9986-4297-9f55-0288e9676947

The LiDAR Point Clouds is a product that is part of the CanElevation Series created to support the National Elevation Data Strategy implemented by NRCan.

This product contains point clouds from various airborne LiDAR acquisition projects conducted in Canada. These airborne LiDAR acquisition projects may have been conducted by NRCan or by various partners. The LiDAR point cloud data is licensed under an open government license and has been incorporated into the National Elevation Data Strategy.

Point cloud files are distributed by LiDAR acquisition project without integration between projects.

The point cloud files are distributed using the compressed .LAZ / Cloud Optimized Point Cloud (COPC) format. The COPC open format is an octree reorganization of the data inside a .LAZ 1.4 file. It allows efficient use and visualization rendering via HTTP calls (e.g. via the web), while offering the capabilities specific to the compressed .LAZ format which is already well established in the industry. Point cloud files are therefore both downloadable for local use and viewable via URL links from a cloud computing environment.

The reference system used for all point clouds in the product is NAD83(CSRS), epoch 2010. The projection used is the UTM projection with the corresponding zone. Elevations are orthometric and expressed in reference to the Canadian Geodetic Vertical Datum of 2013 (CGVD2013).

'''

## Import Libraries
import geopandas as gpd
import os
from pathlib import Path
import boto3
import re
from datetime import datetime
import pdal 
import json


# S3 Bucket Name
BUCKET_NAME = 'canelevation-lidar-point-clouds'
s3 = boto3.client('s3') # Define Boto3 client

## FUNCTIONS
def download_s3(bucket_name, url, out_dir):

    url_path = Path(url)
    object_name = '/'.join(url_path.parts[2:])
    file_name = url_path.name.replace('.copc', '')
    out_path = f'{out_dir}/{file_name}'

    if os.path.exists(out_path):
        print(f'-ALREADY EXISTS: {file_name}')
    else:
        s3.download_file(bucket_name, object_name, out_path)
        print(f'-DOWNLOADED: {file_name}')


def get_matching_urls(tile_index_fp, gdb, layer):    
    # Read Feature Class with GeoPandas
    bbox_gdf = gpd.read_file(gdb, layer = layer).dissolve()

    # Read Tiles ShapeFile as GeoDataFrame
    tile_index_gdf = gpd.read_file(tile_index_fp, bbox = bbox_gdf, engine ='fiona')
    print(str(len(tile_index_gdf)))
    tile_index_gdf['year'] = tile_index_gdf.Project.apply(lambda st: max(re.findall(r'\d+' ,st))).astype(int)
    latest_year = tile_index_gdf.year.astype(int).max()
    tiles_gdf_latest = tile_index_gdf[tile_index_gdf.year == latest_year]

    ## Get Name of Project
    project_name = tiles_gdf_latest.Project.value_counts().reset_index().iloc[0].Project
    project_id = f'{project_name}/{datetime.now().strftime("%Y%m%d_%H%M%S")}' # Configure unique project ID

    # Spatial join to find only matching tiles
    matching_urls = tiles_gdf_latest.URL.to_list()
    print(f'Found {len(matching_urls)} Matching LAZ Files within Bounds for {latest_year}')
    print(f'PROJECT ID: {project_id}')
    return matching_urls, project_id, latest_year


## Download LAZ Files 
def download_laz_files(matching_urls, laz_dir):
    ## Download Matching LAZ Files from NRCAN S3 Bucket
    for url in matching_urls:
        download_s3(
            bucket_name = BUCKET_NAME,
            url = url,
            out_dir = laz_dir
        )

        

## Download LAZ Files 
def pdal_download_s3(matching_urls, out_dir, wkt):
    ## Download Matching LAZ Files from NRCAN S3 Bucket
    pipeline_fp = os.path.join(out_dir ,'download.json')
    url1 = Path(matching_urls[0])
    print(f'DOWNLOADING FROM PATH: {url1.parent}')
    print('=============================================================')
    n = 1
    pipeline = list()
    for url in matching_urls:
        # print(url)
        url_path = Path(url)
        file_name = url.split('/')[-1].replace('.copc', '')
        out_fp = os.path.join(out_dir, file_name).replace('\\', '/')

        # arcpy.AddMessage(out_fp)
        pipeline.extend([{"type" : "readers.las", "filename" : url}])
        
    # pipeline.append({"type" : "filters.merge"})
    pipeline.append({"type" :"writers.las", "filename": out_fp})

    pipeline = dict(pipeline = pipeline)
    # print('DOWNLOADING NOW')

    with open(pipeline_fp, 'w') as f:
        json.dump(pipeline, f)
    # subprocess.run(['pdal', 'pipeline', pipeline_fp])

    pipeline = pdal.Pipeline(json.dumps(pipeline))
    pipeline.execute()
