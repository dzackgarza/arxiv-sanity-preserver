#!/usr/bin/python3
"""
Very simple script that simply iterates over all files data/pdf/f.pdf
and create a file data/txt/f.pdf.txt that contains the raw text, extracted
using the "pdftotext" command. If a pdf cannot be converted, this
script will not produce the output file.
"""

import os
import sys
import time
import shutil
import pickle

from utils import Config

if not shutil.which('pdftotext'): # needs Python 3.3+
  print('ERROR: you don\'t have pdftotext installed. Install it first before calling this script')
  sys.exit()

# todo: add interrupt handler

if not os.path.exists(Config.txt_dir): os.makedirs(Config.txt_dir)

have = set(os.listdir(Config.txt_dir))
files = os.listdir(Config.pdf_dir)
badfiles = set()
# Todo: check for known bad text conversions

print( "Have %s txt files" % len(have) )
print( "Have %s pdf files" % len(files) )
i = 0

for i,f in enumerate(files):
  i = i + 1

  txt_basename = f + '.txt'
  if txt_basename in have:
    #print('%d/%d skipping %s, already exists.' % (i, len(files), txt_basename, ))
    if(i % 1000 == 0):
        print('.', end='', flush=True)
    continue

  pdf_path = os.path.join(Config.pdf_dir, f)
  txt_path = os.path.join(Config.txt_dir, txt_basename)
  cmd = "pdftotext %s %s" % (pdf_path, txt_path)
  os.system(cmd)

  print('\n%d/%d %s\n' % (i, len(files), cmd), end='')

  if not os.path.isfile(txt_path):
    print('there was a problem with parsing %s to text' % (pdf_path, ))
    # os.system('touch ' + txt_path) # create empty file, but it's a record of having tried to convert
    badfiles.add(pdf_path)

  time.sleep(0.01) # silly way for allowing for ctrl+c termination

print("\nProcessed %s files" % i)
open('badpdfconvertfiles.txt', 'w').writelines([l + '\n' for l in list(badfiles)])

