"""\
This script takes a english descriptions of one or more food items, using spaCy to identify and extract expanded noun-chunks.
Input accepts multiple descriptions at once, separated by line
Output to processing_out.txt consists of a Comma Separated list of discrete noun chunks. One list per line as input


For languages other than english, refer to the spaCy documentation to download or use appropriate models.
https://spacy.io/usage/models/

Requirements:
pip install spacy
pip install tqdm

python -m spacy download en_core_web_lg
"""

import spacy
import re
from tqdm import tqdm

def run(text):
	#Normalize whitespace
	text = " ".join(text.split())

	doc = nlp(text)

	# Initial noun-chunks
	noun_chunks = [nc for nc in doc.noun_chunks]

	spans = []

	#Expand noun-chunking for prep relations i.e. "A bowl of chicken soup" rather than "A bowl", "chicken soup"
	with doc.retokenize() as retokenizer:
		for token in doc:
			if token.dep_ == "prep":
				if len([child for child in token.children]) == 0:
					continue
				i1 = token.head.i
				i2 = [child for child in token.children][0].i
				for nc in noun_chunks:
					if i1 >= nc.start and i1 < nc.end:
						spans.append(doc[i1:i2+1])
						break

	# Build list of initial and expanded noun_chunks
	nspans = []
	for nc in noun_chunks:
		nspans.append(doc[nc.start:nc.end])
	for span in spans:
		nspans.append(span)
		for ospan in spans:
			if span.end > ospan.start and span.end <= ospan.end:
				nspans.append(doc[span.start:ospan.end])

	# Remove duplicate or subspan spans
	final_spans = spacy.util.filter_spans(nspans)

	if len(final_spans) == 0:
		final_spans.append(doc[0:len(doc)])

	out = ", ".join([str(span) for span in final_spans]) 
	#out =  str(len([span for span in final_spans])) #Uncomment to output count rather than items
	return out


nlp = spacy.load("en_core_web_md")
#Merge noun-chunks into single tokens i.e. "Cooked rice" rather than "Cooked", "rice"
nlp.add_pipe("merge_noun_chunks")

fileIn = open("./io/processing_in.txt","r", encoding="utf8")
lines = fileIn.readlines()
fileIn.close()

toWrite = ""
for line in tqdm(lines):
	# Strip non-english characters
	line_clean = re.sub(r'[^\x01-\x7F]+', '', line.strip())
	toWrite += run(line_clean) + "\n"

fileOut = open("./io/processing_out.txt", "w+")
fileOut.write(toWrite)
fileOut.close()