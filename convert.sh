#!/bin/bash
pattern="?*.pdf"
for file in *
do
	if [[ $file == $pattern ]]; then
		output=$(basename $file .pdf)
		pdftoppm $file $output -png
		#echo $file $output
	fi 
done
