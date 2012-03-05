#!/usr/bin/python
#
# The tool looks at the folders and subfolders it finds to find *wrapper.log
# files. These were generated by the stitching wrapper and tell us what the
# source files of the stitched image are. Those source files will be opened
# to obtain their meta data which in turn is written to a file called
# original_metadata.txt in the folder where the *wrapper.log resides.
#
# ToDo: attach most of the metadata to the stitched image
#
# Synopsis: grabmetadata.py <folder_file> [<source_img_prefix>]

import os
import glob
import sys
from ij.plugin.filter import Info
from loci.plugins import LociImporter
from loci.plugins import BF
from loci.plugins.in import ImporterOptions

sourcePrefix = ""
folderFile = ""
nArgs = len(sys.argv)
if nArgs == 2:
    folderFile = sys.argv[1]
    print( "using no source file prefix" )
elif nArgs == 3:
    folderFile = sys.argv[1]
    sourcePrefix = sys.argv[2]
    print( "using source file prefix: " + sourcePrefix )
else:
    print( "usage: grabmetadata.py <folder_file> [<source_img_prefix>]" )
    sys.exit(1)

print( "using folder file: " + folderFile )

# Open info file with folders to look in
infoFiles = []
file = open( folderFile )
while 1:
    line = file.readline()
    if not line:
        break
    line = line.rstrip("\n")
    if not os.path.isdir(line):
        print( "not a dir: " + line )
        continue
    for currentFile in glob.glob( os.path.join(line, '*wrapper*.log')):
        infoFiles.append(currentFile)
file.close()

class MetaDataJob:
    def __init__(self, sourceLog, sourcePath, sourceImages, outputPath):
        self.log = sourceLog
        self.sourcePath = sourcePath
        self.sourceImages = sourceImages
        self.outputPath = outputPath
        self.outputData = ""
        self.numChannels = -1

def createJobs( wrapperFiles ):
    """ Look at wrapper log files
    """
    # define some markers to look for
    tilingXMLMarkerStart = "found tiling info XML ("
    tilingXMLMarkerEnd = "MATL_Mosaic.log), going to read it"
    tilingXMLMarker2Start = "did not find tiling info XML ("
    tilingXMLMarker2End = "MATL_Mosaic.log), making wild guess"
    sourceImageMarkerStart = "\tloading "

    metadataJobs = []
    for infoFile in wrapperFiles:
        print( infoFile )
        file = open(infoFile)
        # path of input file is output folder
        xmlPath = ""
        sourceImages = []
        while 1:
            line = file.readline()
            line = line[:len(line)-1]
            if not line:
                break
            # find folder of XML file
            posOne = line.find(tilingXMLMarkerStart)
            if posOne != -1:
                posTwo = line.find(tilingXMLMarkerEnd, posOne)
                posOne = posOne + len(tilingXMLMarkerStart)
                if posTwo == -1:
                    print( "\tNo XML: Couldn't find second marker" )
                    continue
                xmlPath = line[posOne:posTwo]
                print( "\tXML: " + xmlPath )
                continue
            else:
                posOne = line.find(tilingXMLMarker2Start)
                if posOne != -1:
                    posTwo = line.find(tilingXMLMarker2End, posOne)
                    posOne = posOne + len(tilingXMLMarker2Start)
                    if posTwo == -1:
                        print( "\tNo XML: Couldn't find second marker" )
                        continue
                    xmlPath = line[posOne:posTwo]
                    print( "\tXML: " + xmlPath )
                    continue
            # find source images
            posOne = line.find(sourceImageMarkerStart)
            if posOne != -1:
                sourceFile = line[posOne+len(sourceImageMarkerStart):]
                sourceImages.append( sourceFile )
        # show what we got:
        print( "\tSource files: " + ", ".join( sourceImages ) )
        # save the result
        outputDir = os.path.dirname(infoFile)
        metadataJobs.append( MetaDataJob( infoFile, xmlPath, sourceImages, outputDir ) )
    return metadataJobs

def checkJobs( jobs ):
    nFails = 0
    for j in jobs:
        if j.sourcePath == "" or len(j.sourceImages) == 0:
            nFails = nFails + 1
            print( "Warning: There is a problem with content of " + j.log )
    if nFails == 0:
        print( "All jobs look fine, no errors reported." )

def createOutputData( jobs ):
    """ Reads out the meta data.
    """
    failedImages = []
    nJobs = len( jobs )
    for n, j in enumerate( jobs ):
        print( "Job " + str(n+1) + "/" + str( nJobs ) )
        # load every image
        metadata = []
        nImages = len( j.sourceImages )
        nChannels = -1
        for m, img in enumerate( j.sourceImages ):
            print( "\tReading image " + str(m+1) + "/" + str( nImages ) )
            imgPath = os.path.join( j.sourcePath, img )
            options = ImporterOptions()
            options.setId( imgPath )
            options.setSplitChannels( False )
            options.setWindowless( True )
            options.setVirtual( True )
            imps = BF.openImagePlus( options )
            if len(imps) == 0:
                failedImages.append( imgPath )
                print("t\tCould not load image: " + imgPath)
                continue
            # get the meta data
            data = imps[0]
            if nChannels == -1:
                nChannels = data.getNChannels() 
            imgInfo = Info();
            info = imgInfo.getImageInfo( data, data.getChannelProcessor() )
            metadata.append( imgPath )
            metadata.append( info )
        j.outputData = '\n\n>>> next source file >>>\n\n'.join( metadata )
        j.numChannels = nChannels

def getDataPart( data, lineStart ):
    """ Get the end of line in data, starting with lineStart.
    """
    posOne = data.find( lineStart )
    if posOne != -1:
        posOne = posOne + len( lineStart )
        posTwo = data.find( "\n", posOne )
        substring = data[posOne:posTwo]
        return substring
    else:
        print("\tCould not find \"" + lineStart + "\"" )
        return None

def writeOutData( jobs ):
    """ Writes out the whole meta data to a file in the folder
    of the image. A reduced form of that data is written to the
    info.yml file.
    """
    print( "Writing files" )
    for j in jobs:
        # write file with all data
        metadataFile = os.path.join( j.outputPath, "original_metadada.txt" )
        f = open(metadataFile, 'w')
        f.write( j.outputData )
        f.close()
        print( "\tWrote " + metadataFile )
        # read in existing info.yml (if any)
        existingYAML = ""
        infoFile = os.path.join( j.outputPath, "info.yml" )
        if os.path.exists( infoFile ):
            f = open( infoFile )
            lines = []
            while 1:
                line = f.readline()
                if not line:
                    break
                line = line[:len(line)-1]
                # ignore existing metadata lines
                if not line.startswith("metadata-ch"):
                    lines.append( line )
            f.close()
            existingYAML = '\n'.join( lines )
        # create a shortened version of the meta data
        metadataYAML = []
        for i in range(0, j.numChannels):
            md = "metadata-ch" + str(i) + ": \""
            mdList = []
            # Look for current channels AnalogPMTOffset
            offsetStr = "Image " + str(i) + " : AnalogPMTOffset = "
            offsetData = getDataPart( j.outputData, offsetStr )
            if offsetData != None:
                mdList.append( "PMT Offset: " + offsetData )
            powerStr = "Image " + str(i) + " : ExcitationOutPutLevel = "
            powerData =  getDataPart( j.outputData, powerStr )
            if powerData != None:
                mdList.append( "Laser Power: " + powerData )
            gainStr = "Image " + str(i) + " : PMTVoltage = "
            gainData =  getDataPart( j.outputData, gainStr )
            if gainData != None:
                mdList.append( "PMT Voltage: " + gainData )
            md = md + ", ".join( mdList ) + "\""
            metadataYAML.append( md )
        # write all out to the info.yml
        shortMetaData = '\n'.join( metadataYAML )
        outputYAML = existingYAML + "\n" + shortMetaData
        f = open(infoFile, 'w')
        f.write( outputYAML )
        f.close()
        print( "\tWrote " + infoFile )

def main():
    jobs = createJobs( infoFiles )
    checkJobs( jobs )
    createOutputData( jobs )
    writeOutData( jobs )
    print( "done" )


# call main
if __name__ == "__main__":
    main()
