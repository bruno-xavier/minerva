# minerva
Minerva is an OMR program written in Python to grade exams. This is still in very early stages of development and in a very amateur fashion.

This was developed by me, a Mathematics Professor at IFB - Instituto Federal de Brasília, to aid myself
in grading paper while still using LaTeX to typeset mathematical symbols with precision, thus generating 
a high-quality question sheet. A software that does both - generate exams with LaTeX and grades using OMR -,
as far as I know, does not exist.

WHAT DOES THESE DO?:

There are 3 main programs.
- sheetgenerator.py: generates a LaTeX answer sheet and a question sheet provided by a csv file. Uses terminal pdflatex
to compile files. Output answer sheet includes a QR code featuring name and student number given by the csv file. Input
is given by templates 'FOLHADERESPOSTAS.tex' for answer sheets and 'QUESTOES.tex' for questions.

- convert.sh: bash script that batch converts any pdf files in current working directory to png files. Since most
batch scanners will scan files and save them as pdf, this is useful for converting it to png - a format that cv2 in omr.py
will recognize.

- omr.py: does the actual grading. Input is an image of the answered sheet. Grading is tailored to suit the specific
template provided in this repository. Attempts to use another template must be accompanied by fine tuning of the code.

This programs are licensed under GNU GPL 3.0.
