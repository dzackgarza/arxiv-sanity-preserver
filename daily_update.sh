#!/bin/bash

set -e

. ~/.nvm/nvm.sh
. ~/dotfiles/.bash_colors

echo $(date +%x_%H:%M:%S:%N)
SECONDS=0

PROJROOT=/var/www/html/math-arxiv-sanity

$PROJROOT/fetch_papers.py
$PROJROOT/tor_download.py
#find $PROJROOT/data -size 0 -type f -delete
#$PROJROOT/tor_download.py
#find $PROJROOT/data -size 0 -type f -delete
#$PROJROOT/tor_download.py

find $PROJROOT/data -size 0 -type f -delete
find $PROJROOT/data/pdf -name "*.txt" -exec mv -t ./data/txt {} +

echo "Cleaning PDFs ---------------------------------------" && ./cleanpdf.py
echo "Parsing PDFs to Text --------------------------------" && ./parse_pdf_to_text.py

find $PROJROOT/data/pdf -name "*.txt" -exec mv -t ./data/txt {} +
find $PROJROOT/data -size 0 -type f -delete

echo "Creating thumbnails ---------------------------------" && ./thumb_pdf.py
echo "Analyzing -------------------------------------------" && ./analyze.py
echo "Building SVM ----------------------------------------" && ./buildsvm.py
echo "Making Cache ----------------------------------------" && ./make_cache.py
find $PROJROOT/data -size 0 -type f -delete

pm2 restart serve
echo "Finished." >> /home/zack/cronstatus.log
echo "$(date +%x_%H:%M:%S:%N)" >> /home/zack/cronstatus.log
echo "Hours to complete:" >> /home/zack/cronstatus.log
echo "$SECONDS / 3600" | bc -l  >> /home/zack/cronstatus.log
