# -*- coding: utf-8 -*- 

import time

import logger
import encryption
import config
import db

import os
import string
import codecs

class Model():
    def __init__(self, logFile, configFile):
        
        # Предполагается что один коннект пользователя один объект модели
        # Модуль лога требует файл куда будет записываться сообщения, идентификатор сессии(текущее время), имя пользователя
        
        # Инициализация логгирования
        self.objLoger = logger.Logger(self, logFile, str(time.time()) )
        self.objLoger.start(u'бот')
        # Инициализация шифрования
        self.objEncryption = encryption.Encryption(self)
        
        # Инициализация конфигурации
        self.objConfig = config.Config(self, configFile)
        # Инициализация работы с базой
        self.objDB = db.DB(self)
        
    #def connect(self):
    #    return
    #    self.objDB = db.DB(self, self.objConfig.db)
    #    print "in model=" + str(self.objConfig.db)
        
    def generateFile(self, occ, template, setUserMarks = True, out = '.\\tmp\\temp.txt'):
        
        # Начинается процесс генерации файла для печати
        # Найдем файл шаблон с метками
        
        file = self.objConfig.get('templates', template).split('*')[0]
        
        if file and os.path.isfile(".\\templates\\" + file):
            with codecs.open('.\\templates\\' + file, 'r', 'utf-8') as hf:
                self.content = '\n'.join( line.rstrip('\n\r') for line in hf.readlines() )
        else:
            self.objLoger.error('При формировании документа не удалось найти файл ' + file + ' в папке .\\templates\\, который установлен был для "' + template + '"')
            return
        
        # Получаем результат процедуры intPrint_2000 в виде списка
        
        idTempalte = self.objDB.getIdTypePayment(template)
        marksDB = self.objDB.intPrint(occ, idTempalte)
        
        if not marksDB:
            self.objLoger.error(u'При формировании документа для ' + str(occ) + u' запрашивается данные из базы, но произошла ошибка. Вероятнее всего запрашивается не для той управляющей компании. ')
            return
        
        for index, (mark, value) in enumerate(marksDB):
            print mark[2:-1],
        
        if setUserMarks:
            
            userMarks = [ ('<M' + mark + '>', value.split('*')[1]) for mark, value in self.objConfig.items('userMarks') ]
            userMarks.sort( key = lambda x: int(x[0][2:-1]) )
        
        # Проверки сделаны, заменяем в контенте метки значениями из intPrint_2000
        
        # Для заданного диапазона удаляем для меток с a до b пробелы и тире строки
        a, b = 82, 130
        # Доделать здесь через bool тип!!!!!!!
        offset = 0
        barcode = ''
        for index, (mark, value) in enumerate(marksDB, 1):
            value = value.rstrip()
            # на 39 штрихкод зарезервирован исходя из документации инари
            if int(mark[2:-1]) == 39:
                barcode = value
                print 'mark = ' + mark + ', barcode:' + barcode
                continue
            
            # Начинаем извращение, т.к. программисты с инари слишком заняты чтоб подправить прогу сделаем это сами, а именно
            # Для меток с 82 по 130 меняем позиции вставок (offset), к примеру в базе есть 82 и 83, 84 - пустая, 85 => чтоб пустая строка 84
            # не оставалась пустой вставляем в это место значение 85-ой и т.д. до 130 (все это для экономии места на листе А4)
            if a <= int(mark[2:-1]) <= b:
                if value.replace('-','').strip():
                    self.pasteMark('<H' + str(int(mark[2:-1]) + offset) + '>', value)
                else:
                    offset -= 1
            else:
                self.pasteMark(mark, value)
            
        # Поскольку после извращенства с диапазоном 82-130 могут остаться не заполненые метки, то убираем их (обнуляем)
        
        for mark, value in marksDB[a:b]:
            self.pasteMark(mark, '')
            
        # Начало вставки меток из словаря управляющие коды. Поскольку вставляются управляющие коды (начальные значения аски)
        # то перекодируем на этом этапе весь текст с utf в cp1251. Так же и метку в cp1251 иначе не сможет найти в тексте
        # convertCode - для перевода из строки (десятичной системы счисления) в коды аски
            
        self.content = self.content.encode('cp1251')
        
        if setUserMarks:
            for mark, value in userMarks:
                self.pasteMark(mark.encode('cp1251'), self.convertCode(value))
        
        # Сгенерируем и вставим штрих код
        
        if barcode and setUserMarks:
            self.pasteBarcode(barcode)
        
        # Надо убрать знак $ указывающий на начало открытия метки
        
        self.content = self.content.replace('$', '')
        
        with open(out, 'w') as hf:
            hf.write(self.content)
        
        # Активируйте remove для удаления пустых строк в диапазоне [a-b]
        a = 43
        b = 64
        remove = True
        
        if remove:
            with open(out) as hf:
                content = hf.readlines()
            
            content = ''
            
            for index, line in enumerate(open(out)):
                if a <= index <= b:
                    if not line.strip():
                        continue
                content += line.rstrip() + '\n'
                
            with open(out, 'w') as hf:
                hf.write(content)
        
        return 1
        
    def pasteMark(self, mark, val):
        
        # Алгоритм следующий: находим метку mark в тесте и последующую открывающую скобку.
        # Если места достаточно для value, то вставляем, иначе обрезаем значение value
        
        lenMark = len(mark)
        lenValue = len(val)
        start = 0
        
        while 1:
            value = '$' + val
            
            lenContent = len(self.content)
            
            indexMark = self.content.find(mark, start)
            if indexMark == -1 : return 
            
            # По оставшейся строке находим < \n or $
            for index, char in enumerate( self.content[(indexMark + lenMark):], indexMark + lenMark):
                code = ord(char)
                if (code == 60 or code == 13 or code == 36):
                    break
            else:
                index = -1
                
            if index != -1:
                # Обрезать или не обрезать?
                if ( (index + 1 - indexMark) < lenValue):
                    value = value[: (index - indexMark - 2) ] + '?'
            
            start = index
            
            #Если вставляемое значение меньше метки, то дополняем пробелами
            while len(value) <= lenMark:
                value = value + " "
            
            self.content = self.content[0:indexMark] + value + self.content[indexMark+len(value)-1:]
            
    def convertCode(self, code):
        
        result = ''
        
        items = code.split(';')
        
        for item in items:
            item = item.strip()
            
            numbers = item.split(' ')
            
            for number in numbers:
                result += chr(int(number))
            result += ' '
        
        return result[:-1]
        
    def pasteBarcode(self, data):
        
        data, check = self.generateCheckCode(data)
        data += str(check)
        self.pasteMark('<BAR>'.encode('cp1251'), self.convertCode('27 16 66 33 67') + data.encode('cp1251'))
        
    def generateCheckCode(self, data):
        
        if len(data) != 30:
            print u"Ошибка в generateCheckCode, принято значение отличное от 30"
            return
        
        result = 105
        for i in range(15):
            result = result + (i+1) * int(data[i*2:(i+1)*2])
        result = result % 103
        if result/10 == 0: result = "0" + str(result)
        if int(result)/100 != 0:
            data, result = self.generateCheckCode(data[:26] + '0001')
        return data, result
        
    def GenerateBarCode(data):
        
        check = True
        
        if len(data) != 30:
            print u'Ошибка в GenerateBarCode, принято значение отличное от 30'
            return ''
        result = 105
        for i in range(15):
            result = result + (i+1) * int(data[i*2:(i+1)*2])
        result = result % 103
        if result/10 == 0: result = "0" + str(result)
        if int(result)/100 != 0:
            
            f = open('bags.txt', 'a')
            f.write('bag\n')
            f.close()
        
        if check:
            if result > 99:
                print "generate new barcode"
                data, result = GenerateBarCode(data[:26] + '0001')
            
        
        return data, result
        
        
    
        
    def getListOCCFromFile(self, filename):
        
        
        if os.path.isfile(filename):
            res = []
            
            with open(filename, 'r') as hf:
                res = [ line.strip() for line in hf.readlines() if line.strip() ]
            
            res = [ item for item in res if item.isdigit() ]
            
            return res
            
        else:
            self.objLoger.warning(u'Программа парсит файл "' + filename + u'", но данный файл не удается найти')
            
        
        

    
    
    def printing(self, printerUse):
        # Проверяем есть ли такой принтер
        
        data = [ row.split('*') for row in self.objConfig.options('printers') ]
        
        printer = ''
        server = ''
        for serverConfig, printerConfig in data:
            if printerConfig == printerUse:
                printer = printerConfig
                server = serverConfig
        
        print 'printer=' + printer
        print 'server=' + server
        
        if not (printer and server):
            self.objLoger.error(u'Послана команда печати документа на принтер: "' + printer + u'" но данный принтер не найден в программе, или не доступен сервер')
            return
        
        #if printer not in printers:
        #    self.objLoger.error(u'Послана команда печати документа на принтер: "' + printer + u'" но данный принтер не найден в программе.')
        #    return
        #else:
        #    index = printers.index(printer)
        #    server = self.objConfig.   printers[index][0]
            
            
        # Проверяем есть ли темп файл
        
        path = ".\\tmp\\temp.txt"
        
        if not os.path.isfile(".\\tmp\\temp.txt"):
            self.objLoger.error(u'Послана команда печати документа на принтер: "' + printer + u'" но файл печати temp.txt не найден в .\\tmp\\')
            return
        
        # Проверяем доступен ли выбранный принтер для печати
        
        status = int(self.objConfig.get('printers', server + '*' + printer).split('*')[-1])
        
        if not status:
            self.objLoger.error(u'Послана команда печати документа на принтер: "' + printer + u'" но принтер программно выключен. Включите принтер в настройках чтоб расспечатать документ.')
            return
        
        cmd = "print /d:\\\\" + server + "\\" +  printer + " " + path
        
        print "cmd=" + cmd
        
        #os.system(cmd)
        
        
    def arhive(self, occ):
        
        
        print "arhive " + occ
        
    def getTime(self, second):
        out, hour, min, sec = ["", "", "", ""]
        hour = second / 3600
        second = second % 3600
        min = second / 60
        second = second % 60
        sec = second % 60
        
        if hour: out = out + str(hour) + "h "
        if min: out = out + str(min) + "m "
        if sec: out = out + str(sec) + "s "
        return out
        
       

    def sortListByOCC(self, list):
        list.sort(key = lambda occ: int(occ[0]))
        return list
        
    def sortListByFio(self, list):
        list.sort(key = lambda fio: (fio[2], fio[3], fio[4]) )
        return list
    
    def sortListByAddress(self, list):
        list.sort(key = lambda row: (row[5], row[6], row[7], row[8], row[9], row[10]) )
        return list
        
        
        
        
        
        
        
        

def autorization(Login, Password):
    
    result64 = coding(Login, Password)
    listLP = []
    listLP.append('bc71827e0011bff2da8123bfdf1525a87ae31be096e84aace1d6bf832c4729d2')
    hf = open('autorization', 'r')
    for line in hf.readlines():
        listLP.append(line[:-1])
    return result64 in listLP


def SetData(OCC, type, template, dict):
    #try:
    #config = ConfigParser.RawConfigParser()
    #self.config.read('print.ini')
    
    if os.path.exists(template): print "template=" + str(template)
    else: print "template not exist"
    if os.path.exists(dict): print "dict=" + str(dict)
    else: print "dict not exist"
    
    
    cursor = hb.cursor()
    #print "OCC=" + str(OCC)
    #print "type=" + str(type)
    sql = 'EXEC intPrint_2000 ' + str(OCC) + ", " + str(type)
    
    row = cursor.execute(sql)

    f = open(template,'r')
    content = f.read()
    f.close()
    
    row = cursor.fetchone()
    for i in range(ini.countH):
        word = str(row[i]).strip()
        if i==38: SetBarCode(ini.metkaBar, word, dict)
        findStr = "<H" + str(i+1) + ">"
        content = parseStr(content, findStr, word)
    #except:
        #print 'Error query to sql'	
    dict = parseDict(ini.dirDict)
    for k, v in dict.iteritems():
        v = v.strip()
        k = '<' + k + '>'
        content = parseStr(content, k, v)
    #SetBarCode(ini.metkaBar, "barcode", dict)			
    content = content.replace("$","")
    #print "FINISH content"
    return content
    
def SetDataThirdOnOne(OCC, type, template, dict):
    print "in model get occ=" + str(OCC)
    
    return
    
    #try:
    #config = ConfigParser.RawConfigParser()
    #self.config.read('print.ini')
    
    if os.path.exists(template): print "template=" + str(template)
    else: 
        print "template[0] not exist"
        return
    if os.path.exists(dict): print "dict=" + str(dict)
    else: 
        print "dict[0] not exist"
        return
    
    content = ""
    for i in range(3):
        currentOCC = OCC[i]
        
        
    
        cursor = hb.cursor()
        #print "OCC=" + str(OCC)
        #print "type=" + str(type)
        sql = 'EXEC intPrint_2000 ' + str(currentOCC) + ", " + str(type)
    
        row = cursor.execute(sql)

        f = open(template,'r')
        contentTemp = f.read()
        f.close()
    
        row = cursor.fetchone()
        for i in range(ini.countH):
            word = str(row[i]).strip()
            if i==38: SetBarCode(ini.metkaBar, word)
            findStr = "<H" + str(i+1) + ">"
            #print "before parse: findStr=" + str(findStr) + ", and word=" + str(word) 
            contentTemp = parseStr(contentTemp, findStr, word)
            #if i == 2:
            #    break
            #print "CONTENT TEMP=" + str(contentTemp)
        #except:
            #print 'Error query to sql'	
        content = content + contentTemp
        #print "iteration CONTENT=" + str(content)
        
    
        
    dict = parseDict(dict)
    for k, v in dict.iteritems():
        v = v.strip()
        k = '<' + k + '>'
        content = parseStr(content, k, v)
    SetBarCode(ini.metkaBar, "barcode")			
    content = content.replace("$","")
    #print "FINISH content"
    return content
    
    
    
    


def SetBarCode(metka, newText, dict):
    #print "SetBarCode newText=" + str(newText) + ",metka=" + str(metka)
    hf = open(ini.dirDict, 'r')
    text = ""
    for line in hf.readlines():
        memory = line
        if (line.find(metka) != -1):
            data, result = GenerateBarCode(newText)
            text = text + metka + "=" + str(data) + str(result) + "\n"
            #print "SetBarCode text=" + str(text)
        else: text = text + line
    hf.close()
    hf = open(ini.dirDict,'w')
    hf.write(text)
    #print text
    hf.close()
    
    
def GenerateBarCode(data):
    check = True
    
    #print "data(in GenerateBarCode)=" + str(data)
    if len(data) != 30:
        print u"Ошибка в GenerateBarCode, принято значение отличное от 30"
        return ""
    result = 105	
    for i in range(15):
        result = result + (i+1) * int(data[i*2:(i+1)*2])
    result = result % 103
    #print "check code: " + str(result)
    if result/10 == 0: result = "0" + str(result)
    if int(result)/100 != 0:
        f = open('bags.txt', 'a')
        f.write('bag\n')
        f.close()
        
    print "OUT BAR STRING (CHECK CODE):" + str(result)
    
    if check:
        if result > 99:
            print "generate new barcode"
            data, result = GenerateBarCode(data[:26] + '0100')
        
    
    return data, result
    
def parseDict(pathDict):
    hf = open(pathDict,'r')
    result = dict()
    find = '='
    try:
        for line in hf.readlines():
            index = line.find(find)
            result[line[0:index]] = line[index+1:-1]
    except: print "Error in doctionary file"
    hf.close()
    return result
    
def addFioAddressToList(list):
    #print "list=" + str(list)
    
    for index in range(len(list)):
        cursor = hb.cursor()
        sql = 'SELECT TOP 1 LAST_NAME, FIRST_NAME, SECOND_NAME, FLAT_ID  FROM PEOPLE WHERE OCC_ID = ' + str(list[index][0])
        cursor.execute(sql)
        row = cursor.fetchone()
        
        fio = str(row[0]).strip()
        name = str(row[1]).strip()
        if name: fio += " " + name[:1] + "."
        patronymic = str(row[2]).strip()
        if patronymic: fio += " " + patronymic[:1] + "."
        
        list[index].append(fio)
        list[index].append(str(row[3]))
        #print "fio(" + str(index) + ")=" + str(fio)
        #list[index].append(str(row[0]).strip())
        #list[index].append(str(row[1]).strip())
        #list[index].append(str(row[2]).strip())
        #list[index].append(str(row[3]))
        
        cursor = hb.cursor()
        sql = 'SELECT NAME, BLDN_NO, FLAT_NO FROM INFO_VIEW WHERE FLAT_ID = ' + list[index][3]
        #print "sql" + str(sql)
        
        cursor.execute(sql)
        row = cursor.fetchone()
        
        # Предположительно у улиц домов и квартир, могут быть только числа, числа и буквы или только буквы
        # поэтому применяя parseAddress разделяем на составляющие для упрощения дальнейшей сортировки адресов
        streetN, streetC = parseAddress(str(row[0]).strip())
        list[index].append(streetN)
        list[index].append(streetC)
        
        houseN, houseC = parseAddress(str(row[1]).strip())
        list[index].append(houseN)
        list[index].append(houseC)
        
        flatN, flatC = parseAddress(str(row[2]).strip())
        list[index].append(flatN)
        list[index].append(flatC)
        
    
    #return list
    
    #list.sort(key=lambda flat: flat[8])
    #list.sort(key=lambda subTypeBuild: subTypeBuild[10])
    #list.sort(key=lambda build: build[9])
    #list.sort(key=lambda street: street[6])
    
    #for i in range(len(list)):
        #print "i(" + str(i) + ")=" + str(list[i])
        #print str(list[i][10]) + "\n"
    #print "list (end addFioAddressToList)=" + str(list)
    return list
    
def parseAddress(name):
    # входная строка мб 23, 23б, пустующая
    # на выходе получаем разделенные числа и буквы, если чисел нет то numbers='' если букв нет то subtype=''
    
    findChar = False
    numbers = ''
    subtype = ''
    
    for index, char in enumerate(name):
        if char not in string.digits:
            findChar = True
            break
    
    if not findChar: # только число
        number = int(name)
    else:
        if not index: # только строка
            subtype = name
            
        else:
            numbers = int(name[:index])
            subtype = name[index:]
    return numbers, subtype
    
    

    


    

    
    
    
    
    

    
def generateUserName():
    name = ''
    while len(name) != 10:
        code = random.randint(33,255)
        # Исключаем символы '#', ':', '='
        if code == 35 or code == 58 or code == 61: continue
        else:
            simbol = chr(code)
            name = name + simbol
        
    return name
    
    
# testing functions:

def getBadOcc(file):
    

    for occ in open(file):
        cursor = hb.cursor()
        
        sql = 'EXEC intPrint_2000 ' + str(occ) + ", " + str(47)
    
        row = cursor.execute(sql)
        row = cursor.fetchone()
        #print "occ = " + str(occ)
        bartemp = str(row[38])
        #print "DATA=" + bar
        
        data, bar = GenerateBarCode(bartemp)
        
        #print "CODE=" + str(bar)
        bar = int(bar)
        
        if bar > 99:
            print "FIND OCC =" + str(occ)
            print "BAR CODE =" + str(bartemp)
            print "CHECKcode=" + str(bar)
            print "\n\n"
        
        
        
        #print "occ=" + str(occ) + "row[38]=" + str(row[38])
        timer.sleep(0.1)
    print "finish"

    

if __name__ == '__main__':
    Model('MatrixPrinter.log', '../config.ini')