'''
Title: Vehicle Routing Problem Map and Directions Automation.
Author: Stephanie Wendel - sawendel
Class: GIS 540 GIS Programming
Created: 4/15/2014
Upated: 4/24/2014
Version: 1.2

Description: A Vehicle Routing Problem (VRP) is used to find routes for multiple
stops and multiple vehicles to provide the best services at the lowest cost. For
example, a package delivery service, such as USPS, might use this to send your
package on the quickest route to be delivered. They have many starting
locations, stops, and trucks to fit into this equation to produce the best
service. The output in ArcGIS Desktop might be easy for a GIS Analyst to read
and understand, but the non-GIS users, such as drivers, need a simplified
version of the information to do their part. The goal of this tool is to
demonstrate how to generate PDF reports with maps and directions for a VRP
analysis. This solution also takes advantage of ArcGIS Online to store the PDFs
as well as the routes as feature services to use within web maps. The route
feature services can be viewed by the driver in phone applications such as
ArcGIS Online App to view their route and stay on track. This solution can be
utilized by any industry that needs to produce map and turn by turn directions
for its employees who need to travel to specific destinations, for example;
pizza delivery, City Inspectors going to do inspections locations, delivering
packages, etc. The point is to simplify the process of doing a VRP and to
produce a user friendly information for the employee to follow.
'''

# Import modules, requests module is non-standard and must be installed,
# see readme.txt
import arcpy
import os, sys, zipfile, traceback, time
import requests, socket, json
import VRPS
from datetime import date

def calculateNextDay():
    """Calculates the next date to use for the next day's orders"""
    today = date.today()
    dayofweek = today.isoweekday()
    added_days = {5:3, 6:2}
    if dayofweek in added_days:
        day_gap = added_days[dayofweek]
        while day_gap > 0:
            try:
                today = today.replace(day=today.day + 1)
                day_gap -= 1
            except ValueError:
                today = today.replace(month=today.month + 1, day=1)
                day_gap -= 1
    else:
        try:
            today = today.replace(day=today.day + 1)
        except ValueError:
            today = today.replace(month=today.month + 1, day=1)


    tom_format = today.strftime("%m_%d_%Y")
    return tom_format

# Environmental Variables
arcpy.env.overwriteOutput = True

# User Parameters and variable setup
ND = arcpy.GetParameterAsText(0)
time_impedance = arcpy.GetParameterAsText(1)
timeUnits = arcpy.GetParameterAsText(2)
inspection_orders = arcpy.GetParameterAsText(3)
depots = arcpy.GetParameterAsText(4)
routestable = arcpy.GetParameterAsText(5)
outputfolder = arcpy.GetParameterAsText(6)
templatemap = arcpy.GetParameterAsText(7)
username = arcpy.GetParameterAsText(8)
password = arcpy.GetParameterAsText(9)

# Generated inital variables
output_lyr = os.path.join(outputfolder, "vpr_layer.lyr")
mxd = arcpy.mapping.MapDocument(templatemap)
df = arcpy.mapping.ListDataFrames(mxd)[0]
directions = os.path.join(outputfolder, "directions.txt")
date = calculateNextDay()

# Setup AGOL access
hostname = "http://" + socket.getfqdn()

try:
    token_params ={'username': username,
                   'password': password,
                   'referer': hostname,
                   'f':'json'}
    token_response= requests.post("https://www.arcgis.com/sharing/generateToken",\
                            params=token_params)
    token_status = json.loads(token_response.text)
    token = token_status['token']
    arcpy.AddMessage("\nToken generated for AGOL.")
except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    msg = "Traceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    try:
        token_status
        if 'error' in token_status:
            code = token_status['error']['code']
            msg = token_status['error']['message']
            details = token_status['error']['details'][0]
            arcpy.AddError("Failed to generate token.")
            arcpy.AddError("Error {0}: {1} {2}".format(code, msg, details))
            print "Error {0}: {1} {2}".format(code, msg, details)
            sys.exit()
    except:
        arcpy.AddError("Failed to generate token.")
        arcpy.AddError(msg)
        print msg
    sys.exit()


# Check out Network Analyst extension
try:
    arcpy.CheckOutExtension("Network")
    arcpy.AddMessage("Network Analyst license checked out.")

except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    msg = "Traceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    arcpy.AddError("Unable to checkout Network Analyst License.")
    arcpy.AddError(msg)
    sys.exit()


# Begin Script processing
# VPR processing
try:
    # VRP layer creation and variable assignments
    arcpy.AddMessage("Starting Vehicle Routing Problem Analysis...")
    vprLayer = arcpy.na.MakeVehicleRoutingProblemLayer(ND, "vprLayer", \
                                time_impedance, time_units=timeUnits, \
                                output_path_shape="TRUE_LINES_WITHOUT_MEASURES")
    vprLayer = vprLayer.getOutput(0)

    subLayerNames = arcpy.na.GetNAClassNames(vprLayer)
    ordersLayerName = subLayerNames["Orders"]
    depotsLayerName = subLayerNames["Depots"]
    routesLayerName = subLayerNames["Routes"]

    # Add Orders
    arcpy.AddMessage("\tAdding Orders...")
    arcpy.na.AddLocations(vprLayer, ordersLayerName, inspection_orders)

    # Add Depots
    arcpy.AddMessage("\tAdding Depots...")
    arcpy.na.AddLocations(vprLayer, depotsLayerName, depots)

    # Add Route Table information
    arcpy.AddMessage("\tAdding Route Requirements...")
    arcpy.na.AddLocations(vprLayer, routesLayerName, routestable)

    # Solve for setup
    arcpy.AddMessage("\tSolving VRP...")
    arcpy.na.Solve(vprLayer)
    arcpy.AddMessage("VRP solved.")

    # Saving layer file and directions
    arcpy.SaveToLayerFile_management(vprLayer, output_lyr,"Relative")
    layer_reference = arcpy.mapping.Layer(output_lyr)
    arcpy.mapping.AddLayer(df, layer_reference, "TOP")
    arcpy.AddMessage("Template Map updated with new routes.")
    arcpy.Directions_na(vprLayer, "TEXT", directions, "MILES", "REPORT_TIME")
    arcpy.AddMessage("Directions saved.")

except arcpy.ExecuteError:
    msgs = arcpy.GetMessages(2)
    arcpy.AddError("An error occurred during processing:\n")
    arcpy.AddError(msgs)
    arcpy.AddError("\nPYou may need to check that your orders, depots, and \
                    routes are formated correctly.")

# Make RouteDirections object to pull direction information off of it
d = VRPS.RouteDirection(directions)

# update sublayers name reference
ordersLayer = arcpy.mapping.ListLayers(mxd, "Orders")[0]
depotsLayer = arcpy.mapping.ListLayers(mxd, "Depots")[0]
routesLayer = arcpy.mapping.ListLayers(mxd, "Routes")[0]


# Start mapbook and upload processing for each inspector
arcpy.AddMessage("Starting Mapbook processing...")
routesCursor = arcpy.da.SearchCursor(routestable, ["Name"])
routebookcollection = []
for inspector_row in routesCursor:
    Name = inspector_row[0]
    # Create empty Route book PDF
    arcpy.AddMessage("\tStarting {}'s mapbook...".format(Name))
    pdf_path = os.path.join(outputfolder, "{0}_RouteBook_{1}.pdf".format(Name, date))
    pdf = arcpy.mapping.PDFDocumentCreate(pdf_path)
    routebookcollection.append(pdf_path)
    # select individual inspector orders
    arcpy.SelectLayerByAttribute_management(depotsLayer, "NEW_SELECTION",\
            "Name = 'Assessors Office'")
    arcpy.SelectLayerByAttribute_management(ordersLayer, "NEW_SELECTION",\
            "RouteName = '{}'".format(Name))
    count = int(arcpy.GetCount_management(ordersLayer).getOutput(0))
    sequence_num = 2
    # Create a temporary folder in the output to build order pages
    outputfolder_temp = os.path.join(outputfolder, Name + "_temp")
    if arcpy.Exists(outputfolder_temp):
        arcpy.Delete_management(outputfolder_temp)
    os.makedirs(outputfolder_temp)
    # start page build
    while sequence_num <= (count + 1):
        if sequence_num == 2:
            arcpy.SelectLayerByAttribute_management(ordersLayer, \
                    "NEW_SELECTION", \
                    "Sequence = 2 AND RouteName = '{0}'".format(Name))
        else:
            arcpy.SelectLayerByAttribute_management(depotsLayer, \
                        "CLEAR_SELECTION")
            arcpy.SelectLayerByAttribute_management(ordersLayer, \
                "NEW_SELECTION", \
                "(Sequence = {0} OR Sequence = {1}) AND RouteName = '{2}'".format(\
                sequence_num, (sequence_num - 1), Name))
        df.zoomToSelectedFeatures()
        df.scale = df.scale + 2000
        # Find directions for inspector for select order and update map
        d.findStringPositions(Name)
        dic = d.seekLines()
        DirecttextElement = arcpy.mapping.ListLayoutElements(mxd, \
                         "TEXT_ELEMENT", "directions")[0]
        DirecttextElement.text = dic[(sequence_num - 1)]
        DirecttextElement.elementWidth = 3.25
        InspectTexttElement = arcpy.mapping.ListLayoutElements(mxd, \
                         "TEXT_ELEMENT", "inspection")[0]
        ordersCursor = arcpy.da.SearchCursor(ordersLayer, ["Name"])
        for row in ordersCursor:
            InspectTexttElement.text = row[0]
        page_name = os.path.join(outputfolder_temp, "{0}_{1}.pdf".format(Name,\
                                 sequence_num))
        # Export map and apped it to main route book pdf
        arcpy.mapping.ExportToPDF(mxd, page_name, "PAGE_LAYOUT")
        pdf.appendPages(page_name)
        sequence_num += 1
    pdf.saveAndClose()
    arcpy.Delete_management(outputfolder_temp)
    arcpy.AddMessage("\t{}'s Mapbook created.".format(Name))

    # upload routes to Agol and publish
    arcpy.AddMessage("\tStarting upload of Route and Orders shapefiles...")
    upload_routes = VRPS.uploadPublish(Name, date, outputfolder, \
                    routesLayer, "Name = '{}'".format(Name), username, token)
    upload_orders = VRPS.uploadPublish(Name, date, outputfolder, \
                    ordersLayer, "RouteName = '{}'".format(Name), username, token)
    if upload_orders != None and upload_routes != []:
        VRPS.makeWebmap(Name, date, upload_routes, upload_orders, username, token)
    arcpy.AddMessage("\tFinsihed processing {}'s pdf and webmap.\n".format(Name))


# Upload PDF to ArcGIS Online and share them with the organization
arcpy.AddMessage("Starting PDF upload process...")
output_pdf_dict = {}
for routebook in routebookcollection:
    upload_pdf_dict = VRPS.uploadPDF(routebook, username, token)
    output_pdf_dict.update(upload_pdf_dict)
VRPS.sharePDFs(output_pdf_dict, username, token)

# final cleanup
del d, inspector_row, routesCursor, mxd, df, vprLayer, ordersLayer
del routesLayer, depotsLayer

arcpy.CheckInExtension('Network')

arcpy.AddMessage("Processing Complete!")