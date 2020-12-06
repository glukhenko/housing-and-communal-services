# -*- coding: utf-8 -*- 

import wx
import time
import locale

# Импортирование панелей
from PanelFind import PanelFind   # MainPanelFind
from PanelSinglePrint import PanelSinglePrint
from PanelMultiplePrint import PanelMultiplePrint
from PanelSettingPrinters import PanelSettingPrinters
from PanelSettingTemplate import PanelSettingTemplate     # MainPanelSettingTemplate
from PanelSettingDB import PanelSettingDB
from StatementCSV import StatementCSV
from PanelUser import PanelUser

class MainWindow(wx.Frame):
    def __init__(self, parent = None):
        # Основное окно состоит из основного горизонтального сайзера, внутри которого слева вертикальный сайзер (информационная панель), и правый вертикальный сайзер (основная панель)
        # В процессе работы меняются только правая основная панель

        self.parent = parent
        self.model = parent.objModel
        self.setting = dict(self.parent.objModel.objConfig.items('setting'))
        
        wx.Frame.__init__(self, None, -1, u'Подсистема печати матричного принтера', wx.DefaultPosition, (640, 400), wx.DEFAULT_FRAME_STYLE ^ (wx.MAXIMIZE_BOX | wx.RESIZE_BORDER) | wx.CLIP_CHILDREN )
        self.SetIcon(wx.Icon(self.setting['icon'], wx.BITMAP_TYPE_PNG))
        
        # список historyPanel нужен для back и forward между панелями
        self.historyPanel = []
        # Хранит ссылку на панель (класс), после back чтоб знать куда возвращаться, т.е. forward
        self.NextPanel = None
        
        self.CreateMenuStatusBars()
        self.CreateDefaultWindow()
        self.Centre()
        self.SetFocus()
        
        #self.synchronizationTemplate()
        self.Bind(wx.EVT_CHAR_HOOK, self.OnHook)
        
        
    def OnHook(self, event):
        
        if event.ControlDown() and event.GetKeyCode() == wx.WXK_LEFT and self.back.IsEnabled():
            self.goPreviousPanel(None)
            
        if event.ControlDown() and event.GetKeyCode() == wx.WXK_RIGHT and self.next.IsEnabled():
            self.goFollowingPanel(None)
            
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnExit(None)
        
        event.Skip()
        
    def getData(self, type=""):
        
        # Позволенно хранить до 15 элементов в списке (в любом из ключей словаря)
        
        action = { 'beginProgram' : [
                                        ('Image\\printF.png', self.startListTypePrint, u'Печать документа'),
                                        ('Image\\addPeopleF.png', self.StartWorkWithPeople, u'Работа с пользователями программы'),
                                        ('Image\\settingF.png', self.startSettingProgramm, u'Настройки программы'),
                                        ],
                   'selectPrinter': [
                                        ('Image\\singlePrintF.png', self.StartSinglePrint, u'Распечатка одного документа' ),
                                        ('Image\\multiplePrintF.png', self.StartMultiplePrint, u'Распечатка серии документов' ),
                                        ('Image\\excelPrintF.png', self.StartStatementCSV, u'Распечатка показаний приборов учета'),
                                       ],
                   'selectSetting': [
                                        ('Image\\printerSettingF.png', self.StartSettingPrint, u'Произвести настройки сетевых принтеров'),
                                        ('Image\\templateSettingF.png', self.StartSettingTemplate, u'Произвести настройки шаблонов печати'),
                                        ('Image\\dbSettingF.png', self.StartSettingDB, u'Произвести настройки базы данных и др.'),
                                       ]
                    }
        if action.has_key(type):
            return action[type][:]
        else: return []
        
    def SetAccess(self, status, existDB, typeList):
        
        # Устанавливает доступ тех или иных функций в программе, в зависимости от типа авторизованного пользователя
        # Подумать над этим извращением, т.е. как убрать вход администратора когда нет соединения с базой
        
        # access содержит биты доступа к тем или иным функциям, см. self.getData()
        access = { (u'Администратор', True) : {'beginProgram'  : (1,1,1), 
                                               'selectPrinter' : (1,1,1),
                                               'selectSetting' : (1,1,1)
                                                },
                                                
                   (u'Администратор', False) : {'beginProgram'  : (0,0,1), 
                                                'selectPrinter' : (0,0,0),
                                                'selectSetting' : (1,0,1)
                                                },
                                     
                   (u'Пользователь', True)  : {'beginProgram'  : (1,0,1),
                                               'selectPrinter' : (1,1,1),
                                               'selectSetting' : (1,1,0)
                                                },
                                     
                   (u'Ограниченный пользователь', True)  : {'beginProgram'  : (1,0,0),
                                                            'selectPrinter' : (1,1,1),
                                                            'selectSetting' : (0,0,0)    # Он сюда никак не прийдем, мб организовать в виде дерева?
                                                            },
                
                   (u'Пользователь', False)  : {'beginProgram'  : (1,1,1),
                                                'selectPrinter' : (0,0,1),
                                                'selectSetting' : (1,0,1)
                                                },
                
                 }
        
        laws = access[(status, existDB)][typeList]
        items = self.PanelMain.gridsizer.GetChildren()
        
        for index, law in enumerate(laws):
            win = items[index].GetWindow()
            win.Enable() if law else win.Disable()
            
            
    def CreateMenuStatusBars(self):
        
        menuBar = wx.MenuBar()
        
        menuOperation = wx.Menu()
        
        self.connectDB = menuOperation.Append(-1, u'Подключиться к базе', u'Инициировать подключение к базе данных')
        self.disconnectDB = menuOperation.Append(-1, u'Отключиться от базы', u'Инициировать отключение от базы данных')
        menuOperation.AppendSeparator()
        closeSession = menuOperation.Append(-1, u'Завершить сеанс', u'Смена пользователя программы')
        exitProgram = menuOperation.Append(-1, u'Выход(ESC)', u'Закрыть приложение')
        
        if self.parent.objModel.objDB.connectExist():
            self.connectDB.Enable(False)
        else:
            self.disconnectDB.Enable(False)
        
        menuAction = wx.Menu()
        self.back = menuAction.Append(-1, u'Назад(ctrl + <-)', u'Вернуться назад')
        self.next = menuAction.Append(-1, u'Вперед(ctrl + ->)', u'Перейти дальше')
        self.back.Enable(False)
        self.next.Enable(False)
        
        self.Bind(wx.EVT_MENU, self.OnConnectDB, self.connectDB)
        self.Bind(wx.EVT_MENU, self.OnDisconnectDB, self.disconnectDB)
        self.Bind(wx.EVT_MENU, self.OnCloseSession, closeSession)
        self.Bind(wx.EVT_MENU, self.OnExit, exitProgram)
        self.Bind(wx.EVT_MENU, self.goPreviousPanel, self.back)
        self.Bind(wx.EVT_MENU, self.goFollowingPanel, self.next)
        
        menuBar.Append(menuOperation, u'Операции')
        menuBar.Append(menuAction, u'Действие')
        self.SetMenuBar(menuBar)
        
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetFieldsCount(3)
        self.statusBar.SetStatusWidths([-7, -3, -2])
        
        self.statusBar.SetStatusText(self.parent.status, 1)
        self.statusBar.SetStatusText(self.parent.user, 2)
        
        
    def OnConnectDB(self, event):
        # Инициировать подключение может только администратор
        
        self.parent.objModel.objDB.connect()
        
        if self.parent.objModel.objDB.connectExist():
            dlg = wx.MessageDialog(None, u'Соединение с базой успешно установленно! Можно приступать к работе', u'Успешное соединение', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            
            self.toggleDBMenuItem()
            self.StartMainPanel(None)
            self.synchronizationTemplate()
            self.Update()
        else:
            dlg = wx.MessageDialog(None, u'Не удалось подсоединиться к базе данных. Проверьте настройки подключения.', u'Ошибка связи с базой данных', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            
        
    def OnDisconnectDB(self, event):
        # Оставлять в программе если только администратор иначе закрывать программу полностью
        
        dlg = wx.MessageDialog(None, u'Вы действительно хотите отключиться от базы данных?', u'Запрос отключения', wx.YES_NO | wx.ICON_INFORMATION)
        res = dlg.ShowModal()
        dlg.Destroy()
        
        if res == wx.ID_YES:
            self.parent.objModel.objDB.disconnect()
            
            dlg = wx.MessageDialog(None, u'Соединение с базой успешно разорвано! База даннах не доступна.', u'Успешное разъединение', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            
            self.toggleDBMenuItem()
            
            if self.parent.status != u'Администратор':
                self.Close()
                
            
            
    def toggleDBMenuItem(self):
        
        if self.connectDB.IsEnabled() and not self.disconnectDB.IsEnabled():
            self.connectDB.Enable(False)
            self.disconnectDB.Enable(True)
        elif not self.connectDB.IsEnabled() and self.disconnectDB.IsEnabled():
            self.connectDB.Enable(True)
            self.disconnectDB.Enable(False)
        
        
    
    def OnCloseSession(self, event):    
        self.parent.user = None
        self.parent.status = None
        self.parent.objModel.objLoger.finish()
        self.Close()
        self.parent.autorization()
        
    def OnExit(self, event):
        
        title = u'Выход из программы'
        msg = u'Вы действительно хотите выйте из программы?'
        
        dlg = wx.MessageDialog(None, msg, title, wx.YES_NO | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()
        
        if res == wx.ID_YES:
            self.parent.objModel.objLoger.info(u'Пользователь выходит из программы. Программа завершает свою работу')
            self.parent.objModel.objLoger.finish()
            self.Close()
        
    def goPreviousPanel(self, event):
        if len(self.historyPanel) > 1:
            if len(self.historyPanel) == 2:
                self.back.Enable(False)
            self.historyPanel[-2](self, None)
            self.NextPanel = self.historyPanel.pop(-1)
            if self.NextPanel == self.StartPrintDoc.__func__:
                self.next.Enable(False)
        
    def goFollowingPanel(self, event):
        if self.NextPanel is not None:
            self.NextPanel(self, None)
    
    
    def CreateDefaultWindow(self):
        
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Подготовка информационной панели
        self.leftSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.PanelInfo = wx.Panel(self, style = wx.NO_BORDER, name = 'infoPanel')
        self.PanelInfo.SetBackgroundColour(self.setting['colour'])
        self.helpSB = wx.StaticBox(self.PanelInfo, -1, u'', (5,15), size=(125, 310))
        self.info = wx.StaticText(self.PanelInfo, -1, u'', pos=(10, 40), size=(115,210), style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
        
        self.info.SetForegroundColour(self.setting['colourInfoText'])
        font = wx.Font(8, 74, 93, wx.NORMAL)
        self.info.SetFont(font)
        
        self.leftSizer.Add(self.PanelInfo, proportion = 1, flag = wx.EXPAND)
        
        # Подготовка основной панели
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        
        # Содержимое этой основной панели будет меняться, в зависимости от запрашиваемых функций
        self.PanelMain = wx.Panel(self, style = wx.NO_BORDER)
        self.PanelMain.SetBackgroundColour(self.setting['colour']) # self.colour
        
        self.PanelMain.gridsizer = wx.GridSizer()
        
        self.StartMainPanel(None)
        
        self.rightSizer.Add(self.PanelMain, proportion = 1, flag = wx.EXPAND)
        
        self.mainSizer.Add(self.leftSizer, flag = wx.EXPAND)
        self.mainSizer.Add(self.rightSizer, proportion = 1, flag = wx.EXPAND)
        
        self.SetSizer(self.mainSizer)
        self.Refresh()
        self.Layout()
        
        
    def templateMainPanel(self, parent, data):
        
        count = len(data)
        
        if count < 0: count = 0
        if count > 15: count = 15
        # Определяем количество колонок для гридсайзера, в зависимости от количества элементов
        if 0 <= count <= 9:
            cols = 3
        elif 9 < count <= 12:
            cols = 4
        elif 12 < count <= 15:
            cols = 5
            
        items = self.PanelMain.gridsizer.GetChildren()
        
        if len(items):
            # Если есть элементы, удаляем их все
            for index, item in enumerate(items):
                item.GetWindow().Destroy()
                
        # После удаления устанавливаем количество колонок
        self.PanelMain.gridsizer.SetCols(cols)
        # И заполняем данными грид сайзер
        for index, (image, func, help) in enumerate(data[:15]):
            
            bmp = wx.Image(image, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tempPanelt = wx.Panel(self.PanelMain, -1, name = str(index))
            tempPanelt.button = wx.BitmapButton(tempPanelt, -1, bmp)
            tempPanelt.button.SetToolTip(wx.ToolTip(help))
            tempPanelt.SetBackgroundColour(self.setting['colour']) # self.colour # 
            self.Bind(wx.EVT_BUTTON, func, tempPanelt.button)
            self.PanelMain.gridsizer.Add(tempPanelt, flag=wx.ALIGN_CENTER)
            
        # Добиваем до 4 элементов до заполнения второй строки
        
        if index < 3:
            for i in range(index + 1, 4):
                tempPanelt = wx.Panel(self.PanelMain, -1, name = str(i))
                tempPanelt.SetBackgroundColour(self.setting['colour']) # 544332
                self.PanelMain.gridsizer.Add(tempPanelt, flag=wx.ALIGN_CENTER)
        
        self.PanelMain.SetSizer(self.PanelMain.gridsizer)
        self.PanelMain.Layout()
        self.Update()
        
    def changeMainPanel(self, FmainPanel, args={}):
        
        self.NextPanel = None
        
        items = self.PanelMain.gridsizer.GetChildren()
        
        if len(items):
            # Если есть элементы, удаляем их все
            for index, item in enumerate(items):
                item.GetWindow().Destroy()
        
        # Новая основная панель (PanelMain) которая помещается в gridsizer
        panel = FmainPanel(self, **args)
        self.PanelMain.gridsizer.Add(panel, proportion = 1, flag = wx.EXPAND) # wx.EXPAND
        self.PanelMain.gridsizer.SetCols(0)
        self.PanelMain.SetSizer(self.PanelMain.gridsizer)
        
        self.Layout()
        self.Update()
        
        items = self.PanelMain.gridsizer.GetChildren()
        
        
    # 10 функций по смене панелей
        
    def StartMainPanel(self, event):
        info = u' \n\n Доступны следующие функции: \n\n 1.Распечатка квитанций \n\n 2.Работа с пользователями \n\n 3.Настройка программы'
        self.info.SetLabel(info)
        self.templateMainPanel(self.PanelMain, data = self.getData('beginProgram'))
        self.upgradeHistory(self.StartMainPanel.__func__)
        self.SetAccess(self.parent.status, self.parent.objModel.objDB.connectExist(), 'beginProgram')
    
    def startListTypePrint(self, event):
        info = u'\n\n\nВыберите тип печати \n\n 1.Единичная печать \n\n 2.Массовая печать\n\n 3.Печать показаний приборов учета'
        self.info.SetLabel(info)
        self.templateMainPanel(self.PanelMain, data = self.getData('selectPrinter'))
        self.upgradeHistory(self.startListTypePrint.__func__)
        self.SetAccess(self.parent.status, self.parent.objModel.objDB.connectExist(), 'selectPrinter')
    
    def StartWorkWithPeople(self, event):
        info = u'\n\nПанель добавления и редактирования пользователей программы \n\n Администратор, пользователь и ограниченный пользователь имеют различные права на доступ к функциям программы'
        self.info.SetLabel(info)
        self.changeMainPanel(PanelUser)
        self.upgradeHistory(self.StartWorkWithPeople.__func__)
        
    def startSettingProgramm(self, event):
        info = u'\n\nВ данном окне производятся настройки: \n\n 1.Настройка принтера\n\n 2.Настройка шаблонов\n\n 3.Настройка базы данных'
        self.info.SetLabel(info)
        self.templateMainPanel(self.PanelMain, data = self.getData('selectSetting'))
        self.upgradeHistory(self.startSettingProgramm.__func__)
        self.SetAccess(self.parent.status, self.parent.objModel.objDB.connectExist(), 'selectSetting')
        
    def StartSinglePrint(self, event):
        info = u'\n\n\nПеред печатью необходимо найти жильца\n\n Для этого воспользуйтесь поиском по адресу или по лицевому счету'
        self.info.SetLabel(info)
        self.changeMainPanel(PanelFind)
        self.upgradeHistory(self.StartSinglePrint.__func__)
    
    def StartMultiplePrint(self, event):
        self.dlg = wx.FileDialog(self, message = u'Выбор файла, списка лицевых счетов', defaultDir='', defaultFile='', wildcard='*.*', style=wx.OPEN)
        
        listOcc = None
        fileNamePath  = ''
        if self.dlg.ShowModal() == wx.ID_OK:
            fileNamePath = self.dlg.GetPath()
            listOcc = self.model.getListOCCFromFile(fileNamePath)
        
        if not listOcc:
            return
        
        info = u'\n\nЗдесь представлен список лицевых счетов, загруженных из выбранного файла\n\n Для печати выберите тип извещения и принтер, на котором хотите запустить массовую печать'
        self.info.SetLabel(info)
        self.changeMainPanel(PanelMultiplePrint, {'data' : listOcc, 'file': fileNamePath}) # .decode(locale.getpreferredencoding())
        self.upgradeHistory(self.StartMultiplePrint.__func__)
    
    def StartStatementCSV(self, event):
        #dlg = wx.MessageDialog(None, u'Печать приборов учета пока не доступна', u'Ошибка', wx.OK | wx.ICON_ERROR)
        #dlg.ShowModal()
        #dlg.Destroy()
        
        self.dlg = wx.FileDialog(self, message = u'Выбор файла, показания приборов учета', defaultDir='', defaultFile='', wildcard='*.*', style=wx.OPEN)
        
        fileNamePath  = ''
        if self.dlg.ShowModal() == wx.ID_OK:
            fileNamePath = self.dlg.GetPath()
            
            info = u'\n\n\nЗагружен список показаний приборов учета\n\n Настройте формат печати, укажите управляющую компанию и запустите печать'
            self.info.SetLabel(info)
            self.changeMainPanel(StatementCSV, {'file' : fileNamePath})
            self.upgradeHistory(self.StartStatementCSV.__func__)
    
    def StartSettingPrint(self, event):
        info = u'\nВ данном окне имеется возможность добавить сетевой принтер, удалить существующий или изменить его настройки\n\n Также можно проверить связь с принтером и распечатать тестовую страницу'
        self.info.SetLabel(info)
        self.changeMainPanel(PanelSettingPrinters)
        self.upgradeHistory(self.StartSettingPrint.__func__)
    
    def StartSettingTemplate(self, event):
        info = u'\n\n\nЗдесь представлен список шаблонов, синхронизированный с базой данных\n\nИмеется возможность настраивать и редактировать их'
        self.info.SetLabel(info)
        self.changeMainPanel(PanelSettingTemplate)
        self.upgradeHistory(self.StartSettingTemplate.__func__)
    
    def StartSettingDB(self, event):
        info = u'\n\n\nПроизведите настройки для соединения с базой данных\n\n Необходимо установить имя и пароль пользователя, от чего имени будут запрашиваться сведения из базы данных'
        self.info.SetLabel(info)
        self.changeMainPanel(PanelSettingDB)
        self.upgradeHistory(self.StartSettingDB.__func__)
    
    def upgradeHistory(self, f):
        # Если в истории нет ссылки на данную функцию значит добавляем, иначе воспринимается как возврат назад
        if f not in self.historyPanel:
            # шаг вперед по списку
            self.historyPanel.append(f)
            self.next.Enable(False)
            if len(self.historyPanel) > 1:
                self.back.Enable()
        else:
            # шаг назад по списку
            self.next.Enable()
            if len(self.historyPanel) < 2:
                self.back.Enable(False)
                
    def StartPrintDoc(self, data):
        info = u'\n\n\n\nВыберите тип печати и принтер для распечатки документа'
        self.info.SetLabel(info)
        self.changeMainPanel(PanelSinglePrint, {'data' : tuple(data)})
        self.upgradeHistory(self.StartPrintDoc.__func__)
        
    def synchronizationTemplate(self):
        
        if self.parent.objModel.objDB.connectExist():
            data = self.parent.objModel.objConfig.compareTemplatesList()
            if data is not None:
                lenAdd = len(data[0])
                lenRemove = len(data[1])
                text = ''
                if lenAdd > 0 and lenRemove == 0:
                    text = u'В базу данных был(и) добавлен(ы) следующий(ие) шаблон(ы):'
                    self.model.objLoger.info(text)
                    
                    text += '\n' + '\n'.join(data[0])
                    [ self.model.objLoger.info('... [' + str(i+1) + ']: ' + template) for i, template in enumerate(data[0]) ]
                    
                elif lenAdd == 0 and lenRemove > 0:
                    text = u'Из базы данных был(и) удален(ы) следующий(ие) шаблон(ы):'
                    self.model.objLoger.info(text)
                    
                    text += '\n' + '\n'.join(data[1])
                    [ self.model.objLoger.info('... [' + str(i+1) + ']: ' + template) for i, template in enumerate(data[1]) ]
                    
                elif lenAdd and lenRemove:
                    if lenAdd == lenRemove:
                        text1 = u'Шаблон(ы):'
                        
                        self.model.objLoger.info(text1)
                        [ self.model.objLoger.info('... [' + str(i+1) + ']:' + template) for i, template in enumerate(data[1]) ]
                        
                        text2 = u'был(и) заменен(ы) на:'
                        
                        self.model.objLoger.info(text2)
                        [ self.model.objLoger.info('... [' + str(i+1) + ']:' + template) for i, template in enumerate(data[0]) ]
                        
                        text = text1 + '\n' + '\n'.join(data[1]) + '\n' + text2 + '\n' + '\n'.join(data[0])
                        
                    elif lenAdd != lenRemove:
                        text1 = u'Из базы данных был(и) удален(ы) шаблон(ы):'
                        
                        self.model.objLoger.info(text1)
                        [ self.model.objLoger.info('... [' + str(i+1) + ']:' + template) for i, template in enumerate(data[1]) ]
                        
                        text2 = u'и добавлен(ы) следующий(ие):'
                        
                        self.model.objLoger.info(text2)
                        [ self.model.objLoger.info('... [' + str(i+1) + ']:' + template) for i, template in enumerate(data[0]) ]
                        
                        text = text1 + '\n' + '\n'.join(data[1]) + '\n' + text2 + '\n' + '\n'.join(data[0])
                        
                dlg = wx.MessageDialog(None, text, u'Информация о шаблонах', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
        
        