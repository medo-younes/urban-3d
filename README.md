# Urban3D

## A Python Toolkit for extracting urban features from 3D Point Clouds (In Development)

Urban3D is a Python toolkit that automates the extraction of semantic urban features such as building components (coming soon) and trees. It is available as both an open-source project and an integrated ArcGIS Python Toolbox for ESRI users. Currently supported features are:

1. Automated 3D Point Cloud Download with Bounding Box from [CanElevation LiDAR Series](https://open.canada.ca/data/en/dataset/7069387e-9986-4297-9f55-0288e9676947)
2. Isolating 3D Trees with PDAL and [TreeIso](https://github.com/truebelief/artemis_treeiso)


<div style="text-align: center;">
  <img src="media/trees.png" alt="drawing" width="600">
</div>


## ArcGIS Python ToolBox Installation

1. First [clone your default ArcGIS Pro conda environment](https://pro.arcgis.com/en/pro-app/3.3/arcpy/get-started/clone-an-environment.htm).
2. Once created, copy the environment's path from the Environment Manager window.


```bash
# Clone the repo to your ArcGIS Project Directory
cd your-arcgis-project-directory
git clone https://github.com/medo-younes/urban-3d.git
cd urban-3d

# Activate environment using global path to conda env
conda activate C:\Users\USER\AppData\Local\ESRI\conda\envs\urban3d
conda env update -n C:\Users\USER\AppData\Local\ESRI\conda\envs\urban3d -f arcgis-environment.yml
```
3. In ArcGIS Pro:
   - Open the **Catalog Pane**
   - Right-click on **Toolboxes**
   - Select **Add Toolbox**
   - Browse to your downloaded `.pyt` file
   - Click **OK**

## Regular Installation (coming soon)

<!-- ```
git clone https://github.com/medo-younes/urban-3d.git
``` -->

<!-- ## Downloading 3D Point Clouds

```python

from urban3d.canelevation import 

``` -->

<!-- # Getting Started
- Sample Data -->

