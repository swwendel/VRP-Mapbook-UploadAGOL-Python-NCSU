# VRP-Mapbook-UploadAGOL-Python-NCSU

## Summary

This is my final project for GIS 540 at NCSU. 

A Vehicle Routing Problem (VRP) is used to find routes for multiple stops and multiple vehicles in order to provide the best services at the lowest cost. For example, a package delivery service might use this to send your package on the quickest route to be delivered. They have many starting locations, stops, and trucks to fit into this equation to produce the best service. The output in ArcGIS Desktop might be easy for a GIS Analyst to read and understand, but the non-GIS users, such as drivers, need a simplified version of the information to do their part. The goal of this tool is to demonstrate how to generate PDF reports with maps and directions for a VRP analysis. This solution also takes advantage of ArcGIS Online to store the PDFs as well as the routes as feature services to use within web maps. The route feature services can be viewed by the driver in phone applications such as ArcGIS Online App to view their route and stay on track. This solution can be utilized by any industry that needs to produce map and turn by turn directions for its employees who need to travel to specific destinations, for example; pizza delivery, City Inspectors going to do inspections locations, delivering packages, etc. The point is to simplify the process of doing a VRP and to produce a user friendly information for the employee to follow.

## Features

* VRPS.py - Functions and classes used in the solution.
* Project_core_sawendel.py - Core file that handles the VRP solution and processing of the solution to make directions, a mapbook pdf, feature services and a webmap. 
	* Performs a VRP for given input Network Dataset, orders, routes, and depots.
	* Creates a PDF mapbook of the routes generated in the VRP solution with directions
	* Uploads the PDF to ArcGIS online to share with organization users.
	* Uploads and publishes Routes and Orders to ArcGIS online.
	* Creates a webmap of Routes and Orders for each Route.
	* Shares the webmap with the organizaiton users.


## Instructions

Note: This may not work with your data. Make sure to setup the VRP data to use the ArcGIS Defaults.

1. Fork and then clone the repo or download the files.
2. Install requests module for python. It can be found [here](https://github.com/kennethreitz/requests). 
3. Download the toolbox, map, and sample data to the machine and keep the
    structure the same. The sample uses relative paths.
4. Open vrp_project.mxd.
5. Make find the VRP Project toolbar.
6. Click the VRP button.
7. For the sample data, keep the default values. For the users own data, fill
    out the appropreiate parameters. Make sure to use feature classes and schema
    that follow the standard VRP schemas. For more information on setting that
    up please see the Vehicle routing problem analysis help page link below.
8. Run the tool. The output will be a PDF and webmap posted on ArcGIS Online.


## Requirements

* Your favorite Python editor to make modifications to the code.
* ArcMap 10.1 Advanced License
* Network Analyst License
* ArcGIS Online Organization account with upload and publishing permissions.
* requests 2.2.1 python module found at:
    *Github:https://github.com/kennethreitz/requests
    *pypi: https://pypi.python.org/pypi/requests


## Resources

[ArcGIS Help 10.1, Vehicle routing problem analysis](http://resources.arcgis.com/en/help/main/10.1/index.html#//00470000004v000000)
[ArcGIS REST API] http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r300000054000000
DataSources.txt - provides the sources of the sample data used in this example.

## Issues

If you find a bug or want to request a new feature, please let me know by submitting an issue on this page.

This sample was only tested using ArcGIS 10.1 sp1. Due to differences in versions
there is a chance there could be issues at different versions of the software.

This sample was not tested using 64-bit background geoprocessing. Issues may
arise if the script tool is allowed to run in the background.

## Contributing

Anyone and everyone. I follow the Esri Github guidelines for contributing. Please see [guidelines for contributing](https://github.com/esri/contributing).


## Licensing

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at


   http://www.apache.org/licenses/LICENSE-2.0


Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


A copy of the license is available in the repository's [license.txt](https://github.com/swwendel/ParcelFabricInvestigator-python-addin/blob/master/license.txt) file.