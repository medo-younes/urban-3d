# -*- coding: utf-8 -*-
## Import Libraries

import sys
import os

# Add library path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'urban3d')
sys.path.insert(0, lib_path)

import arcpy
import geopandas as gpd
import os
from pathlib import Path
import re
import pdal
import json
import shapely

import config
# Path to the ArcGIS Pro project
aprx = arcpy.mp.ArcGISProject("CURRENT")
gdb = aprx.defaultGeodatabase

# Access the scene (you can also use 'Map' or other names as needed)
maps = aprx.listMaps()  # Adjust name as necessary
scenes = [mp for mp in aprx.listMaps() if mp.mapType == 'SCENE']
scene_names = [scene.name for scene in scenes]

# Setup Working Directory
cwd = Path(aprx.filePath).parent
os.chdir(cwd)

file_ext ='.copc.laz'





## Map Setup
#====================================================================================================================
lidar_coverage_fp = r'D:\05_Projects\01_Active\Toronto Digital Twin\notebooks\lidar_coverage.shp'
maps = aprx.listMaps()
map_names = [mp.name for mp in maps]

def configure_map():
    if 'SELECT REGION' not in map_names:
        region_map = aprx.createMap('SELECT REGION', 'MAP')
    else:
        region_map = maps[map_names.index('SELECT REGION')]

    # Check if layer is already in the map
    layer_exists = any(lyr.name == 'lidar_coverage' for lyr in region_map.listLayers())

    if layer_exists:
        coverage_layer = [lyr for lyr in region_map.listLayers() if lyr.name == 'lidar_coverage'][0]
        print("Layer already exists.")
    else:
        coverage_layer = region_map.addDataFromPath(lidar_coverage_fp)
        print("Layer not found.")
    


## FUNCTIONS
#====================================================================================================================

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




## ToolBox Class
#====================================================================================================================
class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # Force refresh of modules
        import importlib
        import sys
        
        # If you have helper modules, reload them
        if 'urban3d' in sys.modules:
            importlib.reload(sys.modules['urban3d'])
        # List of tool classes associated with this toolbox
        
        self.tools = [DownloadLiDAR, IsolateTrees]



class DownloadLiDAR:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download CanElevation LiDAR"
        self.description = '''
                Download LiDAR 3D Point Clouds from: https://open.canada.ca/data/en/dataset/7069387e-9986-4297-9f55-0288e9676947
                The LiDAR Point Clouds is a product that is part of the CanElevation Series created to support the National Elevation Data Strategy implemented by NRCan.

                This product contains point clouds from various airborne LiDAR acquisition projects conducted in Canada. These airborne LiDAR acquisition projects may have been conducted by NRCan or by various partners. The LiDAR point cloud data is licensed under an open government license and has been incorporated into the National Elevation Data Strategy.

                Point cloud files are distributed by LiDAR acquisition project without integration between projects.

                The point cloud files are distributed using the compressed .LAZ / Cloud Optimized Point Cloud (COPC) format. The COPC open format is an octree reorganization of the data inside a .LAZ 1.4 file. It allows efficient use and visualization rendering via HTTP calls (e.g. via the web), while offering the capabilities specific to the compressed .LAZ format which is already well established in the industry. Point cloud files are therefore both downloadable for local use and viewable via URL links from a cloud computing environment.

                The reference system used for all point clouds in the product is NAD83(CSRS), epoch 2010. The projection used is the UTM projection with the corresponding zone. Elevations are orthometric and expressed in reference to the Canadian Geodetic Vertical Datum of 2013 (CGVD2013).

            '''
        
        # configure_map()

    def getParameterInfo(self):
        """Define the tool parameters."""

        configure_map()
        params = [
            arcpy.Parameter(
                displayName = "Input Region of Interest",
                name = "project_name",
                datatype = "String",
                parameterType="Required",
                direction = "Input"
            ),
            arcpy.Parameter(
                displayName = "Input Region of Interest",
                name = "input_roi",
                datatype = "GPFeatureLayer",
                parameterType="Required",
                direction = "Input"
            ),
            arcpy.Parameter(
                displayName = "Add to Scene",
                name = "scene_name",
                datatype = "String",
                parameterType="Optional",
                direction = "Input"
            )
        ]
        params[2].filter.type = 'ValueList'
        
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        parameters[1].filter.list = scene_names

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        from urban3d.data.canelevation import download_laz_files
        from urban3d.pc.ops import clip_laz_files
        from urban3d import config
        # Create Cirectory if Needed
        


        
        project_name = parameters[0].ValueAsText
        input_roi = parameters[1].ValueAsText ## May have to retrieve database or path name in the future
        scene_name = parameters[2].ValueAsText
   

        RAW, LAZ,LAS, FILTERED, CLASSIFIED, MERGED = config.data_folder(project_name)


        # Get AWS S3 Endpoints for overlapping point cloud tiles
        bbox_gdf = gpd.read_file(gdb, layer = input_roi).dissolve()
        bbox_geom = bbox_gdf.geometry.iloc[0]
        bbox_wkt = shapely.force_2d(bbox_geom).wkt

        # Read Tiles ShapeFile as GeoDataFrame
        tile_index_gdf = gpd.read_file(gdb, bbox = bbox_gdf, layer ='lidar_tile_index', engine ='fiona')

        tile_index_gdf['year'] = tile_index_gdf.Project.apply(lambda st: max(re.findall(r'\d+' ,st))).astype(int)
        latest_year = tile_index_gdf.year.astype(int).max()
        tiles_gdf_latest = tile_index_gdf[tile_index_gdf.year == latest_year]

        ## Get Name of Project
        project_name = tiles_gdf_latest.Project.value_counts().reset_index().iloc[0].Project
        
        
        # Spatial join to find only matching tiles
        matching_urls = tiles_gdf_latest.URL.to_list()
        print(f'Found {len(matching_urls)} Matching LAZ Files within Bounds for {latest_year}')
        print(f'PROJECT ID: {project_name}')
        arcpy.AddMessage(f'Found {len(matching_urls)} Matching LAZ Files within Bounds for {latest_year}')


        # Setup Directory Paths
        merged_fp = os.path.join(MERGED, f'{project_name}.las')


        # Batch Download LAZ Files
        ## Download Matching LAZ Files from NRCAN S3 Bucket
        # download.download_from_urls(matching_urls, output_path, bbox_wkt)
        download_laz_files(matching_urls,LAZ)
        arcpy.AddMessage('- CLIPPING AND MERGING; Outputting as LAS')
        clip_laz_files(LAZ, bbox_wkt, merge = True)


        # # Create LAS Dataset
        output_las_ds_fp = os.path.join(LAS , f'{project_name}.lasd')
        arcpy.management.CreateLasDataset(merged_fp,output_las_ds_fp)
        arcpy.AddMessage(f'- LAS Dataset Created: {output_las_ds_fp}')

        # # Create LAS Dataset Pyramid
        arcpy.management.BuildLasDatasetPyramid(output_las_ds_fp)
        arcpy.AddMessage(f'- LAS Dataset Pyramid Created: {output_las_ds_fp}')
        
        # # Add LAS dataset to the scene
        scene = aprx.listMaps(scene_name)[0]
        if scene is not None:
            scene.addDataFromPath(output_las_ds_fp)
            arcpy.AddMessage(f'- LAS Dataset Pyramid Added to Scene: {output_las_ds_fp}')
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return



class IsolateTrees:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Isolate Trees"
        self.description = '''
                Filter a CanElevation point cloud and isolate trees using the Treeiso solution

            '''
        

    def getParameterInfo(self):
        """Define the tool parameters."""

        configure_map()
        params = [
            arcpy.Parameter(
                displayName = "Input LAS Point Cloud",
                name = "in_las",
                datatype = "DEFile",
                parameterType="Required",
                direction = "Input"
            ),
            arcpy.Parameter(
                displayName = "Output Folder",
                name = "out_folder",
                datatype = "DEFolder",
                parameterType="Required",
                direction = "Input"
            ),
            arcpy.Parameter(
                displayName = "Add to Scene",
                name = "scene_name",
                datatype = "String",
                parameterType="Optional",
                direction = "Input"
            )
        ]
        
        # Set the filter to only show LAS and LAZ files
        params[0].filter.list = ['las', 'laz']
        params[1].filter.type = 'ValueList'
        
    

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Find all LAS/LAZ files in the project
        las_files = []
        
        # Check all maps in the project
        for map_obj in aprx.listMaps():
            for layer in map_obj.listLayers():
                if hasattr(layer, 'dataSource'):
                    if layer.dataSource.lower().endswith(('.las', '.laz')):
                        las_files.append(layer.dataSource)
        
        # Set the filter list if files are found
        if las_files:
            parameters[0].filter.list = las_files

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""


        # from urban3d.trees import initial_filter, isolate_trees
        from urban3d.features import trees
        from urban3d import config
        
        in_las = parameters[0].ValueAsText
        out_folder = parameters[1].ValueAsText
        suffix =''.join(Path(in_las).suffixes)
        in_las_name = Path(in_las).name.replace(suffix,'')

        RAW, LAZ,LAS, FILTERED, CLASSIFIED, MERGED = config.data_folder(out_folder)
        out_merged = os.path.join(MERGED, f'{in_las_name}_merged.las')

        arcpy.AddMessage(f'- Folder Configuration Complete: {out_folder}')


        ## Execute Tree Filtering Pipeline
        if len(os.listdir(FILTERED)) ==0:
            trees.pdal_tree_filter(in_las, FILTERED, count_limit=800000, run = True)
            arcpy.AddMessage(f'- PDAL Pipeline Complete')
        else:
            arcpy.AddMessage(f'- Filtered Point Clouds Already Found, proceeding to Initial Filter')


        ## Filter out Cluster ID with Trees
        filtered_las = [os.path.join(FILTERED,file) for file in os.listdir(FILTERED) if in_las_name in file and file.split('_')[-2]  == 'filtered']
        cleaned_las = [file.replace('.laz', '_cleaned.laz') for file in filtered_las if '_filtered' in file]
        classified_las = [file.replace('_cleaned.laz', '_treeiso.laz').replace('filtered/', 'classified/') for file in cleaned_las]


        # ## FILTERING BY CLUSTER ID AND HEIGHT
        trees.initial_filter(filtered_las, cleaned_las)

        # # ## TREE ISOLATION AND FINAL K MEANS FILTER
        trees.isolate_trees(cleaned_las, classified_las)

        arcpy.AddMessage(out_merged)
        ## Merge Chipped Trees
        p = classified_las.copy()
        # trees.pdal_merge(classified_las, out_merged)
        p.extend([{"type": "filters.merge"}, {"type" : "writers.las", "filename" : out_merged}])
        p = dict(pipeline = p)
        p = pdal.Pipeline(json.dumps(p))
        p.execute()
        arcpy.AddMessage('- Merge Complete')

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
