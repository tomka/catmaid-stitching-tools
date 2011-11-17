#!/usr/bin/python

import os
import glob
import sys

# We need one argument for knowing the tiling base folder

if len(sys.argv) != 2:
	print "usage: findinfos.py /path/to/tiling/base"
	sys.exit(1)

tilingBase = sys.argv[1]
if os.path.exists(tilingBase):
	print "using tiling base path: " + tilingBase
else:
	print "could not find tiling base path: " + tilingBase
	sys.exit(1)

# Open info file with folders to look in
infoFiles = []
file = open("findinfos.txt")
while 1:
	line = file.readline()
	line = line[:len(line)-1]
	if not line:
		break
	if not os.path.isdir(line):
		print "not a dir: " + line
		continue
	for currentFile in glob.glob( os.path.join(line, '*wrapper*.log')):
		infoFiles.append(currentFile)
file.close()

# look at files
markerOne = "one composite image with dimensions "
markerTwo = " slices"
marker3 = "width convetsion value \""
marker4= "width conversion value \""
outputInfos = {}
for infoFile in infoFiles:
	print infoFile
	dimStr = ""
	resStr = ""
	file = open(infoFile)
	# get path of file
	outputDir = os.path.dirname(infoFile)
	while 1:
		line = file.readline()
		line = line[:len(line)-1]
		if not line:
			break
		# find dimensions
		posOne = line.find(markerOne)
		if posOne != -1:
			posTwo = line.find(markerTwo, posOne)
			posOne = posOne + len(markerOne)
			dimensions = line[posOne:posTwo]
			xPos = dimensions.find("x")
			dimOne = dimensions[:xPos]
			andStr = " and "
			andPos = dimensions.find(andStr)
			dimTwo = dimensions[xPos+1:andPos]
			dimThree = dimensions[andPos+len(andStr):]
			dimStr = "dimension: " + "(" + dimOne + "," + dimTwo + "," + dimThree + ")"
			print dimStr
			continue
		# find resolution
		pos3 = line.find(marker3)
		if pos3 == -1:
			pos3 = line.find(marker4)
		if pos3 != -1:
			pos4 = line.find("\"", pos3 + len(marker3))
			xRes = line[pos3+len(marker3):pos4]
			xResNr = float(xRes)
			xResNr = xResNr * 1000
			xRes = str(xResNr)
			resStr = "resolution: " + "(" + xRes + "," + xRes + "," + xRes + ")"
			print resStr
	# remember results
	outputInfos[outputDir] = dimStr + "\n" + resStr

# write out info.yml
outputFile = "info.yml"
for od in outputInfos:
	outputStr = outputInfos[od]
	# find output file paths by getting the name of the first
	# tif or tiff file we find
	outputDirBase = ""
	for imgFile in glob.glob( os.path.join(od, '*.tif*')):
		outputDirBase = os.path.basename(imgFile)
		# remove extension
		outputDirBase = outputDirBase[:outputDirBase.rfind(".tif")]
		break
	print outputDirBase
	extensions = ["-ch1", "-ch2", "-ch3", "-ch4", "-composite"]
	for ext in extensions:
		outputDir = os.path.join(tilingBase, outputDirBase + ext)
		outputPath = os.path.join(outputDir, outputFile)
		if not os.path.exists(outputDir):
			print "\tNot existing: " + outputDir
			continue
		print "\toutput to: " + outputPath
		f = open(outputPath, 'w')
		f.write(outputStr)
		f.close()

print "done"

		
