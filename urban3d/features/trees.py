import sys
sys.path.append(r"D:\05_Projects\01_Active\Toronto Digital Twin\urban-3d")

import os
import os
import laspy
import numpy as np
from glob import glob
from pathlib import Path
import pandas as pd
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from urban3d.pc.ops import run_pdal_pipeline
from urban3d.features.treeiso.treeiso import process_las_file
import json
import pdal
COUNT_LIMIT = 800000

# def get_las_paths(in_folder, out_folder, out_extension=None):
    
#     # Input File Paths
#     in_files = os.listdir(in_folder)
#     in_las_paths = glob(os.path.join(in_folder, "*.la[sz]"))
#     in_las_sffx = [''.join(Path(in_las).suffixes) for in_las in in_las_paths]

#     # Output File Paths
#     out_files = [file.replace(suffix,f'{suffix if out_extension is None else f'{out_extension}{suffix}'}') for file, suffix in zip(in_files, in_las_sffx)]
#     out_las_paths = [os.path.join(out_folder, file) for file in out_files]

#     return in_las_paths, out_las_paths


def pdal_tree_filter(in_las, out_folder, count_limit):
    fp = Path(in_las)
    suffix =  ''.join(fp.suffixes)

    in_las_name = in_las.split('/')[-1]
    out_file = in_las_name.replace(suffix, f'_filtered_#.laz')

    pipeline_dict = dict(
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
                    "expression" : "Classification != 2 && (HeightAboveGround < 40 && HeightAboveGround > 0)"
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
                    "expression" : "Classification != 7",
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
    
    )
    
    print(pipeline_dict)
    # Run PDAL Pipeline
    pipeline_json = json.dumps(pipeline_dict)
    pdal_pipeline = pdal.Pipeline(pipeline_json)
    print('Running Pipeline')
    pdal_pipeline.execute()

    



# Filter Points by Height Above Ground
def filter_by_hag(in_las, out_las, multiplier):
    
    las = laspy.read(in_las)
    hag = las.HeightAboveGround
    mean_hag = np.mean(hag)
    std_hag =  np.std(hag)

    hag_mask = (hag < (mean_hag  + (std_hag * multiplier))) & (hag > 0.5)
    las_hag_filtered = las[hag_mask]

    las_hag_filtered.write(out_las)



def initial_filter(filtered_paths, cleaned_paths):
    for in_las, out_las in zip(filtered_paths, cleaned_paths):
        if os.path.exists(out_las) == False:
            las = laspy.read(in_las)
            dimensions = ['X', 'Y', 'Z', 'ClusterID','intensity', 'number_of_returns', 'Curvature', ]

            # ## Filter by Cluster ID
            df = build_las_df(las, dimensions, rescale=True)
            cluster_id = select_tree_cluster(df)
            las = las[las.ClusterID == cluster_id]

            
            # # ## Filter By Height Above Ground
            hag = las.HeightAboveGround
            # q = np.percentile(hag, q = 0.99)
            hag_mask = hag < 40
            las = las[hag_mask]

            # ## Write LAS
            las.write(out_las)
        else:
            print(f'- Exists: {out_las}')


def isolate_trees(cleaned_paths, classified_paths):
    for in_las, out_las in zip(cleaned_paths, classified_paths):
        if os.path.exists(out_las) == False:
            # ## Isolate Trees
            process_las_file(in_las, out_las, if_isolate_outlier=False)

            ## Second Kmeans Pass to filter out Trees from Tree ISO Segments
            las = laspy.read(out_las)
            dimensions = ['X', 'Y', 'Z', 'final_segs','intensity', 'number_of_returns', 'Curvature',  ]
            df = build_las_df(las, dimensions, rescale=True)
            df['final_segs'] = las.final_segs
            df_mean = df.groupby('final_segs').mean().reset_index()
            df_mean['count'] = df.groupby('final_segs').X.count()

            kmeans = KMeans(n_clusters= 2)
            df_mean['ClusterID'] = kmeans.fit_predict(df_mean[['Curvature', 'intensity']])
            df_mean = df_mean[df_mean.ClusterID == select_tree_cluster(df_mean)]

            q_lower =  df_mean['count'].quantile(q=0.3)
            q_upper =  df_mean['count'].quantile(q=0.99)
            df_mean = df_mean[(df_mean['count'] > q_lower) & (df_mean['count'] < q_upper)] 

            ## Out put Cleaned Las with Trees
            las_clean = las[df.final_segs.isin(df_mean.final_segs).values]
            las_clean.write(out_las)
        else:
            print(f'- Exists: {out_las}')



def build_las_df(las, dimensions, rescale = False):
    f= np.column_stack([las[dim] for dim in dimensions])
    df = pd.DataFrame(f, columns= dimensions)
    if rescale:
        df = (df - df.min())/ (df.max() - df.min())
        df.ClusterID = las.ClusterID
        return df
    else:
        return df

def select_tree_cluster(df):
    df_mean = df.groupby('ClusterID').mean().T

    # Cluster with Lowest Intensity
    it = 0 if df_mean[0].intensity < df_mean[1].intensity else 1
    
    # Cluster with Higest Curvature
    nr = 0 if df_mean[0].number_of_returns > df_mean[1].number_of_returns else 1

    # Cluster with Highest Number of Returns
    cr = 0 if df_mean[0].Curvature > df_mean[1].Curvature else 1


    votes = [it, nr, cr]

    return max(set(votes), key=votes.count)
