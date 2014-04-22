'''
Title: VPRS
Author: Stephanie Wendel - sawendel
Class: GIS 540 GIS Programming
Created: 4/15/2014
Upated: 4/24/2014
Version: 1.2

Description: This contains the class and functions necessary for the VRP
solution. It must be imported into the script in order to run the solution.
'''
import json, zipfile, requests, arcpy, traceback, os, sys, time


# reusable classes and functions
class RouteDirection:
    """Defines a RouteDirections Object to gather key information about
    directions that is read from the generated directions text file."""
    def __init__(self, Directions_file):
        """Sets up the inital properties of the RouteDirections Object"""
        self.lines = None
        self.start = None
        self.end = None
        self._setup(Directions_file)

    def _setup(self, Directions_file):
        """Private function that reads the lines from the file and stores the
        contents in the lines property of the object."""
        read = open(Directions_file, "r")
        self.lines = read.readlines()
        read.close()

    def findStringPositions(self, name):
        """Finds the starting and end positions of the directions for each route
        (or route name) within the directions file. The values are set to the
        properties of the object."""
        start = "Begin route {}".format(name)
        end = "End of route {}".format(name)
        linecount = 0
        for line in self.lines:
            if start in line:
                self.start = linecount
                linecount += 1
            elif end in line:
                self.end = linecount
                linecount += 1
            else:
                linecount +=1
        return [self.start, self.end]

    def seekLines(self):
        """Reads the lines between the starting position and the end position
        and formats them to be used in the map document as a text element."""
        lineDict = {}
        if self.start != None or self.end != None:
            count = self.start + 2
            Groupkey = 1
            value = ""
            while count <= self.end:
                line = self.lines[count]
                if "Arrive at" in line:
                    value += line
                    count += 1
                    value += self.lines[count]
                    count += 1
                    value += self.lines[count]
                    lineDict[Groupkey] = value
                    Groupkey += 1
                    value = ""
                else:
                    value += line
                    count += 1
            return lineDict



def uploadPublish(routeid, date, folder, layer, where, username, token):
    """Prepares the data for upload to ArcGIS online by doing a selection for
    the input data, making a shapefile, zipping the shapefile, adding it to
    ArcGIS online, and publishing the data"""
    file_name = "{0}_{1}_{2}".format(routeid, layer.name, date)
    zip_file = os.path.join(folder, file_name+ ".zip")
    arcpy.env.workspace = folder
    arcpy.SelectLayerByAttribute_management(layer, "NEW_SELECTION", where)
    arcpy.CopyFeatures_management(layer, file_name +".shp")

    # create a zip file of the shapefile to upload
    zf = zipfile.ZipFile(zip_file, "w")
    for shpfile_part in arcpy.ListFiles(file_name+"*"):
        if shpfile_part != file_name + ".zip":
            zf.write(os.path.join(folder, shpfile_part), shpfile_part, \
                                zipfile.ZIP_DEFLATED)
    zf.close()

    # Upload zip file
    try:
        addItem_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/addItem".format(username)
        addItem_params = {'title': "{}".format(file_name), "type": "Shapefile",
                  'f': 'json', 'token':token}
        addItem_filesup = {'file':open(zip_file, 'rb')}
        addItem_response = requests.post(addItem_url, params=addItem_params, files=addItem_filesup)
        addItem_status = json.loads(addItem_response.text)

        # if there is an error uploading zip file return messages
        if 'error' in addItem_status:
            code = addItem_status['error']['code']
            msg = addItem_status['error']['message']
            arcpy.AddWarning('Unable to upload {0}.zip. Error {1}: {2}'.format(file_name, code, msg))
            arcpy.AddWarning('Manually upload zip file.')

        # if upload succeeds being publishing of zip file
        elif addItem_status['success'] == True:
            itemid = addItem_status['id']
            arcpy.AddMessage("\t\tUploaded {} to AGOL.".format(layer.name))

            publish_zip_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/publish".format(username)
            publishParams = json.dumps({'name': file_name})
            publish_zip_params = {'itemID': itemid,
                              'filetype':'shapefile',
                              'f': 'json',
                              'publishParameters': publishParams,
                              'token': token}
            publish_zip_response = requests.post(publish_zip_url, \
                                                 params=publish_zip_params)
            publish_zip_status = json.loads(publish_zip_response.text)

            # if there is an error publishing return messages
            if 'error' in publish_zip_status:
                code = publish_zip_status['error']['code']
                msg = publish_zip_status['error']['message']
                arcpy.AddError('Unable to publish {0}.zip. Error {1}: {2}'.format(file_name, code, msg))
                arcpy.AddError('Manually publish zip file.')

            # if publishing succeeds capture service url and id to return
            else:
                arcpy.AddMessage('\t\tPublished {} as feature service.'.format(layer.name))
                services = publish_zip_status['services']
                for service in services:
                    serviceurl = service['serviceurl'] + "/0"
                    serviceItemId = service['serviceItemId']
                    service_share_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/items/{1}/share".format(username,serviceItemId)
                    service_share_params = {'everyone': 'false', 'org':'true', 'f':'json', 'token':token}
                    service_share_response = requests.post(service_share_url, params=service_share_params)

                return [file_name, serviceurl, serviceItemId]
        else:
            arcpy.AddWarning(addItem_status)
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        tmsg = "Traceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        arcpy.AddError("Unable to upload and/or publish {}.zip. Manually upload and publish.".format(file_name))
        arcpy.AddError(tmsg)


def makeWebmap(name, date,  route_service, order_service, username, token):
    """ Creates a webmap with each inspector's order locations and routes. Input
    for route_service and order_service must be a list containing title and
    service url in that order."""
    webmap_name = "{0}'s Inspections for {1}".format(name, date.replace("_", "-"))
    route_service_title = route_service[0]
    route_service_url = route_service[1]
    route_serviceItemID = route_service[2]
    order_service_title = order_service[0]
    order_service_url = order_service[1]
    bookmark_name = "{} Routes".format(name)

    # Try to create webmap
    try:
        # Get extent information to make a bookmark of the route area
##        service_data_url ="http://www.arcgis.com/sharing/rest/content/items/{}".format(route_serviceItemID)
##        service_data_params =  {'f': 'json', 'token': token}
##        service_data_response = requests.get(service_data_url, params=service_data_params)
##        service_data_extent =  json.loads(service_data_response.text)['extent']
##        extent = {'xmax' : service_data_extent[1][0], 'xmin': service_data_extent[0][0], 'ymax': service_data_extent[1][1], 'ymin':service_data_extent[0][1]}
        webmap_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/addItem".format(username)
        text = json.dumps({'operationalLayers': [{'url': order_service_url,
            'visibility':'true',"opacity":1, 'title': order_service_title},
            {'url': route_service_url,'visibility':'true',"opacity":1,
            'title': route_service_title}],
            "baseMap":
            {'baseMapLayers':[{'id':"World_Imagery_1068",
            'opacity':1,'visibility':'true',
            'url':'http://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'}]
             ,'title':'Imagery'},'version':'1.9.1'})
        #'bookmarks':[{'extent': service_data_extent, 'name': webmap_name}]
        webmap_params = {'title': webmap_name, 'type':'Web Map', 'text':text,
                         'f': 'json','token': token}
        webmap_response = requests.post(webmap_url, params=webmap_params)
        webmap_status = json.loads(webmap_response.text)

        # check for errors
        if 'error' in webmap_status:
            code = webmap_status['error']['code']
            msg = webmap_status['error']['message']
            details = webmap_status['error']['details']
            arcpy.AddError('\tUnable to add webmap {0}. Error {1}: {2}, {3}'.format(file_name, code, msg, details))
            arcpy.AddError('\tManually create webmap.')

        # Share the webmap with the organization
        elif webmap_status['success'] == True:
            arcpy.AddMessage('\t{} webmap added to AGOL.'.format(webmap_name))
            webmap_id =  webmap_status['id']
            share_webmap_url ="http://www.arcgis.com/sharing/rest/content/users/{0}/items/{1}/share".format(username,webmap_id)
            share_webmap_params = {'everyone': 'false', 'org':'true', 'f':'json', 'token':token}
            share_webmap_response = requests.post(share_webmap_url, params=share_webmap_params)
            share_webmap_status = json.loads(share_webmap_response.text)

            # Check for errors when sharing webmap
            if 'error' in share_webmap_status:
                code = share_webmap_status['error']['code']
                msg = share_webmap_status['error']['message']
                arcpy.AddError('\tUnable to share webmap {0}. Error {1}: {2}'.format(file_name, code, msg))
                arcpy.AddError('\tManually share webmap.')

            elif 'itemId' in share_webmap_status:
                arcpy.AddMessage("\t{} webmap has been shared.".format(webmap_name))
            else:
                arcpy.AddWarning(share_webmap_status)
        else:
            arcpy.AddWarning(webmap_status)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        tmsg = "Traceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        arcpy.AddError("Unable to create {} webmap. Manually finish setup.".format(webmap_name))
        arcpy.AddError(tmsg)



def uploadPDF(mapbook, username, token):
    """Uploads a pdf to ArcGIS Online and shares the file with the
    organization"""
    bookname = os.path.basename(mapbook)
    upload_pdf_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/addItem".format(username)
    upload_pdf_params = {'title':bookname, 'type':'PDF', 'f': 'json','token': token}
    pdf_filesup = {'file':open(mapbook, 'rb')}
    try:
        upload_pdf_request = requests.post(upload_pdf_url,
                                    params=upload_pdf_params, files=pdf_filesup)
        upload_pdf_status = json.loads(upload_pdf_request.text)
        if 'error' in upload_pdf_status:
            code = upload_pdf_status['error']['code']
            msg = upload_pdf_status['error']['message']
            arcpy.AddError('\tUnable to upload PDF. Error {0}: {1}'.format(code, msg))
            arcpy.AddError('\tManually upload PDF files.')

        elif upload_pdf_status['success'] == True:
            arcpy.AddMessage("\tUploaded {} PDF to AGOL.".format(bookname))
            pdf_id = upload_pdf_status['id']
            return {pdf_id: bookname}
        else:
            arcpy.AddWarning(upload_pdf_status)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        tmsg = "Traceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        arcpy.AddError("Failed to upload PDF.")
        arcpy.AddError(tmsg)



def sharePDFs(itemsDictionary, username, token):
    """Uses a dictionary formated as {itemid; pdfname} to share pdfs on AGOL"""
    string_items_list = ""
    for item in itemsDictionary:
        string_items_list += item +  ","
    string_items_list[:-1]
    share_pdf_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/shareItems".format(username)
    share_pdf_params = {'everyone': 'false', 'org':'true', 'items': string_items_list, 'f':'json', 'token':token}
    try:
        share_pdf_response = requests.post(share_pdf_url, params=share_pdf_params)
        share_pdf_status = json.loads(share_pdf_response.text)
        if 'results' in share_pdf_status:
            share_pdf_results = share_pdf_status['results']
            if share_pdf_results != []:
                for result in share_pdf_results:
                    pdf_name  = itemsDictionary[result['itemId']]
                    if result['success'] == True:
                        arcpy.AddMessage("\tShared {} on AGOL.".format(pdf_name))
                        print "\tShared {} on AGOL.".format(pdf_name)

                    else:
                        if 'error' in result:
                            code = result['error']['code']
                            msg = result['error']['message']
                            arcpy.AddError("\tUnable to share {0}. Error {1}: {2}".format(pdf_name, code, msg))
                            arcpy.AddError("\tManually share PDF file.")

                        else:
                            arcpy.AddWarning("\tUnable to share {}.".format(pdf_name))
                            arcpy.AddWarning("\tManually share PDF file.")
            else:
                arcpy.AddWarning("\tUnable to share PDFs.'")
                arcpy.AddWarning("\tManually share PDF files.")
        else:
            arcpy.AddWarning(share_pdf_status)
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        tmsg = "Traceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        arcpy.AddError("Unable to share PDF. Manually Share.")
        arcpy.AddError(tmsg)



if __name__ == '__main__':
    main()