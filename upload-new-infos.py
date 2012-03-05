#!/usr/bin/python
#
# This tool will upload new info.yml files from their place in the stitched
# images folders to the CatMaid data storage.
#
# Synopsis: upload-new-infos.py <folder_file> <tiling_base>

import os
import glob
import sys

infoFile = "info.yml"

folderFile = ""
tilingBase = ""
exportToTiled = False

# Parse arguments
nArgs = len(sys.argv)
if nArgs == 3:
    folderFile = sys.argv[1]
    tilingBase = sys.argv[2]
else:
    print( "usage: upload-new-infos.py <folder_file> <tiling_base>" )
    sys.exit(1)

print( "using folder file: " + folderFile )
print( "using tiling base: " + tilingBase )


# Open info file with folders to look in
infoFileFolders = []
file = open( folderFile )
while 1:
	line = file.readline()
	if not line:
		break
	line = line.rstrip("\n")
	if not os.path.isdir(line):
		print "not a dir: " + line
		continue
	if not os.path.exists( os.path.join( line, infoFile ) ):
		print("Skipping -- found no info.yml in " + line)
		continue
	infoFileFolders.append( line )
file.close()

# copy to tiling folders
for infoFileFolder in infoFileFolders:
	infoFilePath = os.path.join( infoFileFolder, infoFile )
	print infoFilePath
	stitchedImgFolder = os.path.split( infoFileFolder )[1]

	# Create names for per-channel tile folders. First look
	# for a *.tiff file.
	imageFound = False
	outputFolders = []
    	for imgFile in glob.glob( os.path.join( infoFileFolder, '*.tiff')):
		if imageFound:
			print "\tFound more than one image, took first one!"
		imgFileBase = os.path.split( os.path.splitext( imgFile )[0] )[1]
		extensions = ["-ch1", "-ch2", "-ch3", "-ch4", "-composite"]
		for ext in extensions:
			outputDir = os.path.join( tilingBase, imgFileBase + ext)
			if not os.path.exists(outputDir):
				print "\tNot existing: " + outputDir
				continue
			print "\tfound tiling folder: " + outputDir
			outputFolders.append( outputDir )
		# we are actually only interested in the first (and only image)
		imageFound = True
	if not imageFound:
		print "\tFound NO image and could therefore not produce tiling folder names, continueing with next folder!"
		continue
	if len( outputFolders ) == 0:
		print "\tFound NO output folders, continueing with next folder!"
		continue

	# Read in existing info file
	f = open( infoFilePath )
	lines = []
	while 1:
		line = f.readline()
		if not line:
			break
		line = line.rstrip("\n")
		lines.append( line )
	f.close()
	info = "\n".join( lines )

	# Copy the info file over
	for of in outputFolders:
		print "\toutput to: " + of
		outputPath = os.path.join( of, infoFile )
		f = open(outputPath, 'w')
		f.write( info )
		f.close()
print "done"

		
