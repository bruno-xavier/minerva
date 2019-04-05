import qrcode
import csv
import os
import re
import random
from pdfrw import PdfReader, PdfWriter

class Question():
    def __init__(self, enunciado = """""", items = [], gabarito = ''):
        self.enunciado = enunciado
        self.gabarito = gabarito
        self.items = items
        self.whole = enunciado
        for i in items:
            self.whole += i
            
    def setwhole(self):
        if len(self.items) == 0:
            pattern = "\\\\item.*"
            items_re = re.compile(pattern)
            listaitems = items_re.findall(self.enunciado)
            self.enunciado, self.items = listaitems[0], listaitems[1:]
            self.whole = self.enunciado[:]
            for i in self.items:
                self.whole += i
        else:
            pass
            
    def shuffleitems(self, matricula):
        random.seed(matricula)
        random.shuffle(self.items)
        self.getgabarito()

    def getgabarito(self):
        self.setwhole()
        for i in range(len(self.items)):
            if "%gabarito" in self.items[i]:
                self.gabarito = ['A','B','C','D','E'][i]

    def getitems(self):
        self.items = []
        pattern = "\\\\item.*"
        items_re = re.compile(pattern)
        itemlist = items_re.findall(self.whole)
        for i in range(len(itemlist[1:])):
            self.items.append(itemlist[i])

class Exam():
    def __init__(self, text="""""",listaquestoes=[], gabarito = ['A','A','A','A','A','A','A','A','A','A']):
        self.text = text
        self.listaquestoes = listaquestoes
        self.gabarito = gabarito

    def gerargabarito(self):
        self.gabarito = []
        for questao in self.listaquestoes:
            self.gabarito.append(questao.gabarito)

    def shufflequestions(self, matricula):
        random.seed(matricula)
        random.shuffle(self.listaquestoes)
        self.gerargabarito()

    def getquestoes(self):
        self.listaquestoes = []
        q_pattern = re.compile(r"%qinicio.*?%qfim", re.M|re.DOTALL)
        rawquestoes = q_pattern.findall(self.text)
        for questao in rawquestoes:
            tempquestion = Question(questao)
            tempquestion.getgabarito()
            self.listaquestoes.append(tempquestion)
        self.gerargabarito()


with open("FOLHADERESPOSTAS.tex", "r") as f:
    template = f.read()
pdflist = []
fdrlist = []
fdqlist = []

with open("QUESTOES.tex", "r") as q:
    questoes = q.read()
    
csv_mime = [["123456789","Joao"],["987654321", "Maria"],["192837465","Jose"]]

def writedocument(matricula,nome):
    qrmatricula = "QR-" + matricula + ".png"
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q)
    qr.add_data(matricula)
    qr.add_data(','+nome)
    qr.make(fit=True)
    qr.make_image().save(qrmatricula)
    return template.replace("HEADNOME", nome).replace("HEADMATRICULA", matricula).replace("QRMATRICULA",qrmatricula) 

def gendocument(matricula, nome):
    content = writedocument(matricula, nome)[:]
    with open("FDR-" + matricula +".tex", "w+") as f:
        f.write(content)
    os.system("pdflatex -interaction nonstopmode FDR-" + matricula + ".tex")
    fdrlist.append("FDR-" + matricula + ".pdf")
    #os.system("convert -density 150 FDR-" + matricula +".pdf -quality 90 -background white -alpha off FDR-" matricula + ".png")

def writequestoes(matricula, nome):
    fdq = Exam(questoes)
    fdq.getquestoes()
    return questoes.replace("HEADNOME", nome).replace("HEADMATRICULA", matricula)

def genquestoes(matricula, nome):
    content = writequestoes(matricula, nome)[:]
    with open("FDQ-" + matricula +".tex", "w+") as f:
        f.write(content)
    os.system("pdflatex -interaction nonstopmode FDQ-" + matricula + ".tex")
    fdqlist.append("FDQ-" + matricula + ".pdf")

def movetex():
    listfiles = os.listdir('.')
    for filename in listfiles:
        if filename.endswith('.aux') or filename.endswith('.out') or filename.endswith('.log'):
            os.system("rm "+filename)
            #os.system("mv "+ filename+" ./aux/"+filename)
        elif filename.endswith('.pdf'):
            os.system("rm "+filename)
            #os.system("mv "+ filename+" ./pdf/"+filename)
        elif filename.endswith('.png'):
            os.system("rm "+filename)
            #os.system("mv "+ filename+" ./png/"+filename)
        elif filename[:3] == "FDR" and filename.endswith('.tex'):
            os.system("rm "+filename)

#with open('controle.csv') as csv_file:
#    csv_reader = csv.reader(csv_file, delimiter=',')
#    for row in csv_reader:
#        matricula = row[0]
#        nome = row[1]
#        gendocument(matricula,nome)

#with open('moveis.csv') as csv_file:
#    csv_reader = csv.reader(csv_file, delimiter=',')
#    for row in csv_reader:
#        matricula = row[0]
#        nome = row[1]
#        gendocument(matricula,nome)

for row in csv_mime:
    matricula = row[0]
    nome = row[1]
    gendocument(matricula, nome)
    genquestoes(matricula, nome)

writerfdr = PdfWriter()
writerfdq = PdfWriter()

for inpfn in fdqlist:
    writerfdq.addpages(PdfReader(inpfn).pages)

for inpfn in fdrlist:
    writerfdr.addpages(PdfReader(inpfn).pages)


movetex()

with open('resultfdq.pdf','w+') as outfn:
    writerfdq.write(outfn)


with open('resultfdr.pdf','w+') as outfn:
    writerfdr.write(outfn)

