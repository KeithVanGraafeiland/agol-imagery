## Import required libraries
import os
import arcpy
import getpass
import arcgis
from arcgis.raster import *
from arcgis.raster.analytics import *
from arcgis.gis import GIS
from keith_oceans_credentials import username, password, org_url

# Set environment variables
arcgis.env.verbose = True
arcgis.env.overwrite = True

# Disable SSL warnings
import urllib3
urllib3.disable_warnings()

gis = GIS(org_url, username, password, verify_cert=True)
gis

def publish_hosted_imagery_from_crf(crf_path, imagery_layer_name):
    """
    Publishes a raster dataset to ArcGIS Online as a hosted imagery service.

    Parameters:
    crf_path (str): The path to the CRF file to be published.
    imagery_layer_name (str): The name of the service to be published.
    service_summary (str): A summary of the service to be published.
    service_tags (str): Tags to be applied to the service.
    folder_name (str): The name of the folder in which the service will be published.
    gis (arcgis.gis.GIS): The GIS object to be used for publishing the service.
    service_type (str): The type of service to be published.
    service_description (str): A description of the service to be published.
    service_snippet (str): A snippet of the service to be published.
    service_thumbnail (str): The path to the thumbnail image to be used for the service.
    """

    upload_crf = crf_path

    ### Extract the crf path, folder name, and the file name

    crf_path = os.path.dirname(upload_crf)
    print(crf_path)
    folder_name = "imagery_upload"
    print(folder_name)
    crf_name = os.path.basename(upload_crf)
    print(crf_name)

    access_url = arcgis.raster.utils.generate_direct_access_url(expiration=1440, gis=gis)
    access_url

    azure_account_name = access_url.split('//')[1].split('.')[0]
    print("Azure account name: " + azure_account_name)
    azure_container = access_url.split('?')[0].split('/')[-1]
    print("Azure container name: " + azure_container)
    azure_sas_token = access_url.split('?')[1].split('/')[-1]
    print("Azure storage SAS Token: " + azure_sas_token)
    azure_cpl_endpoint = access_url.split('/')[0] + "//" +  access_url.split('/',3)[-2]
    print("Azure CPL Endpoint: " + azure_cpl_endpoint)

    acs_folder = r'E:\gis_lib\00_common\acs_connections'
    target_connection_file = "agol_azure.acs"
    acs_full_path = os.path.join(acs_folder, target_connection_file)

    if os.path.exists(acs_full_path):
        os.remove(acs_full_path)

    account_name = azure_account_name
    container_name = azure_container
    config_options = "AZURE_STORAGE_SAS_TOKEN " +  azure_sas_token + ";CPL_AZURE_ENDPOINT " + azure_cpl_endpoint

    source_connection = arcpy.management.CreateCloudStorageConnectionFile(
        out_folder_path=acs_folder, 
        out_name=target_connection_file,
        service_provider="AZURE", 
        bucket_name=container_name, 
        access_key_id=account_name,
        config_options=config_options)
    
    source = upload_crf
    target = os.path.join(acs_folder, target_connection_file, folder_name, crf_name)
    arcpy.management.TransferFiles(source, target)
    print(target)
    print(source)

    data_url = access_url.split('?')[0] + "/" + folder_name + "/" + crf_name
    print(data_url)

#    # Check if the imagery layer already exists
#     existing_layers = gis.content.search(query=imagery_layer_name, item_type="Imagery Layer")
#     for layer in existing_layers:
#         if layer.title == imagery_layer_name:
#             print(f"Imagery layer '{imagery_layer_name}' already exists.")
#             return layer
#         else:
#             print(f"Imagery layer '{imagery_layer_name}' does not exist. Proceeding with publishing.")
    ImageryLayer = copy_raster(input_raster=data_url,
                                output_name=imagery_layer_name,
                                context={"compression":"LERC 0"},
                                gis=gis)
    ImageryLayer.update(item_properties={"tags": "climate, ocean, CMIP6, SSP3-7.0, NOAA",
                                        "snippet": "This layer is from NOAA's Climate Change Web Portal.  It was provided by Jamie Scott",
                                        "description": "This layer is from NOAA's Climate Change Web Portal, Accessed on 11/21/2024. URL = https://psl.noaa.gov/ipcc/cmip6/ This hosted imagery layer was published from a CRF file using the ArcGIS API for Python."})              
    return ImageryLayer

# # Example usage
# crf_path = r"E:\test\ssp370\arag_10m_1985.crf"
# imagery_layer_name = os.path.basename(crf_path).replace('.crf', '')
# publish_hosted_imagery_from_crf(crf_path, imagery_layer_name)

# Example batch usage
crf_folder = r'E:\test\ssp370'

for crf in os.listdir(crf_folder):
    crf_path = os.path.join(crf_folder, crf)
    imagery_layer_name = os.path.basename(crf_path).replace('.crf', '')
    publish_hosted_imagery_from_crf(crf_path, imagery_layer_name)