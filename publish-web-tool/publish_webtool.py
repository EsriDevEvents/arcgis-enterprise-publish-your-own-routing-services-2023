"""Publish the GP tool as a web tool.

This is a sample utility to run a script tool and publish as a web tool.

Copyright 2023 Esri
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import logging
import argparse
import json
import copy
from pathlib import Path
import xml.dom.minidom as DOM

import arcpy


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


def publish_webtool(portal_url, federated_server_url, username, password, service_name, output_sd_dir,
                    tbx_file, tool_name, tool_inputs):
    """Publish web tool execution logic.

    Args:
        portal_url (str): Portal url.
        federated_server_url (str): Federated server url.
        username (str): Username for an account on the portal with administrator privilege or publisher privilege that
        allows publishing web tools.
        password (str): Password for the user specified.
        service_name (str): Name of the geoprocessing service to publish the tool as.
        output_sd_dir (str): Full path to the directory on disk where you want to store the output service definition
        file.
        tbx_file (str): Full path to the toolbox file.
        tool_name (str): Name of the tool to run in the toolbox.
        tool_inputs (dict): Dictionary containing the parameters and values to run the tool once before publishing
        as a web tool.
    """
    output_dir = Path(output_sd_dir)
    sddraft_file = output_dir.joinpath(f"{service_name}.sddraft")
    sd_file = output_dir.joinpath(f"{service_name}.sd")

    tool_box_alias = "MyTool"
    LOGGER.info(f"Importing toolbox %s as %s", tbx_file, tool_box_alias)
    arcpy.ImportToolbox(tbx_file, tool_box_alias)

    LOGGER.info("Inspect tool and apply performance tip to create a network dataset layer before running tool.")
    tool_name_full = f"{tool_name}_{tool_box_alias}"
    tool = getattr(arcpy, tool_name_full)
    network_dataset_param_name = None
    params = arcpy.GetParameterInfo(tool_name_full)
    for param in params:
        # Performance trick to make network dataset layer based on network dataset path and use the layer to
        # run tool before publishing.
        if param.datatype == "Network Dataset Layer":
            try:
                network_dataset_param_name = param.name
                network_dataset = tool_inputs.get(network_dataset_param_name, None)
                if network_dataset:
                    nd_layer_name = "nd_layer"
                    nd_layer = arcpy.nax.MakeNetworkDatasetLayer(network_dataset, nd_layer_name)
                    tool_inputs[network_dataset_param_name] = nd_layer
            except Exception as ex:
                arcpy.AddWarning(f"Failed to create network dataset layer from {network_dataset}.\n{ex}")

    LOGGER.info("Running tool %s", tool_name)
    tool_result = tool(**tool_inputs)

    LOGGER.info("Create geoprocessing sharing draft %s", sddraft_file)
    sddraft = arcpy.sharing.CreateSharingDraft("FEDERATED_SERVER", "WEB_TOOL", service_name, tool_result)
    sddraft.offline = False
    sddraft.targetServer = federated_server_url
    sddraft.copyDataToServer = False
    sddraft.messageLevel = "Info"
    sddraft.executionType = "Synchronous"
    sddraft.maximumRecords = 1000
    sddraft.overwriteExistingService = True
    if network_dataset_param_name:
        sddraft.constantValues = [network_dataset_param_name]
    sddraft.exportToSDDraft(str(sddraft_file))
    # Turn on reusejobdir to make sync service faster.
    # Learn more at
    # https://pro.arcgis.com/en/pro-app/latest/help/analysis/geoprocessing/share-analysis/geoprocessing-service-settings-advanced.htm#ESRI_SECTION1_248170C25E4D44C0A2FAF61EA5D30B00
    LOGGER.info("Apply performance tip and set reusejobdir on the sharing draft file.")
    _enable_reuse_job_dir(str(sddraft_file))

    LOGGER.info("Stage service definition file %s", sd_file)
    arcpy.server.StageService(str(sddraft_file), str(sd_file))

    LOGGER.info("Signing into portal %s", portal_url)
    arcpy.SignInToPortal(portal_url, username, password)
    LOGGER.info("Publishing web tool %s", service_name)
    publish_result = arcpy.server.UploadServiceDefinition(str(sd_file), federated_server_url,
                                                          in_override="OVERRIDE_DEFINITION", in_public="PUBLIC")
    LOGGER.debug(publish_result.getMessages())
    LOGGER.info("REST Url: %s", f"{federated_server_url}/rest/services/{service_name}/GPServer/{tool_name}")

    LOGGER.info("Successfully completed")


def _enable_reuse_job_dir(sddraft_file):
    """Modify the sddraft file and enable reusejobdir property.

    Args:
        sddraft_file (str): path to the sddraft file.
    """
    doc = DOM.parse(sddraft_file)
    definition_node = doc.getElementsByTagName("Definition")[0]
    # Configuration properties
    config_props = definition_node.getElementsByTagName("ConfigurationProperties")[0].firstChild.childNodes
    update_existing_prop = False
    # If the service already contains a property called reusejobdir, simply update it to true.
    for prop in config_props:
        key, value = prop.childNodes
        prop_name = key.firstChild.data
        if prop_name == "reusejobdir":
            if value.firstChild is None:
                value.appendChild(doc.createTextNode("true"))
            else:
                value.firstChild.data = "true"
            update_existing_prop = True
    # If the service doesn't contain a property called reusejobdir, copy the first property and update it
    # to create a new property called reusejobdir, and set the value to true. And then append the property
    # to the propertyArray.
    if not update_existing_prop:
        copy_of_prop = copy.deepcopy(config_props[0])
        key, value = copy_of_prop.childNodes
        key.firstChild.data = "reusejobdir"
        if value.firstChild is None:
            value.appendChild(doc.createTextNode("true"))
        else:
            value.firstChild.data = "true"
        config_props.append(copy_of_prop)
    with open(sddraft_file, 'w') as out_fp:
        doc.writexml(out_fp)


def main():
    inputs = {
        "portal_url": "portal_url",
        "federated_server_url": "server_url",
        "username": "username",
        "password": "password",
        "service_name": "TravelDirections",
        "output_sd_dir": r"C:\SD",
        "tbx_file": r"C:\TravelDirections\TravelDirections.tbx",
        "tool_name": "GetTravelDirections",
        "tool_inputs": {
            "stops": r"C:\TravelDirections\SampleInput\SampleInput.gdb\Stops",
            "network_dataset": r"C:\TravelDirections\ToolData\SanDiego.gdb\Transportation\Streets_ND",
            "travel_mode": "Driving Time"
        }
    }

    with arcpy.EnvManager(overwriteOutput=True):
        publish_webtool(**inputs)


def cli():
    """Command line interface to run publish web tool utility."""

    parser = argparse.ArgumentParser(description=globals().get("___doc___", ""), fromfile_prefix_chars="@")

    help_string = "The url of the portal to publish web tool to."
    parser.add_argument("-P", "--portal-url", action="store", dest="portal_url", help=help_string, required=True)

    help_string = "The url of the federated server on the portal to host the web tool."
    parser.add_argument("-S", "--federated-server-url", action="store", dest="federated_server_url",
                        help=help_string, required=True)

    help_string = ("The username of the portal user that has administrative privilege or a publisher privilege "
                   "that allows publishing web tools.")
    parser.add_argument("-u", "--username", action="store", dest="username", help=help_string, required=True)

    help_string = "The password of the user who was specified with the -u parameter."
    parser.add_argument("-p", "--password", action="store", dest="password", help=help_string, required=True)

    help_string = "The name of the service to publish the tool as."
    parser.add_argument("-s", "--service-name", action="store", dest="service_name", help=help_string, required=True)

    help_string = "Path to a folder where the utility will create the service definition files for the services."
    parser.add_argument("-o", "--output-sd-dir", action="store", dest="output_sd_dir", help=help_string, required=True)

    help_string = "Path to the toolbox."
    parser.add_argument("-tbx", "-tbx-file", action="store", dest="tbx_file", help=help_string, required=True)

    help_string = "Name of the tool."
    parser.add_argument("-t", "-tool-name", action="store", dest="tool_name", help=help_string, required=True)

    help_string = ("File containing json that specifies the parameter names and values to run the tool once. "
                   "The web tool is shared from geoprocessing history, so we need some inputs to run the tool "
                   "before we can publish the tool as a web tool. To specify the inputs used to run the tool, "
                   "provide a json file, and the key is the parameter name (not alias), and the value is "
                   "the value to use for the parameter when running the tool. Note: You don't need to specify "
                   "all the parameters, you just need to specify the required parameters of your tool.")
    parser.add_argument("-f", "-tool-inputs-file", action="store", dest="tool_inputs_file", help=help_string,
                        required=True, type=argparse.FileType('r'))

    args = vars(parser.parse_args())
    tool_inputs_file = args.pop("tool_inputs_file")
    tool_inputs = json.load(tool_inputs_file)
    tool_inputs_file.close()
    args["tool_inputs"] = tool_inputs

    with arcpy.EnvManager(overwriteOutput=True):
        publish_webtool(**args)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # If you need to modify the publish web tool script and debug, enable main and disable cli and
    # provide the inputs in main function.
    # main()

    cli()
