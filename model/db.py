# -*- coding: utf-8 -*- 

#import pyodbc
import time
import string

# Класс модель, предназначен для работы с базой, с ботами из программы
class DB():
    def __init__(self, parent):
        self.model = parent
        # handle base
        self.__hb = None
		
        self.__hb = 2
        #self.connect()
        
    def connect(self):
    
        if not self.connectExist():
        
            try:
                botname, botpass, null = self.model.objEncryption.decoding( self.model.objConfig.get('database', 'bot') )
                
                con = 'DRIVER={' + self.model.objConfig.get('database', 'typedb')   + '};'\
                      'SERVER={' + self.model.objConfig.get('database', 'serverdb') + '};'\
                      'DATABASE={' + self.model.objConfig.get('database', 'namedb') + '};'\
                      'UID={' + botname  + '};'\
                      'PWD={' + botpass  + '}'
                       
                self.__hb = pyodbc.connect(con)
                self.model.objLoger.info(u'Успешное подключение к базе')
                
            except pyodbc.Error as msg:
                self.model.objLoger.critical(u'Не установленно соединение с базой, проверьте настроки соединения.')
            
    def disconnect(self):
        
        self.__hb = None
        
    def connectExist(self):
        
        return True if self.__hb is not None else False
    
    def existOcc(self, occ):
        
        # Проверяем есть ли заданный лицевой счет occ в базе
        # !!! Проверить с возвращающими аргументами, к примеру если не найден то поидее rows пустой и тогда от else: return False можно избавится т.к. len будет показывать 0
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = 'SELECT * FROM PEOPLE WHERE OCC_ID=' + str(occ)
            cursor.execute(sql)
            rows = cursor.fetchall()
            if(len(rows) >= 1): return len(rows)
            else: return 0
        
        
    def getDefaultSHF(self):
        
        # Возвращает дефолтную улицу дом и квартиру
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT TOP 1 NAME FROM STREETS WHERE ID != 30 GROUP BY NAME"
            cursor.execute(sql)
            street = cursor.fetchone()[0]
            house = self.getDefaultHouse(street)
            flat = self.getDefaultFlat(street, house)
            return street, house, flat
        
    def getDefaultHouse(self, street):
        
        # Для заданной улицы возвращает дом по умолчанию, т.е. первый элемент из списка
        return self.getListHouse(self.getIdStreet(street))[0]
        
    def getDefaultFlat(self, street, house):
        
        # Для заданной улицы и дома возвращаем квартиру по умолчанию, т.е. первый элемент из списка
        return self.getListFlat(self.getIdStreet(street), house)[0]
        
    def getListStreet(self):
        
        # Возвращаем список улиц, сортировка на уровне базы, т.к. нету цифровых обозначений, типа "7 улица строителей"
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT NAME FROM STREETS ORDER BY NAME"
            cursor.execute(sql)
            rows = cursor.fetchall()
            rows = [row[0] for row in rows]
            return rows
        
    def getListHouse(self, street_id):
        
        # По заданому id улицы возвращаем список домов
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT BLDN_NO FROM INFO_VIEW WHERE STREET_ID = " + str(street_id) + " GROUP BY BLDN_NO"
            cursor.execute(sql)
            rows = cursor.fetchall()
            rows = [row[0] for row in rows]
            #print "www: getListHouse: rows=" + str(rows)
            return self.getSortedListAddress(rows)
        
    def getListFlat(self, street_id, bldn_no):
        
        # По заданому id улицы и номеру дома возвращаем список квартир
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT FLAT_NO FROM INFO_VIEW WHERE STREET_ID = " + str(street_id) + " AND BLDN_NO = '" + bldn_no + "'"
            cursor.execute(sql)
            rows = cursor.fetchall()
            rows = [row[0] for row in rows]
            #print "www,in getListFlat, rows=" + str(rows)
            return self.getSortedListAddress(rows)
        
    def getIdStreet(self, street):
        
        # Возвращает id улицы для улицы заданной в текстовом формате
        if self.connectExist():
            cursor = self.__hb.cursor()
            #print "www, street=" + str(street)
            sql = "SELECT ID FROM STREETS WHERE NAME = '" + street + "'"
            cursor.execute(sql)
            row = cursor.fetchone()
            if row is not None:
                return row[0]
        
        
    def getSortedListAddress(self, rows):
        
        # надо определить есть ли в списке значения отличные от цифр, для этих целей воспользуемся множествами
        
        addr = set(''.join(rows))
        digit = set(string.digits)
        # Если есть буквы то в find будут содержаться элементы, тогда идем по сложной сортировке
        find = addr - digit
        
        if len(find) == 0:
            rows.sort(key=int)
            return rows
        else:
            res = [self.parseAddress(row) for row in rows]
            res.sort(key = lambda item: item[1]) # Сначала сортировка по буквам
            res.sort(key = lambda item: item[0]) # Затем сортировка по цифрам
            # Объединяем раздробленный массив
            res = [str(number) + char for number, char in res]
            return res
        
    def getOCCFIOFromADDRESS(self, street, house, flat):
        
        # Возвращает номер лицевого и фио по заданому id улицы(int), дому(str) и квартиры(str) 
        # [occ, ф, и, о]
        if self.connectExist():
            idStreet = self.getIdStreet(street)
            if idStreet is not None:
                cursor = self.__hb.cursor()
                sql = "SELECT TOP 1 FLAT_ID FROM INFO_VIEW WHERE STREET_ID = " + str(idStreet) + " AND BLDN_NO = '" + house + "' AND FLAT_NO = '" + flat + "'"
                cursor.execute(sql)
                row = cursor.fetchone()
                if row is not None:
                    flatID = row[0]
                    cursor = self.__hb.cursor()
                    sql = "SELECT TOP 1 OCC_ID, LAST_NAME, FIRST_NAME, SECOND_NAME FROM PEOPLE WHERE FLAT_ID = " + str(flatID)
                    cursor.execute(sql)
                    row = cursor.fetchone()
                    return [row[0], row[1].decode('cp1251'), row[2].decode('cp1251'), row[3].decode('cp1251')]
        
    def getFIOAddressFromOCC(self, occ):
        
        if self.connectExist():
            flatID = self.getFlatIDFromOccID(occ)
            
            cursor = self.__hb.cursor()
            sql = "SELECT TOP 1 NAME, BLDN_NO, FLAT_NO FROM INFO_VIEW WHERE FLAT_ID = " + str(flatID)
            cursor.execute(sql)
            
            row = cursor.fetchone()
            if row is not None:
                street = row[0]
                house = row[1]
                flat = row[2]
                
                cursor = self.__hb.cursor()
                f, i, o = self.getFIOFromOCC(occ)
                
                return (f.decode('cp1251'), i.decode('cp1251'), o.decode('cp1251'), street.decode('cp1251'), house.decode('cp1251'), flat.decode('cp1251'))
        
        
    def getAddressFromOCC(self, occ):
        
        # Возвращает строку адреса по заданному номеру лицевого счета
        if self.connectExist():
            flatID = self.getFlatIDFromOccID(occ)
            if flatID is not None:
                cursor = self.__hb.cursor()
                sql = "SELECT TOP 1 ADDRESS FROM INFO_VIEW  WHERE FLAT_ID = " + str(flatID)
                cursor.execute(sql)
                row = cursor.fetchone()
                if row is not None:
                    return row[0]
        
    def getFIOFromOCC(self, occ):
        # Возвращает фио [ф,и,о] для заданного лицевого счета
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT TOP 1 LAST_NAME, FIRST_NAME, SECOND_NAME FROM PEOPLE WHERE OCC_ID = " + str(occ)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row is not None:
                return [row[0], row[1], row[2]]

    def getFlatIDFromOccID(self, occ):
        # Возвращает id квартиры для заданного номера лицевого счета
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT TOP 1 FLAT_ID FROM PEOPLE WHERE OCC_ID = " + str(occ)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row is not None:
                return row[0]
    
    # Далее пойдут функции возвращающие списки отсортировнных адресов, и первые элементы списка (т.е. элементы по умолчанию)
    # getListStreet, getListHouse, getListFlat - списки
    # getDefaultSHF, getDefaultHouse, getDefaultFlat - вытащить первые (т.е. элементы по умолчанию которые отображаются в приложении)
        
    


    def getPeople(self, street_id, bldn_no, flat_no):
        
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT INITIALS, ADDRESS FROM INFO_VIEW WHERE STREET_ID =" + str(street_id) + " AND BLDN_NO = '" + bldn_no + "' AND FLAT_NO = '" + flat_no + "'"
            cursor.execute(sql)
            row = cursor.fetchone()
            if row is not None:
                row[0] + " " + row[1]
        
    def getListTypeTemplates(self):
        
        # Возвращает отсортированный список шаблонов определенных в базе
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT NAME FROM DIF_PAYINGS_TYPES GROUP BY NAME"
            cursor.execute(sql)
            return [row[0].strip().decode('cp1251') for row in cursor.fetchall()]
        
    def getIdTypePayment(self, namePayment):
        
        # Вернуть id для заданного шаблона
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = "SELECT REF_ID FROM DIF_PAYINGS_TYPES WHERE NAME ='" + namePayment + "'"
            cursor.execute(sql)
            return cursor.fetchone()[0]
        
    def intPrint(self, occ, template):
        
        # вернуть список меток со значениями для данного occ и типа шаблона
        # При возникновении ошибки, вероятнее всего запрашивается occ для другого типа шаблона
        
        if self.connectExist():
            cursor = self.__hb.cursor()
            sql = 'EXEC intPrint_2000 ' + str(occ) + ', ' + str(template)
            cursor.execute(sql)
            try:
                data = cursor.fetchall()[0]
                res = [ ( '<H' + str(index) + '>', row.rstrip().decode('cp1251') ) for index, row in enumerate(data, start = 1) if row is not None]
                return res
            except pyodbc.ProgrammingError:
                pass
                
    def addColourFioAddressToList(self, list, start, count):
        
        if self.connectExist():
            colour = self.model.objConfig.get('setting', 'mpSleep')
            
            for i in range(start, start+count):
                occ = list[i]
                
                # Достаем фио и id квартиры по лицевому счету
                cursor = self.__hb.cursor()
                sql = 'SELECT TOP 1 LAST_NAME, FIRST_NAME, SECOND_NAME, FLAT_ID  FROM PEOPLE WHERE OCC_ID = ' + str(occ)
                cursor.execute(sql)
                row = cursor.fetchone()
                
                if row is None:
                    self.model.objLoger.error(u'Произошла ошибка при просмотре списка лицевых счетов. А именно с лицевым счетом: ' + str(occ) + u' (он будет проигнорирован)')
                    continue
                
                if len(row) != 4:
                    self.model.objLoger.error(u'Произошла ошибка при запросе к базе, ожидается 4-х значное значение, а получено ' + str(len(row)) + u'-х. Лицевой счет: ' + str(occ) + u' будет пропущен. Обратитесь к программисту. ')
                    continue
                
                firstname = row[0].strip().decode('cp1251')
                name = row[1].strip().decode('cp1251')
                patronymic = row[2].strip().decode('cp1251')
                flatId = row[3]
                
                # Достаем адрес по id квартиры
                
                cursor = self.__hb.cursor()
                sql = 'SELECT NAME, BLDN_NO, FLAT_NO FROM INFO_VIEW WHERE FLAT_ID = ' + str(flatId)
                cursor.execute(sql)
                row = cursor.fetchone()
                
                if len(row) != 3:
                    self.model.objLoger.error(u'Произошла ошибка при запросе к базе, ожидается 3-х значное значение, а получено ' + str(len(row)) + u'-х. Лицевой счет: ' + str(occ) + u' будет пропущен. Обратитесь к программисту. ')
                    continue
                
                street = row[0].strip().decode('cp1251')
                streetN, streetC = self.parseAddress(street)
                    
                house = row[1].strip().decode('cp1251')
                houseN, houseC = self.parseAddress(house)
                
                flat = row[2].strip().decode('cp1251')
                flatN, flatC = self.parseAddress(flat)
                
                list[i] = [occ, colour, firstname, name, patronymic, streetN, streetC, houseN, houseC, flatN, flatC ]
             


    def parseAddress(self, name):
        
        # входная строка мб 23, 23б, 'иной текст без цифр'
        # на выходе получаем разделенные числа и буквы, если чисел нет то numbers='' если букв нет то subtype=''
        middle = 0
        char = False
        numbers = ''
        subtype = ''
        for i, v in enumerate(name):
            if v not in string.digits:
                middle = i
                char = True
                break
        if not char: numbers = int(name)
        else:
            if not middle: subtype = name
            else:
                numbers = int(name[:middle])
                subtype = name[middle:]
     	return numbers, subtype
             
         
    def parseAddress(self, name):
        
        # входная строка мб 23, 23б, 'иной текст без цифр'
        # на выходе получаем разделенные числа и буквы, если чисел нет то numbers='' если букв нет то subtype=''
        
        findChar = False
        numbers = ''
        subtype = ''
        
        for index, char in enumerate(name):
            if char not in string.digits:
                findChar = True
                break
        
        if not findChar: # только число
            numbers = name
        else:
            if not index: # только строка
                subtype = name
            else:
                numbers, subtype = name[:index], name[index:]
        
        if not numbers:
            numbers = 0
                
        return int(numbers), subtype
        
        # !!!! Проверить сортировку
        
        
        
    def sortListByFio(self, list):
        
        list.sort(key=lambda fio: fio[2])
        return list
    
    def sortListByOCC(self, list):
        
        list.sort(key=lambda occ: int(occ[0]))
        return list
        
        
    def sortListByAddress(self, list):
        
        # Сортировка квартиры
        list.sort(key=lambda flatC: flatC[9])
        list.sort(key=lambda flatN: flatN[8])
        # Сортировка дома
        list.sort(key=lambda houseC: houseC[7])
        list.sort(key=lambda houseN: houseN[6])
        # Сортировка улицы
        list.sort(key=lambda streetC: streetC[5])
        list.sort(key=lambda streetN: streetN[4])
        return list
