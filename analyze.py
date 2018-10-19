#!/usr/bin/python3

"""
Reads txt files of all papers and computes tfidf vectors for all papers.
Dumps results to file tfidf.p
"""

import os
import sys
import pytz
import pickle
import datetime
import numpy as np
from random import shuffle, seed
from sklearn.feature_extraction.text import TfidfVectorizer
from utils import Config, safe_pickle_dump

tz = pytz.timezone('America/Los_Angeles')
sim_dict = {}
batch_size = 200
max_train = 500 # max number of tfidf training documents (chosen randomly), for memory efficiency
max_features = 5000
db = pickle.load(open(Config.db_path, 'rb'))
txt_paths, pids = [], []
n = 0
out = {}

analysis_errors= set([l.strip() for l in open("analysis_errors.txt").readlines()])
known_good_pdfs = set([l.strip() for l in open("known_good_pdfs.txt").readlines()])

def save():
    print("Now saving..")
    open("analysis_errors.txt", 'w').writelines([l + '\n' for l in list(analysis_errors)])
    safe_pickle_dump(sim_dict, Config.sim_path)

import signal
def signal_handler(sig, frame):
    save()
    print('Saved, now exiting')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

seed(1337)

toProcess = {key:db[key] for key in db.keys() if 'ishtml' not in db[key] or not db[key]['ishtml']}
print("Size of full database: %s" % len(db))
print("Size of valid entries: %s" % len(toProcess))

#for pid,j in db.items():
for pid,j in toProcess.items():
    n += 1
    idvv = '%sv%d' % (j['_rawid'], j['_version'])
    pdf_file_name = idvv + '.pdf'
    if not pdf_file_name in known_good_pdfs or pdf_file_name in analysis_errors: continue
    txt_path = os.path.join(Config.txt_dir, idvv) + '.pdf.txt'
    try:
        if not os.path.isfile(txt_path): raise Exception("Could not find file: %s" % txt_path)
        txt = open(txt_path, 'r').read()
        if len(txt) < 1000 or len(txt) > 500000:
            raise Exception("Skipped %d/%d (%s) with %d chars: suspicious amount of text." % (n, len(db), idvv, len(txt)))
        txt_paths.append(txt_path)
        pids.append(idvv)
    except Exception as e:
        print("Error reading file %s (%s)" % (txt_path, e))
        analysis_errors.add(pdf_file_name)
        continue

print("Read in %d text files out of %d db entries." % (len(txt_paths), len(toProcess)))
save()

v = TfidfVectorizer(input='content',
        encoding='utf-8', decode_error='replace', strip_accents='unicode',
        lowercase=True, analyzer='word', stop_words='english',
        token_pattern=r'(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b',
        ngram_range=(1, 2), max_features = max_features,
        norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=True,
        max_df=1.0, min_df=1)

# create an iterator object to conserve memory
def make_corpus(paths):
  for p in paths:
    with open(p, 'r') as f:
      try:
        txt = f.read()
      except Exception as e:
        with open("analyze.log", "a") as myfile:
          myfile.write("Error making corpus: %s\n" % p)
    yield txt

# train
train_txt_paths = list(txt_paths) # duplicate
shuffle(train_txt_paths) # shuffle
train_txt_paths = train_txt_paths[:min(len(train_txt_paths), max_train)] # crop
print("training on %d documents..." % (len(train_txt_paths), ))
train_corpus = make_corpus(train_txt_paths)
v.fit(train_corpus)

# transform
print("transforming %d documents..." % (len(txt_paths), ))
corpus = make_corpus(txt_paths)
X = v.transform(corpus)
print(v.vocabulary_)
print(X.shape)

# write full matrix out
out['X'] = X # this one is heavy!
print("writing", Config.tfidf_path)
safe_pickle_dump(out, Config.tfidf_path)

# writing lighter metadata information into a separate (smaller) file
out = {}
out['vocab'] = v.vocabulary_
out['idf'] = v._tfidf.idf_
out['pids'] = pids # a full idvv string (id and version number)
out['ptoi'] = { x:i for i,x in enumerate(pids) } # pid to ix in X mapping
print("writing", Config.meta_path)
safe_pickle_dump(out, Config.meta_path)

print("Precomputing nearest neighbor queries in batches...")

for i in range(0, len(pids), batch_size):
  print(datetime.datetime.now(tz))
  i1 = min(len(pids), i+batch_size)
  xquery = X[i:i1] # BxD
  ds = -(X.dot(xquery.T)).toarray() #NxD * DxB => NxB
  IX = np.argsort(ds, axis=0) # NxB
  for j in range(i1-i):
    sim_dict[pids[i+j]] = [pids[q] for q in list(IX[:50,j])]
  print('%d/%d...' % (i, len(pids)))

save()
