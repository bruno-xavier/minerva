import numpy as np
from imutils.perspective import four_point_transform
from imutils import contours
import cv2
import imutils
import csv
import math
import sys, getopt, os

class Sheet:
    def __init__(self, respostas = [], tipo = 'A', nota = -1, file_name = "", matricula = "",nome = ""):
        self.respostas = respostas
        self.tipo = tipo
        self.nota = nota
        self.file_name = file_name
        self.matricula = matricula
        self.nome = nome
    
    def grade(self, gabarito):
        pontos = 0
        try:
            index_tipo = ['A','B','C','D','E'].index(self.tipo)
            for i in range(len(self.respostas)):
                if gabarito[index_tipo][i] == self.respostas[i]:
                    pontos += 1
        except ValueError:
            self.getmatricula()
            print self.nome + ": tipo nao identificado"
        self.nota = pontos
        
    def getmatricula(self):
        inputImage = cv2.imread(self.file_name)        
        qrDecoder = cv2.QRCodeDetector()
        # Detect and decode the qrcode
        data,bbox,rectifiedImage = qrDecoder.detectAndDecode(inputImage)
        if len(data)>0:
            data = data.split(',')
            self.matricula = data[0]
            self.nome = data[1]
            #rectifiedImage = np.uint8(rectifiedImage);
            #cv2.imshow("Rectified QRCode", rectifiedImage);
        else:
            self.matricula = "-1"
            #cv2.imshow("Results", inputImage)

def showimg(img):
    cv2.imshow('imagem', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
def getanswers(ifile, show=False):
    img = cv2.imread(str(ifile),0)
    height, width = img.shape
    # perform the actual resizing of the image
    r = (height*1) / img.shape[0]
    dim = (int(img.shape[1] * r), int(height*1))
    img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 150)
    # find contours in the edge map, then initialize
    # the contour that corresponds to the document
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    guides = []
    minx, miny, maxx, maxy = dim[0],dim[1],0,0
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        ar_doc = w / float(dim[0])
        if (abs(ar-2) <= 0.5) and (y>=0.25*dim[1]) and ar_doc <= 0.15 :
            guides.append(c)
            if x <= minx:
                minx = x+w
            if y <= miny:
                miny = y+h
            if x+w >= maxx:
                maxx = x
            if y+h >= maxy:
                maxy = y
    guides_filtered = []
    for c in guides:
        (x, y, w, h) = cv2.boundingRect(c)
        if x == minx:
            guides_filtered.append(c)
        if y == miny:
            guides_filtered.append(c)
        if x+w == maxx:
            guides_filtered.append(c)
        if y+h == maxy:
            guides_filtered.append(c)
    guides_filtered = sorted(guides_filtered, key=cv2.contourArea, reverse=True)
    for g in guides_filtered:
        cv2.drawContours(img, [g], 0, (0,255,0), 3)
    vert_ratio = 0.6
    rect_minx = int(minx*vert_ratio + maxx*(1-vert_ratio)) 
    rect_maxx = maxx
    rect_miny = miny
    rect_maxy = maxy
    vertex = [[rect_minx,rect_miny],[rect_minx,rect_maxy],[rect_maxx,rect_miny],[rect_maxx,rect_maxy]]
    corners = np.array(vertex)
    docCnt = cv2.convexHull(corners)
    warped = four_point_transform(img, docCnt.reshape(4,2))
    edged = cv2.Canny(warped, 75, 160)
    thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    # find contours in the thresholded image, then initialize
    # the list of contours that correspond to questions
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    questionCnts = []
    # loop over the contours
    for c in cnts:
        # compute the bounding box of the contour, then use the
        # bounding box to derive the aspect ratio
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)

        # in order to label the contour as a question, region
        # should be sufficiently wide, sufficiently tall, and
        # have an aspect ratio approximately equal to 1
        if w >= 20 and h >= 20 and abs(ar-1) <= 0.25:
            questionCnts.append(c)
            #cv2.drawContours(warped, [c], 0, (0,255,0), 3)
    # sort the question contours top-to-bottom, then initialize
    # the total number of correct answers
    questionCnts = contours.sort_contours(questionCnts,method="top-to-bottom")[0]
    #if len(questionCnts) != 55:
    #    return [-2,-2,-2,-2,-2,-2,-2,-2,-2,-2] #erro de leitura
    marks = []
    index_to_char = ['A','B','C','D','E']
    # each question has 5 possible answers, to loop over the
    # question in batches of 5
    for (q, i) in enumerate(np.arange(0, len(questionCnts), 5)):
        whitelevel=[]
        cnts = contours.sort_contours(questionCnts[i:i + 5])[0]
        bubbled = None
        for (j, c) in enumerate(cnts):
            mask = np.zeros(thresh.shape, dtype="uint8")
            cv2.drawContours(mask, [c], -1, 255, -1)
            mask = cv2.bitwise_and(thresh, thresh, mask=mask)
            total = cv2.countNonZero(mask)
            whitelevel.append(total)
            if bubbled is None or total > bubbled[0]:
                bubbled = (total, j)
            maxwhite = max(whitelevel)
            minwhite = min(whitelevel)
        validmarks = 0
        for i in range(len(whitelevel)):
            ratio = (float(whitelevel[i])-minwhite)/maxwhite
            whitelevel[i]=math.trunc(100*ratio)
            if ratio >= 0.4:
                validmarks += 1
                cv2.drawContours(warped, [cnts[i]], 0, (0,255,0), 3)
        #print(whitelevel) #densidade de marcacao
        #if validmarks == 5: #em branco
        #    marks.append('X')
        if validmarks == 1: #marcacao valida
            marks.append(index_to_char[bubbled[1]])
        else: #marcacao multipla
            marks.append('X')
    if show==True:
        cv2.imshow(ifile, warped)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    result = Sheet(marks[1:], marks[0])
    return result

def grade(marks, gabarito):
    index_to_char = ['A','B','C','D','E']
    opt = index_to_char.index(marks[0])
    gabarito_opt = gabarito[opt]
    nota = 0
    for i in range(len(marks)):
        if marks[i+1] == gabarito_opt[i]:
            nota += 10./len(marks)
    return nota

def main(argv):
    gabarito = [['E','A','B','E','B','E','E','C','A','E'],['B','A','E','B','E','E','C','E','E','A'],['E','B','E','E','C','E','B','E','A','A'],['E','E','B','C','A','B','E','E','E','A'],['E','A','E','B','B','E','A','E','C','E']]
    #gabarito = [['A','B','C','D','E','A','B','C','D','E']]
    try:
        opts, args = getopt.getopt(argv, "i:sg", ["directory="])
    except getopt.GetoptError:
        sys.exit(2)
    show_image = False
    grade_test = False
    exams = []
    input_file = []
    for opt, arg in opts:
        if opt == '-i':
            input_file.append(arg)
        elif opt == "--directory":
            for filename in os.listdir(arg):
                if filename.endswith(".png"):
                    input_file.append(filename)
        if opt == '-s':
            show_image = True
        if opt == '-g':
            grade_test = True
    for arquivo in input_file:
        exam = getanswers(arquivo,show=show_image)
        exam.file_name = arquivo
        if grade_test:
            exam.grade(gabarito)
        exams.append(exam)
    return exams

if __name__ == "__main__":
    with open('report.csv', mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        for exam in main(sys.argv[1:]):
            exam.getmatricula()
            print "Nome: ", exam.nome , "\nMatricula: ", exam.matricula, "\nTipo: ", exam.tipo, "\nRespostas: ", exam.respostas, "\nNota: ", exam.nota, "\nArquivo: ", exam.file_name, "\n"
            csv_writer.writerow([exam.matricula, exam.nome, exam.nota])
