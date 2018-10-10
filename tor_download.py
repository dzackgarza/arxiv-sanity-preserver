import os
import time
import pickle
import shutil
import random
import urllib
import requests
import concurrent.futures
import gc
from  urllib.request import urlopen
from termcolor import colored
from utils import Config, safe_pickle_dump

printgreen = lambda q: print(colored(q, 'green'))
printred = lambda q: print(colored(q, 'red'))

import signal
import sys
def signal_handler(sig, frame):
    printred('Program interrupted, saving database...')
    safe_pickle_dump(db, Config.db_path)
    printgreen('Saved, now exiting')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


session = requests.session()
session.proxies = {
    'http': 'socks5://localhost:9050',
    'https': 'socks5://localhost:9050'
}
headers = {
    'User-agent': 'HotJava/1.1.2 FCS'
}

db = pickle.load(open(Config.db_path, 'rb'))

def refreshNeeded():
    have = set(os.listdir(Config.pdf_dir))
    print("Database Size: %d \nNumber of current PDFs: %d" % (len(db), len(have)) )
    print("Number of entries not downloaded: %d" % int(len(db) - len(have)))
    entries = []
    numhtml = 0
    for db_key, j in db.items():
        pdfs = [x['href'] for x in j['links'] if x['type'] == 'application/pdf']
        assert len(pdfs) == 1
        if ('ishtml' in db[db_key] and db[db_key]['ishtml'] == True):
            numhtml = numhtml + 1
            #print(db_key)
            continue
        pdf_url = pdfs[0] + '.pdf'
        basename = pdf_url.split('/')[-1]
        fname = os.path.join(Config.pdf_dir, basename)
        if not basename in have:
            entries.append({
                'key': db_key,
                'url': pdf_url,
                'basename': basename,
                'filename': fname
            })
    print("Number of entries that only returned an HTML page: %d" % numhtml)
    print("Number of new entries to be downloaded: %d" % len(entries))
    return entries




def load_url(pdf_url):
    return session.get(pdf_url, timeout = 30)

def reqToFile(db_key, basename, filename, req):
    if ('ishtml' in db[db_key] and db[db_key]['ishtml'] == True):
        return
    if (req.ok and req.headers['Content-Type'] == 'application/pdf'):
        with open(filename, 'wb') as f:
            f.write(req.content)
        print(".", end='', flush=True)
    elif ('text/html' in req.headers['Content-Type']):
        db[db_key]['ishtml'] = True
        raise ValueError(f"{db_key}: was HTML instead of PDF")
    else:
        raise Exception(f"{db_key}: Unknown error")


batch_size = 2500
newEntries = refreshNeeded()
with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
    while(len(newEntries) > 0):
        batch = newEntries[0:batch_size]
        print("New batch, number of new entries to download: %d" % len(batch))
        future_to_url = { executor.submit(load_url, entry['url']): entry for entry in batch }
        for future in concurrent.futures.as_completed(future_to_url):
            if(random.randrange(0, 100) > 98):
                safe_pickle_dump(db, Config.db_path)
                print("Database saved.")
            try:
                this_entry = future_to_url[future]
                req = future.result()
                reqToFile(this_entry['key'], this_entry['basename'], this_entry['filename'], req)
            except Exception as e:
                print('')
                print(e)
                print('')
        printgreen('Batch done, saving database.')
        safe_pickle_dump(db, Config.db_path)
        newEntries = refreshNeeded()
        gc.collect()

print("Done, saving database.")
safe_pickle_dump(db, Config.db_path)
