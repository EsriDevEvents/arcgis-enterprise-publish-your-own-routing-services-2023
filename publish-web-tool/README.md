# Publish Web Tool utility

## Description
Typically, when you develop a geoprocessing service/ web tool, you need to run the script tool in ArcGIS Pro, and use Share As Web Tool pane to [share the geoprocessing history item as a web tool](https://pro.arcgis.com/en/pro-app/latest/help/analysis/geoprocessing/share-analysis/publishing-web-tools-in-arcgis-pro.htm). When you make modifications to the script tool that is used to publish as service, you will need to manually run the tool again and publish. This becomes tedious and makes it slow to iterate through your code changes. This utility helps to automate the running of the script tool and the publishing of the web tool.

The utility runs a script tool within a toolbox, based on the sample inputs you provide, and shares the history of the script tool as a web tool to the portal and federated server you specify.

The utility also implements various best practices to get a performant custom routing service. The sample utility publishes a synchronous geoprocessing service, and also sets [reusejobdir](https://pro.arcgis.com/en/pro-app/latest/help/analysis/geoprocessing/share-analysis/geoprocessing-service-settings-advanced.htm#ESRI_SECTION1_248170C25E4D44C0A2FAF61EA5D30B00) to True to achieve optimal performance.

## Usage

### Call *Publish Web Tool* from the command line
Once you [start the ArcGIS Pro Python 3 conda environment from a command prompt](https://pro.arcgis.com/en/pro-app/2.9/arcpy/get-started/installing-python-for-arcgis-pro.htm#ESRI_SECTION1_CD96A9B97F874266A6F6CDBF6FE5FEDA), use the -h flag to learn how to run the tool from the command line.
```
python publish_webtool.py -h
```

You can specify the parameters one by one, or you can pass in a file containing the parameters and values using an @ symbol. In the example, we have a [publish_sample_file.txt](publish_sample_file.txt) which contains a sample file that specifies the inputs to the utility tool. The [tool_inputs.json](tool_inputs.json) is used to specify the inputs used to run the tool. The example is based on the script tool in [this tutorial](https://pro.arcgis.com/en/pro-app/latest/help/analysis/networks/gettraveldirections-geoprocessing-service-example.htm).

To run the command line with a file:
```
python publish_webtool.py @full_path_to_the_file
```

For example:
```
python publish_webtool.py @C:\publish-web-tool\publish_sample_file.txt
```