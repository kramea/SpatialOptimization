#Name: Kalaivani Ramea Kubendran
#Student ID: 996718312

#Final Project: Soft-linking the electricity generation sector between TIMES and GIS to generate renewable energy power plants.
# TIMES is an energy-economic-environment model that predicts the energy choices given the constraints
# California TIMES model consists of two scenarios: Base case scenario (where no constraints are implemented)..
#...and Deep Greenhouse Gas (GHG) case scenario (where carbon constraints are implemented) to meet the 2050 GHG reduction goal (1990 levels of GHG)


#import the modules
import os, arcpy, shutil, sys
import arcpy.mapping

#Get the user input from arctoolboxGUI
file = arcpy.GetParameterAsText(0) #input text file
inputYear = arcpy.GetParameterAsText(1) #string
yeartest = eval(inputYear)

#Give the path name where the relevant shapefiles are saved
datapath = arcpy.GetParameterAsText(2) #data folder path
datapath = datapath+"\\"
arcpy.env.workspace=datapath
arcpy.env.overwriteOutput=True

path = arcpy.GetParameterAsText(3) #new shapefile path
temp = datapath+"temp\\" #Temporary folder to save all the 'in-between' files
newpath = path+"\\NewShapefiles\\"
if not os.path.isdir(temp):
    os.mkdir(temp)
    #Create a temporary folder to save the files that are to be deleted later
else:
    shutil.rmtree(temp)
    os.mkdir(temp)
if not os.path.isdir(newpath):
    os.mkdir(newpath)
else:
    shutil.rmtree(newpath)
    os.mkdir(newpath)

try:
    
    #Read the contents of the model output
    f = open(file)
    content = f.readlines()
    f.close()


    #Get the header from the text file
    header = content[0]
    header = header.split(',')

    #This assigns the column values for the variables 'scenario', 'process' and 'year' that will be used later for analysis
    for n in range(len(header)):
        if header[n] == "Scenario":
            scenario = n
        if header[n] == "Process":
            process = n
        if header[n] == inputYear:
            year = n

    #Now, the header is removed to retain the contents alone
    content.pop(0)

    for i in range(len(content)):
        content[i] = content[i][:-1] #this removes the newline from the content
        content[i] = content[i].split(',')

    #The following loop will assign the energy demand values to the variables
    for j in range(len(content)):
        data = content[j]
        scen = data[scenario]
        if data[process] == "NEWBIO":
            biomass = eval(data[year])
        if data[process] == "NEWGEO":
            geothermal = eval(data[year])
        if data[process] == "NEWSOL":
            solar = eval(data[year])
        if data[process] == "NEWWIND":
            wind = eval(data[year])

    f = open(newpath+"summary.txt", 'w')
    title = "Spatial Optimization of Renewable power plant locations from California TIMES model"
    f.write(title+'\n')
    f.write("="*len(title))
    f.write('\n\n\n')
    f.write('+'+'-'*14+'+'+'-'*24+'+'+'\n')
    f.write("|"+"Scenario      "+"|"+scen+" "*(24-len(scen))+"|"+'\n')
    f.write("|"+"-"*14+"+"+"-"*24+"|"+'\n')
    f.write("|"+"Year          "+"|"+inputYear+" "*(24-len(inputYear))+"|"+'\n')
    f.write('+'+'-'*14+'+'+'-'*24+'+'+'\n')
    f.write('\n\n\n')
    subhead = " "*5+"The renewable energy power plant locations"+" "*5
    f.write("+"+"-"*len(subhead)+"+"+'\n')
    f.write("|"+subhead+"|"+'\n')
    f.write("+"+"-"*len(subhead)+"+"+'\n')
    f.write("|"+"Attribute"+" "*25+"|"+" "+"Number"+" "*10+"|"+'\n')
    f.write("+"+"-"*34+"+"+"-"*17+"+"+'\n')
    f.close()


    """************************************************************************************************************************************************"""
    #Function 1: Pre-defined function to filter areas of wildlife, culturally sensitive areas, military lands, existing power plant locations and avoids future power plant location conflicts
    def filter_areas(xlayer, xname):
        
        arcpy.SelectLayerByLocation_management(xlayer,"INTERSECT", datapath+"Potential_Wilderness.shp", "", "ADD_TO_SELECTION")
        arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", datapath+"Military_Lands.shp", "", "ADD_TO_SELECTION")
        arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", datapath+"Culture.shp", "", "ADD_TO_SELECTION")
        arcpy.SelectLayerByLocation_management(xlayer,"INTERSECT", datapath+"Solar_Projects.shp", "", "ADD_TO_SELECTION")
        arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", datapath+"Wind_Projects.shp", "", "ADD_TO_SELECTION")
        arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", datapath+"Biomass_projects.shp", "", "ADD_TO_SELECTION")
        arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", datapath+"Geothermal_projects.shp", "", "ADD_TO_SELECTION")

        if xname == "wind":
            
            arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", newpath+"New_Solar.shp", "", "ADD_TO_SELECTION")

        elif xname == "biomass":

            arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", newpath+"New_Solar.shp", "", "ADD_TO_SELECTION")
            arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", newpath+"New_Wind.shp", "", "ADD_TO_SELECTION")

        elif xname == "geothermal":
            
            arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", newpath+"New_Solar.shp", "", "ADD_TO_SELECTION")
            arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", newpath+"New_Wind.shp", "", "ADD_TO_SELECTION")
            arcpy.SelectLayerByLocation_management(xlayer, "INTERSECT", newpath+"New_Biomass.shp", "", "ADD_TO_SELECTION")

        arcpy.DeleteFeatures_management(xlayer)        

    """************************************************************************************************************************************************"""
    #Function 2: A pre-defined function to generate new locations based on mutipliers calculated from formulae, and calculates power generation for each location.
    def location_generation(name, power, xcursor, xnewcursor, xshapename, multiplier):
        location = 0
        energy = 0
        newpoint = arcpy.Point()
        for row in xcursor:
            if name == "solar":
                constant = (row.GHIANN)*multiplier
            if name == "wind":
                constant = (row.speed)*multiplier
            if name == "geothermal" or name == "biomass":
                constant = multiplier
            if energy < power:
                feat = row.getValue(xshapename)
                point = feat.centroid
                newpoint.X = point.X
                newpoint.Y = point.Y
                xnewrow = xnewcursor.newRow()
                xnewrow.shape = newpoint
                if name == "solar":
                    xnewrow.GHIANN = row.GHIANN
                if name == "wind":
                    xnewrow.speed = row.speed
                if name == "geothermal":
                    xnewrow.CLASS = row.CLASS
                if name == "biomass":
                    xnewrow.Total = row.Total
                xnewcursor.insertRow(xnewrow)
                energy = energy + constant
                location = location + 1
                del xnewrow
            else:
                break
        del row
        return location        

    """************************************************************************************************************************************************"""
    #This uses arcpy.mapping module to create maps in CURRENT arcmap document and uses the template in the 'Dataset' folder to update legend, title and other attributes to save as PDF
    def create_map(xmxd):
        mxd = arcpy.mapping.MapDocument(xmxd)
        df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
        for lyr in arcpy.mapping.ListLayers(mxd, "", df):
            arcpy.mapping.RemoveLayer(df, lyr)
        arcpy.MakeFeatureLayer_management(datapath+"CA_County.shp", "County")
        arcpy.MakeFeatureLayer_management(newpath+"New_Solar.shp","Solar")
        arcpy.MakeFeatureLayer_management(newpath+"New_Wind.shp", "Wind")
        arcpy.MakeFeatureLayer_management(newpath+"New_Biomass.shp", "Biomass")
        arcpy.MakeFeatureLayer_management(newpath+"New_Geothermal.shp", "Geothermal")
        countylyr = arcpy.mapping.Layer("County")
        solarlyr = arcpy.mapping.Layer("Solar")
        windlyr = arcpy.mapping.Layer("Wind")
        biolyr = arcpy.mapping.Layer("Biomass")
        geolyr = arcpy.mapping.Layer("Geothermal")
        if xmxd != "CURRENT":
            legend = arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT", "Legend")[0]
            legend.autoAdd = True
            elm = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT")
            elm[0].text = inputYear
            elm[1].text = scen
        arcpy.mapping.AddLayer(df,countylyr)    
        arcpy.mapping.AddLayer(df,solarlyr)
        arcpy.mapping.AddLayer(df,windlyr)
        arcpy.mapping.AddLayer(df,biolyr)
        arcpy.mapping.AddLayer(df,geolyr)
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        if xmxd != "CURRENT":
            legend.adjustColumnCount(1)
            mxd.save()
            arcpy.mapping.ExportToPDF(mxd, newpath+scen+"_"+inputYear+".pdf")
        del mxd
    """************************************************************************************************************************************************"""
    #Solar Energy Locations

    #The annual average solar radiation map is given and the annual average precipitation maps are used for this analysis

    arcpy.AddMessage("Starting solar power plant analysis....")    

    #As the first step, the two shapefiles are merged, using identity analysis
    arcpy.Identity_analysis(datapath+"CASolar.shp",datapath+"Rainfall.shp", temp+"CASolRain.shp")

    #Make a temporary layer for selection analysis
    arcpy.MakeFeatureLayer_management(temp+"CASolRain.shp", temp+"CASol_lyr")

    #Filter the combined shapefile to remove the locations of existing solar projects, culturally sensitive lands, military lands, and potential wilderness
    filter_areas(temp+"CASol_lyr", "solar")

    #The solar file is sorted on high annual average solar radiation, followed by low annual average rainfall
    arcpy.Sort_management(temp+"CASol_lyr", temp+"CASolarSorted.shp", [[ "GHIANN", "DESCENDING"], ["RANGE", "ASCENDING"]])

    arcpy.Delete_management(temp+"CASol_lyr")
    arcpy.Delete_management(temp+"CASolRain.shp")

    #Solar power plant energy generation calculation:
    #Area: Each power plant is assumed to be of 2000 acre size = 8.09X10^6 sq. m 
    #Efficiency: The conversion efficiency from insolation to electricity is assumed to be 20%
    #The annual electricity generated in GWh = [(Annual GHI in kWh/sq.m-day) * Area (sq.m) * Efficiency * 365 days]/1000
    #The constant multiplier is approx. 0.6

    #Create a shapefile for new solar locations
    arcpy.CreateFeatureclass_management(newpath, "New_Solar.shp", "POINT", "", "DISABLED", "DISABLED", temp+"CASolarSorted.shp")
    arcpy.AddField_management(newpath+"New_Solar.shp", "GHIANN", "LONG")
    soldesc = arcpy.Describe(newpath+"New_Solar.shp")
    solshapename = soldesc.shapeFieldName

    #create cursors for existing and new shapefiles
    newsolcur = arcpy.InsertCursor(newpath+"New_Solar.shp")
    exsolcur = arcpy.SearchCursor(temp+"CASolarSorted.shp")
    solconst = 0.6 #from the comments above

    arcpy.AddMessage("Generating new locations for solar power plants..")                     

    solar_loc = location_generation("solar", solar, exsolcur, newsolcur, solshapename, solconst)
    del exsolcur
    del newsolcur

    #write summary file    
    f = open(newpath+"summary.txt", 'a')
    solname = "Solar Power Plants"
    f.write("|"+solname+" "*(34-len(solname))+"|"+" "+str(solar_loc)+" "*(16-len(str(solar_loc)))+"|"+'\n')
    f.close()

    """************************************************************************************************************************************************"""

    #WindEnergy Locations

    arcpy.AddMessage("Starting wind power plant analysis...")                     

    #Proximity to transmission lines is very important for biomass plants--20 mile buffer is created for transmission lines
    arcpy.Buffer_analysis(datapath+"Transmission.shp", temp+"transbuf.shp", "20 miles")

    #Clip the wind contour shapefile with transmission buffer
    arcpy.Clip_analysis(datapath+"CAwind.shp", temp+"transbuf.shp", temp+"clippedwind.shp")

    #Make a temporary layer for selection analysis
    arcpy.MakeFeatureLayer_management(temp+"clippedwind.shp", temp+"CAwind_lyr")
    
    #Filter the combined shapefile to remove the locations of existing solar projects, culturally sensitive lands, military lands, and potential wilderness
    filter_areas(temp+"CAwind_lyr", "wind")

    #The wind file is sorted on high annual average wind speed, followed by high altitude
    arcpy.Sort_management(temp+"CAwind_lyr", temp+"sortedwind.shp", [[ "GRIDCODE", "DESCENDING"], ["RANGE_CODE", "ASCENDING"]])

    arcpy.Delete_management(temp+"CAwind_lyr")
    arcpy.Delete_management(temp+"clippedwind.shp")

    #Wind power plant energy generation calculation:
    #Area: Each power plant is assumed to be of 1000 acre size = 4.05X10^6 sq. m 
    #With an average windspeed of 7 m/s, a turbine will produce 1100 kwh per sq.m per year (assuming 20 to 40% efficiency)
    #Electricity generated (in Gwh) = ((wind speed in m/s) / 7 m/s)* 1100 * (4.05X10^6 /1000000)
    #The annual electricity generated in GWh = Windspeed (in m/s) X 636.43
    #The constant multiplier is approx. 636.43

    #We need to add windspeed as a field to the sorted shapefile
    arcpy.AddField_management(temp+"sortedwind.shp", "speed", "DOUBLE")

    arcpy.AddMessage("Calculating wind speeds for different grids...")                     

    #Need to update the shapefile with windspeeds (in m/s) based on GRIDCODE from NREL
    windcur = arcpy.UpdateCursor(temp+"sortedwind.shp")
    for row in windcur:
        if row.GRIDCODE == 7:
            row.speed = 9
        if row.GRIDCODE == 6:
            row.speed = 8.4
        if row.GRIDCODE == 5:
            row.speed = 7.7
        if row.GRIDCODE == 4:
            row.speed = 7.3
        if row.GRIDCODE == 3:
            row.speed = 6.7
        if row.GRIDCODE == 2:
            row.speed = 6
        if row.GRIDCODE == 1:
            row.speed = 2.8
        windcur.updateRow(row)
    del windcur
    del row

    #Create a shapefile for new wind locations
    arcpy.CreateFeatureclass_management(newpath, "New_Wind.shp", "POINT", "", "DISABLED", "DISABLED", temp+"sortedwind.shp")
    arcpy.AddField_management(newpath+"New_Wind.shp", "speed", "LONG")
    
    #Create a point object for inserting features
    windesc = arcpy.Describe(newpath+"New_Wind.shp")
    winshapename = windesc.shapeFieldName

    #create cursors for existing and new shapefiles
    newwincur = arcpy.InsertCursor(newpath+"New_Wind.shp")
    exwincur = arcpy.SearchCursor(temp+"sortedwind.shp")
    winconst = 636.43 #from the comments above

    arcpy.AddMessage("Creating new locations for wind power plants...")
    wind_loc = location_generation("wind", wind, exwincur, newwincur, winshapename, winconst)

    del exwincur
    del newwincur

    f = open(newpath+"summary.txt", 'a')
    winname = "Wind power plants"
    f.write("|"+winname+" "*(34-len(winname))+"|"+" "+str(wind_loc)+" "*(16-len(str(wind_loc)))+"|"+'\n')
    f.close()

    """************************************************************************************************************************************************"""

    #Biomass Power Plants
    #Average power generated from a biomass power plant = 400 GWh

    arcpy.AddMessage("Starting biomass power plant analysis....")    

    #Proximity to transmission lines is very important for biomass plants--15 mile buffer is created for transmission lines
    arcpy.Buffer_analysis(datapath+"Transmission.shp", temp+"transbuf2.shp", "15 miles")

    #Clip the Biomass layer using the transmission buffer
    arcpy.Clip_analysis(datapath+"CABiomass.shp", temp+"transbuf2.shp", temp+"bioclipped.shp")

    #Make a layer for selection analysis
    arcpy.MakeFeatureLayer_management(temp+"bioclipped.shp", temp+"bio_lyr")

    filter_areas(temp+"bio_lyr", "biomass")

    #Sort the clipped biomass layer using the total biomass availability
    arcpy.Sort_management(temp+"bio_lyr", temp+"biosorted.shp", [["Total", "DESCENDING"]])

    arcpy.Delete_management(temp+"bio_lyr")
    arcpy.Delete_management(temp+"bioclipped.shp")

    #Create a shapefile for new biomass locations
    arcpy.CreateFeatureclass_management(newpath, "New_Biomass.shp", "POINT", "", "DISABLED", "DISABLED", temp+"biosorted.shp")
    arcpy.AddField_management(newpath+"New_Biomass.shp", "Total", "DOUBLE")

    biodesc = arcpy.Describe(newpath+"New_Biomass.shp")
    bioshapename = biodesc.shapeFieldName

    #create cursors for existing and new shapefiles
    newbiocur = arcpy.InsertCursor(newpath+"New_Biomass.shp")
    exbiocur = arcpy.SearchCursor(temp+"biosorted.shp")
    bioconst = 400 #from the comments above

    arcpy.AddMessage("Creating new biomass power plant locations...")    

    bio_loc = location_generation("biomass", biomass, exbiocur, newbiocur, bioshapename, bioconst)

    del exbiocur
    del newbiocur

    f = open(newpath+"summary.txt", 'a')
    bioname = "Biomass power plants"
    f.write("|"+bioname+" "*(34-len(bioname))+"|"+" "+str(bio_loc)+" "*(16-len(str(bio_loc)))+"|"+'\n')
    f.close()

    """************************************************************************************************************************************************"""
        
    #Geothermal Power Plants
    #Average power generated from a biomass power plant = 1920 GWh

    arcpy.AddMessage("Starting geothermal power plant analysis...")    

    #Clip the Geothermal layer using the transmission buffer
    arcpy.Clip_analysis(datapath+"CAGeothermal.shp", temp+"transbuf.shp", temp+"geoclipped.shp")

    #Create a buffer for CA-faults that have high slipping rate and clip out
    arcpy.Buffer_analysis(datapath+"CAfaults.shp", temp+"faultbuf.shp", "30 miles")

    arcpy.Clip_analysis(temp+"geoclipped.shp", temp+"faultbuf.shp", temp+"geoclipped2.shp")    
    

    #Make a temporary layer for selection analysis
    arcpy.MakeFeatureLayer_management(temp+"geoclipped2.shp", temp+"geo_lyr")
    
    #Filter the combined shapefile to remove the locations of existing solar projects, culturally sensitive lands, military lands, and potential wilderness
    filter_areas(temp+"geo_lyr", "geothermal")

    #Sort the clipped geothermal layer using the total biomass availability
    arcpy.Sort_management(temp+"geo_lyr", temp+"geosorted.shp", [["CLASS", "DESCENDING"]])

    arcpy.Delete_management(temp+"geo_lyr")
    arcpy.Delete_management(temp+"geoclipped.shp")

    #Create a shapefile for new geothermal locations
    arcpy.CreateFeatureclass_management(newpath, "New_Geothermal.shp", "POINT", "", "DISABLED", "DISABLED", temp+"geosorted.shp")
    arcpy.AddField_management(newpath+"New_Geothermal.shp", "CLASS", "LONG")

    geodesc = arcpy.Describe(newpath+"New_Geothermal.shp")
    geoshapename = geodesc.shapeFieldName

    #create cursors for existing and new shapefiles
    newgeocur = arcpy.InsertCursor(newpath+"New_Geothermal.shp")
    exgeocur = arcpy.SearchCursor(temp+"geosorted.shp")
    geoconst = 1920 #from the comments above

    arcpy.AddMessage("Creating geothermal power plant locations...")    

    geo_loc = location_generation("geothermal", geothermal, exgeocur, newgeocur, geoshapename, geoconst)
        
    del exgeocur
    del newgeocur

    arcpy.Delete_management(temp+"geosorted.shp")

    f = open(newpath+"summary.txt", 'a')
    geoname = "Geothermal power plants"
    f.write("|"+geoname+" "*(34-len(geoname))+"|"+" "+str(geo_loc)+" "*(16-len(str(geo_loc)))+"|"+'\n')
    f.write("+"+"-"*34+"+"+"-"*17+"+"+'\n')
    f.write('\n\n\n')
    f.close()

    """************************************************************************************************************************************************"""
    #Metadata about the shapefiles

    f = open(newpath+"summary.txt", 'a')
    f.write("*"*len(title)+'\n\n')
    f.write("Metadata:"+'\n')
    f.write("-"*len("Metadata:")+'\n\n')
    f.write("All the locations avoid military lands, culturally sensitive areas and wildlife preservation."+'\n\n')
    f.write("Solar Power"+'\n')
    f.write("------------"+'\n\n')
    f.write("The size of each solar power plant is 2000 acres"+'\n')
    f.write("...which is about 1 mile radius circle buffer around the point"+'\n')
    f.write("or 1.75 mile on each side of the square power plant"+'\n')
    f.write("The New_Solar shapefile shows the annual average solar radiation for each location(GHIANN)"+'\n')
    f.write("The power generated for each power plant is calculated from the location's annual average solar radiation, area of power plant, and efficiency."+'\n')
    f.write('\n\n')
    f.write("Wind Power"+'\n')
    f.write("------------"+'\n\n')
    f.write("The size of each solar power plant is 1000 acres"+'\n')
    f.write("...which is about 0.5 mile radius circle buffer around the point"+'\n')
    f.write("or 0.9 mile on each side of the square power plant"+'\n')
    f.write("The New_Wind shapefile shows the annual average wind speed (in m/s) for each location"+'\n')
    f.write("The power generated for each power plant is calculated from wind speed, average wind turbine power, and area of power plant."+'\n') 
    f.write('\n\n')
    f.write("Biomass Power"+'\n')
    f.write("------------"+'\n\n')
    f.write("The New_Biomass shapefile shows the annual biomass availability for each location."+'\n')
    f.write("The power plant locations are within 15 miles of transmission lines."+'\n')
    f.write('\n\n')
    f.write("Geothermal Power"+'\n')
    f.write("------------"+'\n\n')
    f.write("The New_Geothermal shapefile shows the geothermal favorability for each location."+'\n'+" [Classes 1 to 5, 5 being most favorable]"+'\n')
    f.write("The locations are within 20 miles of transmission lines."+'\n')
    f.write("The earthquake fault lines with slip rates > 5 mm/year are avoided."+'\n')
    f.write("The locations are at least 30 miles away from high-slip rate fault lines."+'\n')
    f.close()
    arcpy.AddMessage("Creating Summary Text file...")

    arcpy.AddMessage("Creating PDF document...")
    mapdoc = datapath+"proj.mxd"
    create_map(mapdoc) #Creates a map using the template from the 'Dataset' folder, and saves a PDF file
    create_map("CURRENT") #Adds new shapefiles to the current arcmap document

    arcpy.AddWarning("The tool successfully generated new locations for renewable energy power plants for the year "+inputYear+" for "+scen+".")
    arcpy.AddWarning("The output files are located at "+newpath)
    
    """************************************************************************************************************************************************"""

except:

    arcpy.AddError("Error in input data.")
    modyear = yeartest % 5
    if yeartest < 2010 or yeartest > 2050:
        arcpy.AddWarning("Year input is out of range.")
        arcpy.AddWarning("Rerun the tool with an appropriate year input.")
    elif modyear > 0:
        arcpy.AddWarning("Enter a year between 2010 to 2050 (in 5-year interval).")
        arcpy.AddWarning("Rerun the tool with an appropriate year input.")
    else:    
        arcpy.AddWarning("Exception occured. Check your input data files/folder path.")
    


        


        
