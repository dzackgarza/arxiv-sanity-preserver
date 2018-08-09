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


# after this many seconds we give up on a paper
timeout_secs = 10

if not os.path.exists(Config.pdf_dir):
    os.makedirs(Config.pdf_dir)

# get list of all pdfs we already have
print("Listing files..")
have = set(os.listdir(Config.pdf_dir))

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

print("Starting...")
for pid,j in db.items():

    pdfs = [x['href'] for x in j['links'] if x['type'] == 'application/pdf']
    assert len(pdfs) == 1
    pdf_url = pdfs[0] + '.pdf'
    basename = pdf_url.split('/')[-1]
    fname = os.path.join(Config.pdf_dir, basename)

    try:
        if not basename in have:
            numtot += 1
            print('\n Fetching %s into %s\n' % (pdf_url, fname))
            num_session += 1
            if doproxy:
                req = session.get(pdf_url, timeout=timeout_secs)
                if(req.headers['Content-Type'] == 'application/pdf'):
                    open(fname, 'wb').write(req.content)
                else:
                    raise ValueError("Response is not a PDF: {}".format(pdf_url))
            else:
                req = urlopen(pdf_url, None, timeout_secs)
                with open(fname, 'wb') as fp:
                    shutil.copyfileobj(req, fp)
            sleeptime = 0 + random.uniform(0,0.25)
            tot_time = time.time() - start_time   # Seconds
            dl_rate = num_session / tot_time      # Papers/second
            num_left = len(db) - numok # Papers
            est_time = 1/dl_rate * num_left # Seconds/Paper * Papers = Seconds
            printgreen('Success. Now sleeping {} seconds. Estimated remaining time: {} hours'.format(sleeptime, round(est_time * (1/60)**2, 2)))
            print('Total time: {}\nTotal papers this session: {} papers\nRate: {} sec/paper'.format(tot_time, numtot, round(1/dl_rate, 2)))
            time.sleep(sleeptime)
        else:
            #print('%s exists, skipping' % (fname, ))
            print(".", end='', flush=True)
        numok+=1
    except Exception as e:
        printred('Error downloading: {}'.format(pdf_url))
        open("error.log", "a").write(pdf_url + '\n')
        print(e)
    if(numok % 200 == 1):
        print('\n%d/%d of %d downloaded ok.\n' % (numok, numtot, len(db)))

print('Final number of papers downloaded okay: %d/%d' % (numok, len(db)))

