import os 

# COORDINATE REFERENCE SYSTEM
crs_h = "EPSG:26917"
crs_v = "6647"
crs = f'{crs_h}+{crs_v}'

ROOT = "../"
DATA = os.path.join(ROOT, "data")
MODELS = os.path.join(ROOT, "models")


# Define Auxillart Directories
RAW = os.path.join(DATA , "raw")
LABELLED = os.path.join(DATA, "labelled")
PROCESSED = os.path.join(DATA, "processed")
