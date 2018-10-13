#!/usr/bin/python3
"""
Use imagemagick to convert all pfds to a sequence of thumbnail images
"""

import os
import time
import shutil
import glob
import subprocess

from utils import Config

def save():
    open("known_bad_thumbs.txt", 'w').writelines([l + '\n' for l in list(known_bad_thumbs)])

import signal
def signal_handler(sig, frame):
    print('Program interrupted, saving files...')
    save()
    print('Saved, now exiting')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

if not shutil.which('convert'): # shutil.which needs Python 3.3+
    print("ERROR: you don\'t have imagemagick installed. Install it first before calling this script")
    sys.exit()

pdf_dir = Config.pdf_dir
if not os.path.exists(Config.thumbs_dir): os.makedirs(Config.thumbs_dir)
if not os.path.exists(Config.tmp_dir): os.makedirs(Config.tmp_dir)

pdf_files = set([x for x in os.listdir(pdf_dir) if x.endswith('.pdf')])
thumbnails_have = set([p[0:-4] for p in os.listdir(Config.thumbs_dir) if p.endswith(".pdf.jpg")])
known_bad_pdfs = set([l.strip() for l in open("known_bad_pdfs.txt").readlines()])
known_bad_thumbs = set([l.strip() for l in open("known_bad_thumbs.txt").readlines()])

to_process = pdf_files - (thumbnails_have | known_bad_pdfs | known_bad_thumbs)

l = len(to_process)
print("Number of PDFs: %s \nNumber of thumbnails: %s \nNumber to process: %s" % (len(pdf_files), len(thumbnails_have), l))

for i,p in enumerate(to_process):
    print("---------------------------------------------------------")
    pdf_path = os.path.join(pdf_dir, p)
    thumb_path = os.path.join(Config.thumbs_dir, p + '.jpg')

    print("%d/%d processing %s" % (i, l, p))

    # erase previous intermediate files thumb-*.png in the tmp directory
    for f in glob.glob("%s/*.png" % Config.tmp_dir):
            os.remove(f)

    try:
        convert_cmd = ['convert', '%s[0-7]' % (pdf_path, ), '-thumbnail', 'x156', '+profile', '"*"', os.path.join(Config.tmp_dir, 'thumb.png')]
        print("Running: ", " ".join(convert_cmd))

        thumb_return_code = subprocess.call(convert_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout = 120)
        if (thumb_return_code != 0): raise Exception("Convert failed, %s" % thumb_return_code)

        thumb_was_rendered = os.path.isfile(os.path.join(Config.tmp_dir, 'thumb-0.png'))
        if not thumb_was_rendered:
            known_bad_thumbs.add(p)
            raise Exception("No thumbnail found in temporary directory")

        montage_cmd = "montage -mode concatenate -quality 80 -tile x1 %s %s" % (os.path.join(Config.tmp_dir, 'thumb-*.png'), thumb_path)
        print("Running: %s" % montage_cmd)

        montage_return_code = subprocess.call(montage_command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout = 120)
        if (montage_return_code != 0): raise Exception("Montage failed, %s" % montage_return_code)

    except Exception as e:
        print("(%s) Convert command not successful: %s" % (p, e))
        continue


print("Done. Number of bad thumbs found: %s" % len(known_bad_thumbs))
save()
