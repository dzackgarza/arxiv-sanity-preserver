#!/usr/bin/python3

# Checks if the PDF files that were actually downloaded are in fact valid PDFs
import os
import sys
import time
import shutil
import pickle
import subprocess
from pathlib import Path


from utils import Config

if not shutil.which('pdftotext'):
    print("pdftotext not available, please install ImageMagick")
    sys.exit()

def save():
    open("known_good_pdfs.txt", 'w').writelines([l + '\n' for l in list(known_good_pdfs)])
    open("known_bad_pdfs.txt", 'w').writelines([l + '\n' for l in list(known_bad_pdfs)])

import signal
def signal_handler(sig, frame):
    print('Program interrupted, saving files...')
    save()
    print('Saved, now exiting')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

all_pdf_files = set([l for l in os.listdir(Config.pdf_dir) if l.endswith(".pdf") ])
known_good_pdfs = set([l.strip() for l in open("known_good_pdfs.txt").readlines()])
known_bad_pdfs = set([l.strip() for l in open("known_bad_pdfs.txt").readlines()])
unknown_files = all_pdf_files - (known_good_pdfs | known_bad_pdfs)

print("Number of all pdfs: %s" % len(all_pdf_files))
print("Number of known good pdfs: %s" % len(known_good_pdfs))
print("Number of known bad pdfs: %s" % len(known_bad_pdfs))
print("Number of unknown files: %s" % len(unknown_files))

print("Moving bad pdfs.")
for i,f in enumerate(known_bad_pdfs):
    pdf_path = os.path.join(Config.pdf_dir, f)
    pdf_file = Path(pdf_path)
    if pdf_file.is_file():
        os.rename( os.path.join(Config.pdf_dir, f), os.path.join(Config.bad_pdf_dir, f) )

if len(unknown_files) == 0:
    print("No unknown files, exiting.")
    sys.exit(0)

print("Sample from all pdfs: %s" % list(all_pdf_files)[0])
print("Sample from known good pdfs: %s" % list(known_good_pdfs)[0])
print("Sample from known bad pdfs: %s" % list(known_bad_pdfs)[0])
print("Sample from unknown pdfs: %s" %list(unknown_files)[0])


for i,f in enumerate(unknown_files):
    print(i)
    if i % 50 == 0:
        print(".",  end = '')
    pdf_path = os.path.join(Config.pdf_dir, f)
    pdf_return_code = subprocess.call(['pdftotext', pdf_path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if pdf_return_code == 0:
        print("Okay: %s" % f)
        known_good_pdfs.add(f)
    else:
        print("Bad: %s" % f)
        known_bad_pdfs.add(f)

print("All unknown files processed.")
save()

