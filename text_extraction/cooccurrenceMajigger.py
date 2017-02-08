import sys
import fileinput
import argparse
import time
from collections import Counter
import itertools
from textExtractionUtils import *
	
# Find all co-occurrences for a list of text, or just a line of text
def extractTermCoOccurrences_OneList(outFile, textInput, textSourceInfo):

	# First check if it is a list of text or just text
	if isinstance(textInput, list):
		textList = textInput
	else:
		textList = [textInput]
	
	# Go through each bit of text
	for text in textList:
		# Remove weird text issues
		text = handleEncoding(text)
	
		# Split the text into sentences
		sentences = sentenceSplit(text)

		# Extract each sentence
		for sentence in sentences:
			
			# Tokenize each sentence
			tokens = tokenize(sentence)
			
			# Get the IDs of terms found in the sentence
			termIDs = getID_FromLongestTerm(tokens, mainWordlist)
			
			#print "-------------------------"
			#print sentence
			#print tokens
			#print [ unicodeLower(t) for t in tokens ]
			#print termIDs
			#print "-------------------------"
			#print
			
			# Remove duplicates from the termIDs
			termIDs = set(termIDs)
			
			# Print co-occurrences to output file immediately
			for (i,j) in itertools.product(termIDs,termIDs):
				if i<j:
					outFile.write("COOCCURRENCE\t%d\t%d\t%d\n" % (i, j, 1))

			# Print out which terms appear in this sentence
			for i in termIDs:
				outFile.write("OCCURRENCE\t%d\t%d\n" % (i, 1))

		# Print out the number of sentences
		sentenceCount = len(sentences)
		outFile.write("SENTENCECOUNT\t%d\n" % (sentenceCount))
		
		
# It's the main bit. Yay!
if __name__ == "__main__":

	# Arguments for the command line
	parser = argparse.ArgumentParser(description='Full co-occurrence pipeline that extracts text from MEDLINE/PMC files, splits into sentences using LingPipe, tags with GENIA and does more!')
	parser.add_argument('--termsWithSynonymsFile', type=argparse.FileType('r'), help='A list of terms for extraction with synonyms separated by a |')
	parser.add_argument('--binaryTermsFile', type=argparse.FileType('rb'), help='A pickled representation of a word-list, previously generated by this script')
	parser.add_argument('--binaryTermsFile_out', type=argparse.FileType('wb'), help='An output file to save the term list to in a binary format (for faster loading later)')
	
	parser.add_argument('--stopwordsFile',  type=argparse.FileType('r'), help='A path to a stopwords file that will be removed from term-lists (e.g. the, there)')
	parser.add_argument('--removeShortwords', help='Remove short words from any term lists (<=2 length)', action='store_true')

	parser.add_argument('--abstractsFile', type=argparse.FileType('r'), help='MEDLINE file containing abstract data')
	parser.add_argument('--articleFile', type=argparse.FileType('r'), help='PMC NXML file containing a single article')
	parser.add_argument('--articleFilelist', type=argparse.FileType('r'), help='File containing filenames of multiple PMC NXML files')

	parser.add_argument('--outFile', type=argparse.FileType('w'), help='File to output cooccurrences')

	args = parser.parse_args()
	
	# Output execution information
	print "######################"
	print " cooccurrenceMajigger "
	print "######################"
	print ""
	if args.termsWithSynonymsFile:
		print "--termsWithSynonymsFile", args.termsWithSynonymsFile.name
	if args.binaryTermsFile:
		print "--binaryTermsFile", args.binaryTermsFile.name
	if args.binaryTermsFile_out:
		print "--binaryTermsFile_out", args.binaryTermsFile_out.name
	if args.stopwordsFile:
		print "--stopwordsFile", args.stopwordsFile.name
	if args.removeShortwords:
		print "--removeShortwords"
	if args.abstractsFile:
		print "--abstractsFile", args.abstractsFile.name
	if args.articleFile:
		print "--articleFile", args.articleFile.name
	if args.articleFilelist:
		print "--articleFilelist", args.articleFilelist.name
	if args.outFile:
		print "--outFile", args.outFile.name
	print ""
	print "######################"
	print ""

	# If loading terms from a text file, close the handle so that it be re-opened
	# with a Unicode codec later
	if args.termsWithSynonymsFile:
		wordlistPath = args.termsWithSynonymsFile.name
		args.termsWithSynonymsFile.close()
	else:
		wordlistPath = None
	
	if not (args.termsWithSynonymsFile or args.binaryTermsFile):
		raise RuntimeError("--termsWithSynonymsFile or --binaryTermsFile must be set")
	
	# Load the parsing tools
	loadParsingTools()
	
	# Dictionary to contain terms->IDs from a word-list
	mainWordlist = loadWordlistFile(wordlistPath, args.stopwordsFile, args.removeShortwords, args.binaryTermsFile, args.binaryTermsFile_out)
		
	startTime = time.time()

	# And now we try to process either an abstract file, single article file or multiple
	# article files
	try:
		if args.abstractsFile:
			processAbstractFile(args.abstractsFile, args.outFile, extractTermCoOccurrences_OneList)
		elif args.articleFile:
			# Just pull the filename and pass that, instead of the object
			filename = args.articleFile.name
			args.articleFile.close()
			processArticleFiles(filename, args.outFile, extractTermCoOccurrences_OneList)
		elif args.articleFilelist:
			# Extract the file list from another file
			fileList = [ f.strip() for f in args.articleFilelist]
		
			processArticleFiles(fileList, args.outFile, extractTermCoOccurrences_OneList)
	except:
		print "Unexpected error:", sys.exc_info()[0]
		print "COMMAND: " + " ".join(sys.argv)
		raise

	endTime = time.time()
	duration = endTime - startTime
	print "Processing Time: ", duration
	
	# Print completion if we were working on an outFile
	if args.outFile:
		print "Finished output to:", args.outFile.name
	

