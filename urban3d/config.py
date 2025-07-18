import os 

# COORDINATE REFERENCE SYSTEM
crs_h = "EPSG:26917"
crs_v = "6647"
crs = f'{crs_h}+{crs_v}'



os.environ['OMP_NUM_THREADS'] = '3'


## DATA DIRECTORIES
ROOT = "../../"
DATA = os.path.join(ROOT, 'PointCloudData/')


## PROJECT ROOT DIRECTORIES
PROJECT_ROOT = "../"
MODELS = os.path.join(PROJECT_ROOT, "models")
MEDIA = os.path.join(PROJECT_ROOT, "media")
NOTEBOOKS = os.path.join(PROJECT_ROOT, "notebooks")


def config_data_folder(project_name):
    
    if os.path.exists(DATA) == False:
        os.mkdir(DATA)

    out_folder = os.path.join(DATA, project_name)
    RAW = os.path.join(out_folder, 'raw/')
    LAZ = os.path.join(RAW, 'LAZ/')
    LAS = os.path.join(RAW, 'LAS/')
    FILTERED = os.path.join(out_folder, 'filtered/')
    CLASSIFIED = os.path.join(out_folder, 'classified/')
    MERGED = os.path.join(out_folder, 'merged/')
    PATHS = [RAW, LAZ,LAS, FILTERED, CLASSIFIED, MERGED]
    for path in PATHS: os.mkdir(path) if os.path.exists(path) == False else None
    print('- Folder Configuration Complete')
    return PATHS
