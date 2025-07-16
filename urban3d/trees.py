import pdal
import json
import os
import laspy
import numpy as np
from treeiso.treeiso import process_las_file
from glob import glob
from pathlib import Path
import pandas as pd

COUNT_LIMIT = 800000

def get_las_paths(in_folder, out_folder, out_extension=None):
    
    # Input File Paths
    in_files = os.listdir(in_folder)
    in_las_paths = glob(os.path.join(in_folder, "*.la[sz]"))
    in_las_sffx = [''.join(Path(in_las).suffixes) for in_las in in_las_paths]

    # Output File Paths
    out_files = [file.replace(suffix,f'{suffix if out_extension is None else f'{out_extension}{suffix}'}') for file, suffix in zip(in_files, in_las_sffx)]
    out_las_paths = [os.path.join(out_folder, file) for file in out_files]

    return in_las_paths, out_las_paths



def pdal_tree_filter(in_las, out_folder, count_limit, k = 8):
    fp = Path(in_las)
    suffix =  ''.join(fp.suffixes)
    out_file = str(fp.name).replace(suffix, f'_filtered_#{suffix}')

    pp= dict(
        pipeline = [
                {
                    "type" : "readers.las",
                    "filename" : in_las,
                },
                {
                    "type": "filters.expression",
                    "expression" : "Classification != 6 && Classification != 7 && Classification != 18"
                },
                {
                    "type" : "filters.csf",
                },
                {
                    "type": "filters.hag_nn",
                    "count" : 10,
                    "allow_extrapolation" : True
                },
                {
                    "type" : "filters.expression",
                    "expression" : "Classification != 2"
                },
                {
                    "type" : "filters.neighborclassifier",

                    "k" : 16,
                },
                {
                    "type": "filters.outlier",
                    "method": "statistical",
                    "mean_k" : 16,
                    "multiplier" : 2.2
                },
                {
                    "type":"filters.elm",
                    "threshold":2.0
                },
                {
                    "type" : "filters.expression",
                    "expression" : "Classification != 7",
                },
                {
                    "type":"filters.normal",
                    "knn": 30
                },
                {
                    "type":"filters.covariancefeatures",
                    "knn":30,
                    "threads": 8,
                    "feature_set": "Anisotropy, Scattering,SurfaceVariation"
                },
                {
                    "type":"filters.lloydkmeans",
                    "k": 2,
                    "maxiters": 20,
                    "dimensions":"Intensity, NumberOfReturns, Anisotropy, Scattering, SurfaceVariation",
                },
                {
                    "type" : "filters.neighborclassifier",
                    "k" : 16,
                    "dimension" : "ClusterID"
                },
                {
                    "type" : "filters.expression",
                    "expression" : "HeightAboveGround>2 && Classification != 7",
                },
                {
                    "type" : "filters.chipper",
                    "capacity" : count_limit
                },
                {
                    "type" : "writers.las",
                    "filename" : os.path.join(out_folder, out_file),
                    "extra_dims" : "all"
                },
                
        ],
        options = {
            "threads": 8
        }
    )

    return pdal.Pipeline(json.dumps(pp))



def batch_filter_by_hag(in_folder, out_folder, multiplier):
    in_las_paths, out_las_paths = get_las_paths(in_folder, out_folder, out_extension="")

    for in_las, out_las in zip(in_las_paths, out_las_paths):
        filter_by_hag(in_las, out_las, multiplier)

# Filter Points by Height Above Ground
def filter_by_hag(in_las, out_las, multiplier):
    
    las = laspy.read(in_las)
    hag = las.HeightAboveGround
    mean_hag = np.mean(hag)
    std_hag =  np.std(hag)

    hag_mask = (hag < (mean_hag  + (std_hag * multiplier))) & (hag > 0.5)
    las_hag_filtered = las[hag_mask]

    las_hag_filtered.write(out_las)



def isolate_trees_from_chips(in_folder, out_folder):
    in_las_paths, out_las_paths = get_las_paths(in_folder, out_folder, out_extension="_treeiso")

    for in_las, out_las in zip(in_las_paths, out_las_paths):
        process_las_file(in_las, out_las = out_las)



def build_las_df(las, dimensions, rescale = False):
    f= np.column_stack([las[dim] for dim in dimensions])
    df = pd.DataFrame(f, columns= dimensions)
    if rescale:
        df = (df - df.min())/ (df.max() - df.min())
        df.ClusterID = las.ClusterID
        return df
    else:
        return df

def select_cluster(df):
    df_mean = df.groupby('ClusterID').mean().T

    # Cluster with Lowest Intensity
    it = 0 if df_mean[0].intensity < df_mean[1].intensity else 1
    
    # Cluster with Higest Curvature
    nr = 0 if df_mean[0].number_of_returns > df_mean[1].number_of_returns else 1

    # Cluster with Highest Number of Returns
    cr = 0 if df_mean[0].Curvature > df_mean[1].Curvature else 1


    votes =[it, nr, cr]

    return max(set(votes), key=votes.count)
