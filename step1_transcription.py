"""\
This script reads a text file containing line-separated urls, downloads each khmer speech audio at that url, 
then uses google transcription API to receive and save a text transcript of that audio to transcribe_out.txt.
Raw JSON response is saved to transcribe_web.txt for posterity.

Output of transcribe_out.txt is a tab-separated list of urls and their transcript. Newlines are not an issue with our data set but may be with
other languages, consider denoting transcript start/end within something other than newlines/tabs.

Setup requirements including getting an API key can be found at the official tutorial:
https://codelabs.developers.google.com/codelabs/cloud-speech-text-python3/#0

Requirements:
pip install google-cloud-speech
pip install tqdm
"""

import wget
import os

from google.cloud import speech
from tqdm import tqdm

client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="km-KH",
    enable_separate_recognition_per_channel=False
)
local_audio_url = './audio.mp3'

def transcribe_text() -> speech.RecognizeResponse:
    global local_audio_url
    with open(local_audio_url, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)


    response = client.recognize(config=config, audio=audio)
    return response

def download_file(url):
    global local_audio_url
    wget.download(url, local_audio_url)

fileIn = open("./io/transcribe_urls.txt","r", encoding="utf8")
lines = fileIn.readlines()
fileIn.close()

mainOut = open("./io/transcribe_out.txt", "w+", encoding="utf8")
webOut = open("./io/transcribe_web.txt", "w+", encoding="utf8")

for url in tqdm(lines):
    url = url.strip()

    #Remove the current local file
    if os.path.isfile(local_audio_url):
        os.remove(local_audio_url)

    # Download the file at the given url to the local folder
    try:
        download_file(url)
    except Exception:
        mainOut.write(url + "\tDOWNLOAD_FAILED\n")
        webOut.write("DOWNLOAD_FAILED\n|||\n")
        continue

    # Run transcription on the new local file
    try:
        response = transcribe_text()
    except Exception:
        print("TRANSCRIBE_FAILED")
        mainOut.write(url + "\tTRANSCRIBE_FAILED\n")
        webOut.write("TRANSCRIBE_FAILED\n|||\n")
        continue

    # Read the transcription response and write to output file
    web_out = str(response)
    transcript = "NULL"
    if hasattr(response, 'results') and len(response.results) > 0:
        transcript = response.results[0].alternatives[0].transcript

    mainOut.write(url + "\t" + transcript + "\n")
    webOut.write(web_out + "\n|||\n")

mainOut.close()
webOut.close()