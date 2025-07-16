import arcpy

# Define variables
output_folder = r"Toronto Orthos/"  # Replace with your desired folder path
service_url = "https://gis.toronto.ca/arcgis/rest/services/basemap/cot_ortho_2023_color_10cm/MapServer"
extent = arcpy.Extent(629000, 4830000, 645000, 4842000)  # Adjust to your AOI in the same spatial ref
spatial_ref = arcpy.SpatialReference(26917)  # UTM Zone 17N (NAD83), used by City of Toronto

# Set environment
arcpy.env.outputCoordinateSystem = spatial_ref
arcpy.env.extent = extent

# Download parameters
image_output = f"{output_folder}\\toronto_ortho_2023.tif"

# Use arcpy's Export Map Server Cache to extract an image
arcpy.server.ExportMapServerCache(
    service_url,
    "default",
    image_output,
    "TIFF",
    "LAYER",
    "20",  # Zoom level (adjust based on desired resolution)
    extent,
    "",  # All tiles within extent
    "INDEXED"
)

print(f"Image downloaded to {image_output}")
