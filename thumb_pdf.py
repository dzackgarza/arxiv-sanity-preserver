#!/usr/bin/python3
"""
Use imagemagick to convert all pfds to a sequence of thumbnail images
requires: sudo apt-get install imagemagick
"""

import os
import time
import shutil
from subprocess import Popen

from utils import Config

# make sure imagemagick is installed
if not shutil.which('convert'): # shutil.which needs Python 3.3+
  print("ERROR: you don\'t have imagemagick installed. Install it first before calling this script")
  sys.exit()

# create if necessary the directories we're using for processing and output
pdf_dir = os.path.join('data', 'pdf')
if not os.path.exists(Config.thumbs_dir): os.makedirs(Config.thumbs_dir)
if not os.path.exists(Config.tmp_dir): os.makedirs(Config.tmp_dir)

# fetch all pdf filenames in the pdf directory
pdf_files = set([x for x in os.listdir(pdf_dir) if x.endswith('.pdf')]) # filter to just pdfs, just in case
thumbnails_have = set([p[0:-4] for p in os.listdir(Config.thumbs_dir) if p.endswith(".pdf.jpg")])
to_process = list(pdf_files - thumbnails_have)

l = len(to_process)
print("Number of PDFs: %s \nNumber of thumbnails: %s \nNumber to process: %s" % (len(pdf_files), len(thumbnails_have), l))

bad_thumbs = set()
bad_pdfs = set()

# iterate over all pdf files and create the thumbnails
for i,p in enumerate(to_process):
  print("---------------------------------------------------------")
  pdf_path = os.path.join(pdf_dir, p)
  thumb_path = os.path.join(Config.thumbs_dir, p + '.jpg')

  pdfReturnCode = os.WEXITSTATUS( os.system('pdftotext %s' % pdf_path) )
  if not pdfReturnCode == 0:
    print("PDF file not valid: %s \nSkipping.." % p)
    bad_pdfs.add(p)
    continue
  else:
    print("File appears to be a valid PDF: %s \nReturn code: %s" % (p, pdfReturnCode))

  # if os.path.isfile(thumb_path):
    # print("skipping %s, thumbnail already exists." % (pdf_path, ))
    # continue

  print("%d/%d processing %s" % (i, l, p))

  # take first 8 pages of the pdf ([0-7]), since 9th page are references
  # tile them horizontally, use JPEG compression 80, trim the borders for each image
  #cmd = "montage %s[0-7] -mode Concatenate -tile x1 -quality 80 -resize x230 -trim %s" % (pdf_path, "thumbs/" + f + ".jpg")
  #print "EXEC: " + cmd

  # nvm, below using a roundabout alternative that is worse and requires temporary files, yuck!
  # but i found that it succeeds more often. I can't remember wha thappened anymore but I remember
  # that the version above, while more elegant, had some problem with it on some pdfs. I think.

  # erase previous intermediate files thumb-*.png in the tmp directory
  if os.path.isfile(os.path.join(Config.tmp_dir, 'thumb-0.png')):
    for i in range(8):
      f = os.path.join(Config.tmp_dir, 'thumb-%d.png' % (i,))
      f2= os.path.join(Config.tmp_dir, 'thumbbuf-%d.png' % (i,))
      if os.path.isfile(f):
        cmd = 'mv %s %s' % (f, f2)
        os.system(cmd)
        # okay originally I was going to issue an rm call, but I am too terrified of
        # running scripted rm queries, so what we will do is instead issue a "mv" call
        # to rename the files. That's a bit safer, right? We have to do this because if
        # some papers are shorter than 8 pages, then results from previous paper will
        # "leek" over to this result, through the intermediate files.

  # spawn async. convert can unfortunately enter an infinite loop, have to handle this.
  # this command will generate 8 independent images thumb-0.png ... thumb-7.png of the thumbnails
  full_cmd = ['convert', '%s[0-7]' % (pdf_path, ), '-thumbnail', 'x156', '+profile', '"*"', os.path.join(Config.tmp_dir, 'thumb.png')]
  print("Running convert command")
  print(" ".join(full_cmd))

  pp = Popen(full_cmd)
  t0 = time.time()
  while time.time() - t0 < 60: # give it n seconds deadline
    ret = pp.poll()
    if not (ret is None):
      # process terminated
      break
    time.sleep(0.1)

  ret = pp.poll()

  if ret is None:
    print("Time up: convert command did not finish. Skipping.")
    pp.terminate() # give up
  else:
    print("Convert command successful.")

  pdf_is_rendered = os.path.isfile(os.path.join(Config.tmp_dir, 'thumb-0.png'))

  if not pdf_is_rendered:
    print("Convert did not successfully generate thumbnails. Adding to log and skipping.")
    bad_pdfs.add(p)
    bad_thumbs.add(p)
  else:
    cmd = "montage -mode concatenate -quality 80 -tile x1 %s %s" % (os.path.join(Config.tmp_dir, 'thumb-*.png'), thumb_path)
    print("Creating montage..")
    print(cmd)
    os.system(cmd)

  print("Done, next.")
  time.sleep(0.01) # silly way for allowing for ctrl+c termination


with open("bad_thumbs.log", 'w') as f:
    f.writelines(bad_thumbs)
with open("bad_pdfs.log", 'w') as f:
    f.writelines(bad_pdfs)

print("Done. Number of bad thumbs found: %s" % len(bad_thumbs))
