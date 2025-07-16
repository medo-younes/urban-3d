
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
import arcpy
from pathlib import Path
import boto3
import re
from datetime import datetime

# S3 Bucket Name
BUCKET_NAME = 'canelevation-lidar-point-clouds'
s3 = boto3.client('s3') # Define Boto3 client

## FUNCTIONS
def download_s3(bucket_name, url, out_dir):

    url_path = Path(url)
    object_name = '/'.join(url_path.parts[2:])
    file_name = url_path.name
    out_path = f'{out_dir}/{file_name}'

    if os.path.exists(out_path):
        arcpy.AddMessage(f'-ALREADY EXISTS: {file_name}')
    else:
        s3.download_file(bucket_name, object_name, out_path)
        arcpy.AddMessage(f'-DOWNLOADED: {file_name}')


def get_matching_urls(tile_index_fp, gdb, layer):    
    # Read Feature Class with GeoPandas
    bbox_gdf = gpd.read_file(gdb, layer = layer).dissolve()

    # Read Tiles ShapeFile as GeoDataFrame
    tile_index_gdf = gpd.read_file(tile_index_fp, bbox = bbox_gdf, engine ='fiona')
    arcpy.AddMessage(str(len(tile_index_gdf)))
    tile_index_gdf['year'] = tile_index_gdf.Project.apply(lambda st: max(re.findall(r'\d+' ,st))).astype(int)
    latest_year = tile_index_gdf.year.astype(int).max()
    tiles_gdf_latest = tile_index_gdf[tile_index_gdf.year == latest_year]

    ## Get Name of Project
    project_name = tiles_gdf_latest.Project.value_counts().reset_index().iloc[0].Project
    project_id = f'{project_name}/{datetime.now().strftime("%Y%m%d_%H%M%S")}' # Configure unique project ID

    # Spatial join to find only matching tiles
    matching_urls = tiles_gdf_latest.URL.to_list()
    arcpy.AddMessage(f'Found {len(matching_urls)} Matching LAZ Files within Bounds for {latest_year}')
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

def batch_laz_to_las(laz_dir, las_dir):
    ## Convert LAZ to LAS
    laz_fps = [f'{laz_dir}/{laz_fp}' for laz_fp in os.listdir(laz_dir)]
    for laz_fp in laz_fps:
        arcpy.conversion.ConvertLas(
                    in_las = laz_fp,
                    target_folder = las_dir,        
        )
        arcpy.AddMessage(f'- Successfully converted: {laz_fp.split("/")[-1]}')


def create_las_pyramid(las_dir, output_las_fp):
    # Setup Out File Name based on LAS file name
    las_name = os.listdir(las_dir)[0].split('_')[1]

    # Create LAS Dataset
    arcpy.management.CreateLasDataset(las_dir,output_las_fp)
    arcpy.AddMessage(f'- LAS Dataset Created: {output_las_fp}')

    # Create LAS Dataset Pyramid
    arcpy.management.BuildLasDatasetPyramid(output_las_fp)
    arcpy.AddMessage(f'- LAS Dataset Pyramid Created: {output_las_fp}')