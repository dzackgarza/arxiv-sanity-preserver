find . -name "*.pdf" -size -100k| while read f; do
  fp=`realpath $f`
  if ! pdfinfo "$fp" &> /dev/null; then
    echo "$fp is broken."
    rm $fp
  fi
done
