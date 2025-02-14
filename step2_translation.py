"""\
This script reads a text file called translate_in.txt, separates by line, and sends each line to google cloud translate 
to be translated to English.
Raw JSON response is saved to translate_web.txt for posterity.

Output at translate_out.txt is a tab-separated list of urls and their transcript. Newlines are not an issue with our data set but may be with
other languages, consider denoting transcript start/end within something other than newlines/tabs.

Setup requirements including getting an API key can be found at the official tutorial:
https://cloud.google.com/python/docs/reference/translate/latest

Requirements:
pip install google-cloud-translate
pip install tqdm
"""

import six

from google.cloud import translate_v2 as translate
from tqdm import tqdm

translate_client = translate.Client()

def translate_text(text):
	if isinstance(text, six.binary_type):
		text = text.decode("utf-8")

	# Text can also be a sequence of strings, in which case this method
	# will return a sequence of results for each text.
	return translate_client.translate(text, target_language='en')



fileIn = open("./io/translate_in.txt","r", encoding="utf8")
lines = fileIn.readlines()
fileIn.close()

text = ""
web = "["
for line in tqdm(lines):
	translation = translate_text(line)
	web += str(translation) + ","
	text += translation["translatedText"] + "\n"


fileOut = open("./io/translate_out.txt", "w+", encoding="utf8")
fileOut.write(text)
fileOut.close()

web += "]"
fileOut = open("./io/ranslate_web.txt", "w+", encoding="utf8")
fileOut.write(web)
fileOut.close()