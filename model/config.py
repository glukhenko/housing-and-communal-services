# -*- coding: utf-8 -*- 

import ConfigParser
import os
import copy
import locale
import codecs


class Config(ConfigParser.RawConfigParser):
    # Изменен родительский, для употребления utf-8
    
    def __init__(self, parent, file, *args, **kwargs):
        ConfigParser.RawConfigParser.__init__(self, *args, **kwargs)
        
        self.model = parent
        self.__configFile = file
        
        if not os.path.isfile(self.__configFile):
            self.model.objLoger.critical(u'Не найден конфигурационный файл "' + self.__configFile + u'". Программа завершает свою работу.')
            self.model.objLoger.finish()
            exit(1)
        
        with codecs.open(self.__configFile, 'r', 'utf-8') as hf:
            try:
                self.readfp(hf)
            except ConfigParser.ParsingError as msg:
                temp = msg.args[0]
                print 'args=' + temp
                print 'msg = ' + msg.message
                
                self.model.objLoger.critical(u'Проблемы при чтении конфигурационного файла "' + self.__configFile + u'". Программа завершает свою работу.')
                self.model.objLoger.finish()
                exit(1)
        
    def write(self, fp):
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, unicode(value).replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            
            # отсортируем данные секции, т.к. хранятся в словаре
            data = self._sections[section].items()
            data.sort( key = lambda x: x[0].lower() )
            if section in ['userMarks', 'intPrint2000']:
                data.remove( ('__name__', section))
                
                data.sort( key = lambda x: int(x[0]) )
                data.append( ('__name__', section) )
            
            for (key, value) in data:
                if key != "__name__":
                    fp.write("%s = %s\n" %
                             (key, unicode(value).replace('\n','\n\t')))
            fp.write("\n")
        
    def optionxform(self, strOut):
        
        return strOut
    
    def save(self):
        with codecs.open('config.ini', 'w', 'utf-8') as hf:
            self.write(hf)
        
    def autorization(self, login, psw):
        
        # Безопасный логин и пароль
        safe = u"629a21e000000000002Ыйyкgvс'1?ТZj;Ь4ПC>78FkfНjжияННUCAгПФbОqеяИ8y_Aъxыѓu9Л0НЛЧЯU{dk11"
        safeLogin, safePsw, safeStatus = self.model.objEncryption.decoding(safe)
        # Безопасный ли режим входа?
        if (safeLogin == login) & (safePsw == psw):
            return safeStatus
        # Проверяем всех пользователей в конфиге
        
        users = [ self.model.objEncryption.decoding(value) for key, value in self.items('users') ]
        
        for clogin, cpsw, cstatus in users:
            if (clogin == login) & (cpsw == psw):
                return cstatus
    
    def parseIntPrint2000(self):
        
        # Поскольку в списке мб диапазон (10...23) т.е. 10 потом 23 то небоходимо проверять разницу соседних, чтоб присводить диапазону одно и то же значение
        
        data = self.items('intPrint2000')
        data.sort( key = lambda x: int(x[0]) )
        
        result = {}
        prevItem = 0
        prevValue = ''
        for item, value in data:
            item = int(item)
            if item != prevItem + 1:
                for i in range(prevItem+1, item):
                    result['<H' + str(i) + '>'] = prevValue
            
            result['<H' + str(item) + '>'] = value
            prevItem = item
            prevValue = value
        
        return result
        
    def getIdUser(self, user, password, status):
        
        users = self.items('users')
        for index, value in users:
            cuser, cpassword, cstatus = self.model.objEncryption.decoding(value)
            if user == cuser and password == cpassword and status == cstatus:
                return index
                
        
    #------------------------------------------------------------------------------------------
    
  #  def __init__(self, parent, file):
  #      
  #      self.model = parent
  #      self.__configFile = file
  #      
  #      #print "file=" + str(file)
  #      if not os.path.isfile(file):
  #          #print "Error in model.config in __init__ - not find file config " + file
  #          self.model.objLoger.critical(u'Не найден конфигурационный файл "' + self.__configFile + u'". Программа завершает свою работу.')
  #          exit(1)
  #          
  #      
  #      self.hc = ConfigParser.RawConfigParser()
  #      
  #      try:
  #          self.hc.read(self.__configFile)
  #      except ConfigParser.ParsingError, msg:
  #          self.model.objLoger.critical(u'Возникла критическая ошибка при распарсивании конфигурационного файла "' + msg.filename + '"')
  #          
  #          for index, err in enumerate(msg.errors):
  #              self.model.objLoger.critical(u'Ошибка ' + str(index) + u': строка:' + str(err[0]) + u', значение: ' + err[1])
  #          self.model.objLoger.critical(u'Программа завершает свою работу.')
  #          self.model.objLoger.finish()
  #          exit(1)
  #      
  #      
  #      # [[templateDB, template, dict, status], [...], ...]
  #      #self.templatesdb = self.getTemplatesDB()
  #      self.templatesdb = self.parseSection('templatesdb', 3)
  #      #print "self.templatesdb=" + str(self.templatesdb)
  #      
  #      
  #      # [[templatenolinks, template, dict, status], [...], ...]
  #      self.templatesuser = self.parseSection('templatesuser', 3)
  #      #print "self.templatesuser=" + str(self.templatesuser)
  #      
  #      
  #      # [[NamePrinter, NameServer, speed, status], [...], ...]
  #      self.printers = self.parseSection('printers', 4)
  #      
  #      
  #      
  #      
  #      # [[login,pass,status], [...], ...]
  #      self.users = self.parseSection('users', 1)
  #      #print "self.users=" + str(self.users)
  #      
  #      for index, data in enumerate(self.users):
  #          print '[' + str(index) + '] = ' + '|'.join(data)
  #      
  #      
  #      
  #      #print "--" * 20
  #      # {'namedb':'...', 'serverdb':'...', 'botname':'...', 'botpass':'...'}
  #      self.db = self.parseDataBase()
  #      
  #      for key, value in self.db.items():
  #          print '[' + key + '] = ' + value
  #      
  #      
  #      # {'colour' : ...}
  #      self.settings = self.parseSetting()
  #      
  #      self.intPrint2000 = self.parseIntPrint2000()
  #      
  #      self.userMarks = self.parseUserMarks()
  #      
  #      self.csv = self.parseCsv()
  #      
  #      
  #      self.csvData = self.parseCsvData()
  #      
  #      for item in self.csvData:
  #          print item
        
    #def parseSection(self, section, count):
    #    # Здесь парсятся секции конфиг файла представлющие из себя список
    #    self.model.objLoger.info(u'Загрузка ' + section + u' из файла "' + self.__configFile + '" ...')
    #    if not self.hc.has_section(section):
    #        self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" не найдена секция [' + section + '].')
    #        return []
    #    else:
    #        numbers = self.hc.options(section)
    #        
    #        if not numbers:
    #            self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" в секции [' + section + u'] не найдено ни одного элемента.')
    #        
    #        numbers.sort(key = int)
    #        
    #        if count == 1:
    #            # Для обработки секции с зашифрованными пользователями
    #            resrveUser = set()
    #            result = []
    #            
    #            for item in numbers:
    #                row = self.hc.get(section, item).decode('utf-8')
    #                data = self.model.objEncryption.decoding(row)
    #                if data[0] not in resrveUser:
    #                    resrveUser.add(data[0])
    #                    
    #                    result.append(data)
    #            
    #     #       result = [ self.hc.get(section, item).decode('utf-8') for item in numbers ]
    #            
    #     #       result = [ self.model.objEncryption.decoding(item) for item in result ]
    #        else:
    #            result = []
    #            for id in numbers:
    #                
    #                value = self.hc.get(section, id).split('*')
    #                
    #                # Надо как то строковые значения перевести из utf8 в юникод
    #                temp = []
    #                for val in value:
    #                    try:
    #                        int(val)
    #                        temp.append(val)
    #                    except ValueError:
    #                        temp.append(val.decode('utf-8'))
    #                    
    #                # Если расспарсиваются секции [templatesdb] или [templatesuser] то там в качестве второго параметра устанавливается адрес файла шаблона
    #                # По хорошему проверяем есть ли данный файл в момент запуска программы указанный в конфиг файле. Если вдруг нет то обнуляем значение в конфиге.
    #                
    #                if (section == 'templatesdb' or section == 'templatesuser'):
    #                
    #                    if temp[1] != '0':
    #                        if not os.path.isfile('.\\templates\\' + temp[1]):
    #                            
    #                            text = u'Шаблон "' + temp[0] + u'" связан с файлом "' + temp[1] + u'". Этот файл не был найден в папке templates поэтому убираем связку шаблона с файлом в конфигурационном файле. Связку на существующий файл можно установить через программу: Настройки -> Шаблоны печати'
    #                            self.model.objLoger.error(text)
    #                            temp[1] = '0'
    #                            
    #                            if temp[2] == '1':
    #                                temp[2] = '0'
    #                    elif temp[1] == '0' and temp[2] == '1':
    #                        temp[2] = '0'
    #                
    #                
    #                if len(temp) == count:
    #                    result.append(temp)
    #                else:
    #                    text = u'В конфигурационном файле для шаблона была найдена неформатная запись: '
    #                    value = [ val.decode('utf-8') for val in value]
    #                    text += '*'.join(value)
    #                    text += u'. Для данной секции установленно ' + str(count) + u' значения !!! проверить удаление после создания диструктора для конфигурационного файла'
    #                    self.model.objLoger.error(text)
    #                
    #                
    #                
    #                
    #                
    #        self.model.objLoger.info(u'Количество загруженных элементов для ' + section + u': ' + str(len(result)) + u' шт.')
    #        return result
        
    #def parseDataBase(self):
    #    
    #    if not self.hc.has_section('database'):
    #        self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" не найдена секция [database].')
    #    else:
    #        data = self.hc.items('database')
    #        data = dict(data)
    #        
    #        for key, value in data.items():
    #            data[key] = value.decode('utf-8')
    #            
    #        # Статус нам не важен, поэтому обрезаем до 2-х элементов список
    #        
    #        data['botname'], data['botpass'] = self.model.objEncryption.decoding(data['bot'])[:2]
    #        data.pop('bot')
    #        return data
        
    #def parseSetting(self):
    #    if not self.hc.has_section('setting'):
    #        self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" не найдена секция [setting].')
    #    else:
    #        data = self.hc.items('setting')
    #        return dict(data)
        
    #def parseIntPrint2000(self):
    #    if not self.hc.has_section('intprint2000'):
    #        self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" не найдена секция [intprint2000].')
    #    else:
    #        data = self.hc.items('intprint2000')
    #        data.sort(key = lambda x: int(x[0]))
    #        
    #      #  for key, item in data:
    #      #      print item
    #        
    #        
    #        
    #        # Поскольку в списке мб диапазон (10...23) т.е. 10 потом 23 то небоходимо проверять разницу соседних, чтоб присводить диапазону одно и то же значение
    #        
    #        result = {}
    #        prevItem = 0
    #        prevValue = ''
    #        for item, value in data:
    #            item = int(item)
    #            value = value.decode('utf-8')
    #            if item != prevItem + 1:
    #                for i in range(prevItem+1, item):
    #                    result["<H" + str(i) + ">"] = prevValue
    #            
    #            result["<H" + str(item) + ">"] = value
    #            
    #                
    #            prevItem = item
    #            prevValue = value
    #            
    #        return result
        
    #def parseUserMarks(self):
    #    if not self.hc.has_section('usermarks'):
    #        self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" не найдена секция [usermarks].')
    #    else:
    #        data = self.hc.items('usermarks')
    #        
    #        result = {}
    #        for key, value in data:
    #            items = value.split('*')
    #            
    #            if len(items) != 2:
    #                self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" ошибка чтения, элемент с номером ' + str(key) + u' не был распознан.')
    #                continue
    #            else:
    #                result['<M' + str(key) + '>'] = ( items[0].decode('utf-8'), items[1].decode('utf-8') )
    #                
    #        return result
            
            
        
    
        
        
        
        
    
    
        
        
        
        
    def getPrinters(self):
        
        if not self.hc.has_section('printers'):
            print "Error in model.config in getPrinters - not exist section printers"
        else:
            printersID = self.hc.options('printers')
            printersID.sort(key = int)

            return [self.hc.get('printers', id).split('*') for id in printersID]
        
    def getUsers(self):
        
        if not self.hc.has_section('users'):
            print "Error in model.config in getPrinters - not exist section users"
        else:
            usersID = self.hc.options('users')
            usersID.sort(key = int)
            
            result = []
            for id in usersID:
                str = self.hc.get('users', id).split('*', 1)[0]
                res = self.model.objEncryption.decoding(str)
                # Если получилось дешифровать то добавляем в список, иначе в будующем удаляем данную запись из файла
                if res is not None:
                    log, psw, status = res
                    result.append([log, psw, status])
            return result   
    
    #def getStatusOfUser(self, user):
    #    
    #    users = [usr[0] for usr in self.users]
    #    if user in users:
    #        return self.users[users.index(user)][2]

    #def delUser(self, user):
    #    
    #    users = [usr[0] for usr in self.users]
    #    if user in users:
    #        self.users.pop(users.index(user))
    #        self.saveConfigData()
    #        return True
    
    #def hasUser123(self, login, psw):
    #    
    #    # Переписать функцию т.к. используется для авторизации, а не для проверки юзера в системе
    #    print "log=" + str(self.users)
    #    print "hasUser, login=" + str(login) + ", psw=" + str(psw)
    #    # Если пользователь существует возвращаем 0 иначе строку информации
    #    users = [user[0] for user in self.users]
    #    print "users=" + str(users)
    #    if login in users:
    #        index = users.index(login)
    #        if self.users[index][1] == psw:
    #            return 0
    #        else:
    #            return 'Пароль введен не правильно'
    #    else:
    #        return 'Пользователь ' + str(login) + ' не найден'
    
        

    
    #def addUser(self, login, psw, status):
    #    if not self.hasUser(login):
    #        self.users.append([login, psw, status])
    #        self.saveConfigData()
            
    #def changePropertiesUser(self, user, newUser, psw, status):
    #    users = [usr[0] for usr in self.users]
    #    if user in users:
    #        index = users.index(user)
    #        self.users[index] = [newUser, psw, status]
    #        print "after update, users=" + str(self.users)
    #        self.saveConfigData()
    
    #def getStatusUser(self, user):
    #    users = [user[0] for user in self.users]
    #    return self.users[users.index(user)][2]
        
    #def getDataBase(self):
    #    if not self.hc.has_section('database'):
    #        print "Error in model.config in getDataBase - not exist section database"
    #    else:
    #        data = self.hc.items('database')
    #        data = dict(data)
    #        
    #        temp = data['bot'].decode('cp866')
    #        
    #        print u'Бот:' + temp + '\n\n'
    #        
    #        with open('ouut.txt', 'w') as hf:
    #            hf.write(temp.encode('utf-8'))
    #        
    #        print u'Нормально'
    #        
    #        #print "data=" + str(data)
    #        # Статус нам не важет, поэтому обрезаем до 2-х элементов
    #        res = self.model.objEncryption.decoding(data['bot'])
    #        #print "res=" + str(res)
    #        data['botname'], data['botpass'] = self.model.objEncryption.decoding(data['bot'])[:2]
    #        data.pop('bot')
    #        return data
            
    #def getSetting(self):
    #    if not self.hc.has_section('setting'):
    #        print "Error in model.config in setting - not exist section database"
    #    else:
    #        data = self.hc.items('setting')
    #        return dict(data)
    
    #def AppendItemsToListTemplateDB(self, names):
    #    
    #    for name in names:
    #        self.templatesdb.append([name, '0', '0'])
    #        
    #    self.templatesdb.sort(key = lambda item: item[0])
    #    
    #    
    #def RemoveItemsFromListTemplateDB(self, names):
    #    
    #    templates = [ template[0] for template in self.templatesdb ]
    #    indexes = [ index for index, value in enumerate(templates) if value in names ]
    #    indexes.sort(reverse = True)
    #    
    #    # Удаляем с конца, неохота возиться с копией списка
    #    for index in indexes:
    #        self.templatesdb.pop(index)
        
        
    def compareTemplatesList(self):
        
        # Функция сравнивает списки шаблонов в базе и в конфигурационном файле программы, на наличие изменений
        # Возвращает None если изменений не было, иначе [AddTemplate, RemoveTemplate], где AddTemplate и RemoveTemplate списки, один из которых может быть пустым.
        
        templatesConfig = self.model.objConfig.options('templates')
        
        templatesConfig = set(templatesConfig)
        templatesDB = self.model.objDB.getListTypeTemplates()
        templatesDB = set(templatesDB)
        
        AddTemplate = []
        RemoveTemplate = []
        
        result = templatesConfig ^ templatesDB
        if len(result):
            print '___result=' + str(len(result))
            for template in result:
                if template in templatesDB:
                    AddTemplate.append(template)
                else:
                    RemoveTemplate.append(template)
                    
            # Удаляем из списка шаблонов (из конфигурации)
            for templ in RemoveTemplate:
                self.remove_option('templates', templ)
            
            for templ in AddTemplate:
                self.set('templates', templ, '*0')
            
            self.save()
            return [AddTemplate, RemoveTemplate]
    
    #def parseCsv(self):
    #    
    #    if not self.hc.has_section('csv'):
    #        self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" не найдена секция "csv".')
    #        data = {}
    #    else:
    #        data = self.hc.items('csv')
    #    return dict(data)
    #    
    #    
    #def parseCsvData(self):
    #    
    #    res = []
    #    if not self.hc.has_section('csvdata'):
    #        self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" не найдена секция "csvdata".')
    #    else:
    #        
    #        data = self.hc.items('csvdata')
    #        print u'При распарсивании порядок следующий:' + str(data)
    #        for out, row in data:
    #            temp = row.split('*')
    #            if len(temp) != 4:
    #                self.model.objLoger.error(u'В конфигурационном файле "' + self.__configFile + u'" ошибка чтения, элемент с номером ' + str(out) + u' не был распознан в секции csvdata.')
    #                continue
    #            else:
    #                name, idCsv, width, align = temp
    #                res.append([name.decode('utf-8'), idCsv, width, align.decode('utf-8'), out])
    #                res.append([name.decode('utf-8'), idCsv, width, align.decode('utf-8')])
    #                
    #    res.sort(key = lambda x: int(x[4]))
    #    return res
        
        
    
    
    
    #def save(self):
    #    # Пробегаемся по секциям [templatesdb], [templatesuser], [printers], [users], [database], [setting], [intPrint2000]
    #    content = ""
    #    
    #    # Заносим [templatesdb] 
    #    content += "[templatesdb]\n"
    #    for index, item in enumerate(self.templatesdb, start = 1):
    #        content += str(index) + " = " + "*".join(item) + "\n"
    #        
    #    # Заносим [templatesuser]
    #    content += "\n[templatesuser]\n"
    #    for index, item in enumerate(self.templatesuser, start = 1):
    #        content += str(index) + " = " + "*".join(item) + "\n"
    #        
    #    # Заносим [printers] 
    #    content += "\n[printers]\n"
    #    for index, item in enumerate(self.printers, start = 1):
    #        content += str(index) + " = " + "*".join(item) + "\n"
    #        
    #    # Заносим [users] 
    #    content += "\n[users]\n"
    #    for index, item in enumerate(self.users, start = 1):
    #        print "index=" + str(index)
    #        sequence = self.model.objEncryption.coding(*item)
    #        content += str(index) + " = " + sequence + "\n"
    #        
    #    # Заносим [database] в определенном порядке
    #    content += "\n[database]\n"
    #    database = ['typedb', 'namedb', 'serverdb', 'bot']
    #    db = copy.deepcopy(self.db)
    #    db['bot'] = self.model.objEncryption.coding(db['botname'], db['botpass'], u'Администратор')
    #    db['bot'] = db['bot']
    #    db.pop('botname')
    #    db.pop('botpass')
    #    
    #    for data in database:
    #        content += str(data) + " = " + db[data] + "\n"
    #        
    #    # Заносим [setting] 
    #    content += "\n[setting]\n"
    #    
    #    settings = ['colour',
    #                'popupBackColour', 
    #                'popupTopColour',
    #                'colourInfoText',
    #                'mpSleep',
    #                'mpNext',
    #                'mpGo',
    #                'mpDone',
    #                'mpMouse',
    #                'icon',
    #                'iconPreview',
    #                'statusImageAdmin',
    #                'statusImageUser',
    #                'editorIcon',
    #                'loader',
    #                'logo',
    #                'colsMainTemplate',
    #                'rowsMainTemplate'
    #                ]
    #                
    #                
    #    for setting in settings:
    #        content += setting + " = " + str(self.settings[setting.lower()]) + "\n"
    #        
    #    # Заносим [intPrint2000] 
    #    content += "\n[intprint2000]\n"
    #        
    #    
    #    
    #    
    #    
    #    intPrint2000 = [ ( int(index[2:-1]), value ) for index, value in self.intPrint2000.items() ]
    #    # [(int,''), (int,''), (int,''),...]
    #    
    #    intPrint2000.sort(key = lambda x: x[0])
    #    
    #    
    #    # Избавляемся от повторений
    #    oldValue = ''
    #    shift = 0
    #    for index, (id, value) in enumerate(intPrint2000[:]):
    #        if oldValue == value:
    #            intPrint2000.pop(index + shift)
    #            shift -= 1
    #            
    #        oldValue = value
    #        
    #    for id, value in intPrint2000:
    #        content += str(id) + " = " + value + "\n"
    #    
    #    
    #    # Заносим [userMarks]
    #    content += "\n[usermarks]\n"
    #    
    #    keys = self.userMarks.keys()
    #    keys.sort(key = lambda x: int(x[2:-1]))
    #    
    #    for key in keys:
    #        content += key[2:-1] + ' = ' + self.userMarks[key][0] + '*' + self.userMarks[key][1] + '\n'
    #    
    #    
    #    # Заносим [csv]
    #    content += '\n[csv]\n'
    #    
    #    csv = ['CountInPage',
    #           'LeftIndent', 
    #           'Separator'
    #            ]
    #                        
    #    for name in csv:
    #        content += name + " = " + self.csv[name.lower()] + "\n"
    #    
    #    
    #    
    #    # Заносим [csvdata]
    #    content += '\n[csvdata]\n'
    #    
    #    
    #    print u'Сохраняю csv:'
    #    for row in self.csvData:
    #        print '|'.join(row)
    #    
    #    
    #    for row in self.csvData:
    #  #      index = row.pop(-1)
    #        content += index + ' = ' + '*'.join(row) + '\n'
    #    
    #    
    #    
    #    with open(self.__configFile, 'w') as hf:
    #        content = content.encode('utf-8')
    #        hf.write(content)
        
        