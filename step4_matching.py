"""\
This script finds and sorts a candidate list of matches from a FCD for the descriptions extracted in the prior step. It then compares 
the reference items identified by human analysts to the candidate items.

Inputs two files:
(1) db_names.txt A list of names as seen in a FCD.
(2) matching_in.txt A list of records to perform the matching algoritm on. One record per line. Each line contains 3 tab-separated columns:
<id : a reference id for the line/record>	<descriptions : comma-separated list of discrete item descriptions resulting from step 3>	<references : a list of reference items separated by ; character>

Outputs two files:
(1) matching_out_records.txt Lists how many of the reference items could be found and the average index references were found within the candidate shortlist
(2) matching_out_items.txt Lists all reference items, and the index at which they could be found in the candidate shortlist. References with no candidate have an index of 0

For languages other than english, refer to the spaCy documentation to download or use appropriate models.
https://spacy.io/usage/models/

Requirements:
pip install spacy
pip install tqdm

python -m spacy download en_core_web_lg
"""

import re
import string

import spacy
from tqdm import tqdm

nlp = spacy.load("en_core_web_lg")
nlp.add_pipe("merge_noun_chunks")

dbIn = open("./io/db_names.txt","r")
rNames = dbIn.readlines()
names = []
dbIn.close()
for name in rNames:
	names.append(name.strip().lower())
names.sort(key=len)

#Classes to hold results
class Node:
	item = None
	score = -1
	found = 0
	index = -1

class Group:
	text = ""
	index = -1
	nodes = []
	matched = False
class Match:
	mid = -1
	text = ""
	index = -1
	group = None
	matched = False

def sort_f(node):
	return node.found
def sort_i(node):
	return node.index

fileRecord = open("./io/matching_out_records.txt", "w+")
fileItems = open("./io/matching_out_items.txt", "w+")

lemma_tags = {"NNS", "NNPS"}
def check_lemma(token):
	if token.tag_ in lemma_tags:
		return token.lemma_
	return token.text

def has_unmatched(groups):
	matches = [g for g in groups if g.matched == False]
	return len(matches) > 0

def run(line):
	splits = line.split("\t")
	idCode = splits[0].strip()
	texts = splits[1].lower().split(", ")
	targets = splits[2].lower().split(";") #Use a character not appearing in your FCD to separate reference items
	groups = []

	#Find matches for each discrete description resulting from prior step (CSV list of descriptions)
	for text in texts:
		#If using a FCD with hyphenated names (e.g. pan-fried) this will need to be edited to not remove the hyphen
		text = text.translate(str.maketrans('', '', string.punctuation))
		group = Group()
		group.text = text.strip()
		if len(group.text) == 0:
			continue

		#NLP the single description (not whole line)
		doc = nlp(text)
		searchTerm = ""
		replaced = False

		#Only use parts of description relevant for matching.
		#Descriptors like "grilled", "chicken flavoured" will be bundled in by the noun-chunk pipeline (token has multiple words)
		for token in doc:
			if (token.dep_ == 'pobj'):
				#Use lemmatized versions of words where possible
				#Some FCDs may require a map of lemmatized forms to match to this
				searchTerm = searchTerm + " " + check_lemma(token)
				replaced = True
		if not replaced:
			for token in doc:
				if (token.dep_ == 'ROOT'):
					searchTerm = check_lemma(token)
					replaced = True
		if replaced == False:
			print(text)

		nodes = []
		arrows = searchTerm.strip().split(" ")
		for name in names:
			node = Node()
			node.text = name
			for arrow in arrows:

				# Version using number of , characters as the index rather than total characters
				# s = name.split(arrow.lower())
				# if len(s) < 2:
				# 	continue
				# node.found = node.found + 1
				# index = len(s[0].split(","))
				# node.index = node.index + index

				#Search for individual word in FCD name
				regex = re.search("\\b" + arrow + "\\b", name)
				if regex == None:
					continue
				index = regex.start()
				node.found = node.found + 1
				if node.index < 0 or index < node.index:
					node.index = index

			if node.found > 0:
				nodes.append(node)

		# Sort matches
		nodes.sort(key=sort_i)
		nodes.sort(key=sort_f, reverse=True)
		group.nodes = nodes
		if len(group.nodes) > 0:
			groups.append(group)

	#The list of groups can be returned to the frontend display at this point. 
	#The remaining code compares the reference matches provided by human analysts, and the candidate matches found above

	find_count = 0
	avg_index = 0

	matches = []

	#Create a match object for each of the reference
	for idx, target in enumerate(targets):
		match = Match()
		match.text = target.strip()
		match.mid = idx
		matches.append(match)

	#Loop until all matches have been fulfilled by a candidate, or there is no appropriate candidates remaining.
	while has_unmatched(matches):
		for match in matches:
			if match.matched:
				continue

			t = match.text
			for group in groups:
				for idx, node in enumerate(group.nodes):
					if node.text == t:
						if match.group != None and match.group.index < idx:
							break;
						found = True
						group.index = idx
						match.group = group
						break;
			match.matched = True

		#Check for duplicate matches and remove worst fit
		#Worse candidate is reset to matches=false so the loop will attempt to find a new match
		for m1 in matches:
			for m2 in matches:
				if (m1.mid == m2.mid):
					continue
				if m1.group != None and m2.group != None and m1.group.text == m2.group.text:
					try:
						groups.remove(m1.group)
					except Exception as e:
						pass

					if m1.group.index < m2.group.index:
						m2.group = None
						m2.matched = False
					else:
						m1.group = None
						m1.matched = False

	#As there may be more than one item per record (input line), a second output file lists all items and the index
	#at which the analyst-selected item was found in the subset 
	for match in matches:
		toWriteItems = idCode + "\t" + match.text + "\t"
		if match.group != None:
			find_count = find_count + 1
			avg_index += match.group.index
			toWriteItems += str(match.group.index + 1) + "\n"
		else:
			toWriteItems += str(0) + "\n"
		fileItems.write(toWriteItems)

	if find_count > 0:
		avg_index = str(avg_index / len(target))
	else:
		avg_index = "NULL"

	return str(find_count) + "\t" + avg_index


fileIn = open("matching_in.txt","r",encoding='utf-8')
lines = fileIn.readlines()
fileIn.close()

for line in tqdm(lines):
	result = run(line)
	fileRecord.write(result + "\n")


fileRecord.close()
fileItems.close()