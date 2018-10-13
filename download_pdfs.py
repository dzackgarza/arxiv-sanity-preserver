#!/usr/bin/python3
import os
import time
import pickle
import shutil
import random
import urllib
import requests
from  urllib.request import urlopen
from termcolor import colored
from utils import Config

printgreen = lambda q: print(colored(q, 'green'))
printred = lambda q: print(colored(q, 'red'))


printgreen("Loading list of current PDFs...")

timeout_secs = 20 # after this many seconds we give up on a paper
if not os.path.exists(Config.pdf_dir): os.makedirs(Config.pdf_dir)
have = set(os.listdir(Config.pdf_dir)) # get list of all pdfs we already have

printgreen("Loading database...")
numok = 0
numtot = 0
db = pickle.load(open(Config.db_path, 'rb'))

doproxy = True
if doproxy:
    session = requests.session()
    session.proxies = {
        'http': 'socks5://localhost:9050',
        'https': 'socks5://localhost:9050'
    }
    headers = {'User-agent': 'HotJava/1.1.2 FCS'}

start_time = time.time()
num_session = 0

printgreen("Starting downloads!")
for pid,j in db.items():

  pdfs = [x['href'] for x in j['links'] if x['type'] == 'application/pdf']
  assert len(pdfs) == 1
  pdf_url = pdfs[0] + '.pdf'
  basename = pdf_url.split('/')[-1]
  fname = os.path.join(Config.pdf_dir, basename)

  # try retrieve the pdf
  try:
    if not basename in have:
      numtot += 1
      print('fetching %s into %s' % (pdf_url, fname))
      num_session += 1
      if doproxy:
          req = session.get(pdf_url)
          with open(fname, 'wb') as fp:
            shutil.copyfileobj(req.raw, fp)
      else:
        req = urlopen(pdf_url, None, timeout_secs)
        with open(fname, 'wb') as fp:
            shutil.copyfileobj(req, fp)
      sleeptime = 0 + random.uniform(0,0.25)
      tot_time = time.time() - start_time   # Seconds
      dl_rate = num_session / tot_time      # Papers/second
      num_left = len(db) - numok # Papers
      est_time = 1/dl_rate * num_left       # Seconds/Paper * Papers = Seconds
      printgreen('Success. Now sleeping {} seconds. Estimated remaining time: {} hours'.format(sleeptime, round(est_time * (1/60)**2, 2)))
      print('Total time: {}\nTotal papers this session: {} papers\nRate: {} sec/paper'.format(tot_time, numtot, round(1/dl_rate, 2)))
      time.sleep(sleeptime)
    else:
      print('%s exists, skipping' % (fname, ))
    numok+=1
  except Exception as e:
    printred('error downloading: {}'.format(pdf_url))
    print(e)

  print('%d/%d of %d downloaded ok.' % (numok, numtot, len(db)))

print('final number of papers downloaded okay: %d/%d' % (numok, len(db)))

