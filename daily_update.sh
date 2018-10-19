#!/bin/bash

set -e

. ~/.bashrc
. ~/dotfiles/.bash_colors


clr_red $(date +%x_%H:%M:%S:%N)
SECONDS=0

./fetch_papers.py
./tor_download.py
find ./data -size 0 -type f -delete
./tor_download.py
find ./data -size 0 -type f -delete
./tor_download.py

find ./data -size 0 -type f -delete
find ./data/pdf -name "*.txt" -exec mv -t ./data/txt {} +

clr_green "Cleaning PDFs ---------------------------------------" && ./cleanpdf.py
clr_green "Parsing PDFs to Text --------------------------------" && ./parse_pdf_to_text.py

find ./data/pdf -name "*.txt" -exec mv -t ./data/txt {} +
find ./data -size 0 -type f -delete

clr_green "Creating thumbnails ---------------------------------" && ./thumb_pdf.py
clr_green "Analyzing -------------------------------------------" && ./analyze.py
clr_green "Building SVM ----------------------------------------" && ./buildsvm.py
clr_green "Making Cache ----------------------------------------" && ./make_cache.py
find ./data -size 0 -type f -delete

pm2 restart serve
clr_red $(date +%x_%H:%M:%S:%N)
clr_red $SECONDS
clr_green "DONE"
