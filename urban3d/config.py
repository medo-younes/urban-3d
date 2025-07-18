import os 

# COORDINATE REFERENCE SYSTEM
crs_h = "EPSG:26917"
crs_v = "6647"
crs = f'{crs_h}+{crs_v}'

## S3 Bucket Options
S3_BUCKETS = {
            "CanElevation Series - LiDAR Point Clouds" : "canelevation-lidar-point-clouds"
}

S3_BUCKET_OPTIONS = list(S3_BUCKETS.keys())
DEFAULT_S3_BUCKET = "CanElevation Series - LiDAR Point Clouds"

os.environ['OMP_NUM_THREADS'] = '3'


## DATA DIRECTORIES
ROOT = "../"
DATA = os.path.join(ROOT, 'PointCloudData/')

## PROJECT ROOT DIRECTORIES
PROJECT_ROOT = "../"
MODELS = os.path.join(PROJECT_ROOT, "models")
MEDIA = os.path.join(PROJECT_ROOT, "media")
NOTEBOOKS = os.path.join(PROJECT_ROOT, "notebooks")


def config_data_folder(project_name):

    project_folder = os.path.join(DATA, project_name)

    if os.path.exists(project_folder) == False:
        os.mkdir(project_folder)

    RAW = os.path.join(project_folder, 'raw/')
    LAZ = os.path.join(RAW, 'LAZ/')
    LAS = os.path.join(RAW, 'LAS/')
    FILTERED = os.path.join(project_folder, 'filtered/')
    CLASSIFIED = os.path.join(project_folder, 'classified/')
    MERGED = os.path.join(project_folder, 'merged/')
    PATHS = [RAW, LAZ,LAS, FILTERED, CLASSIFIED, MERGED]
    for path in PATHS: os.mkdir(path) if os.path.exists(path) == False else None
    print('- Folder Configuration Complete')
    return PATHS
