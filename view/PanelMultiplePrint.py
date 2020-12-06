# -*- coding: utf-8 -*- 

# Нельзя генерировать пользовательское событие из основного потока, т.к. начальное окно проги не покажется
# Так как запущена анимация в начале то из обработчика пользовательского события вызываем Yield() чтоб анимация
# проигрывалась потихоньку

# Проверить в CreateButtonList избавиться то пользовательского события по созданию кнопки
# А использовать только Yield()

# Кароче допилить быстродействие когда будет готово все и свободное время
# Трабл с вставкой значений из базы (фио адрес) для больших файлов, пока вызывается Yield() на каждые 10 операций к базе
# Аналогично с сортировкой, и сменой цветов (OnAll and OffAll)
# Возможно придется использовать очереди или чтото другое

# PS Долгий вариант пока работает нормально

import wx
import threading
import copy
import time
import datetime
import os

from LoaderImage import LoaderImage


myCREATE_BTN = wx.NewEventType()
CREATE_BTN = wx.PyEventBinder(myCREATE_BTN, 1)

mySIGNAL_START = wx.NewEventType()
SIGNAL_START = wx.PyEventBinder(mySIGNAL_START, 1)
    
    
class EventCreateBtn(wx.PyCommandEvent):
    # класс события предназначен для создания одной кнопки в режиме массовой печати
    def __init__(self, etype, eid, value = None, data = 0):
        wx.PyCommandEvent.__init__(self, etype, eid)
        
        self.data = data
        
class EventSignalStart(wx.PyCommandEvent):
    # класс события предназначен для посылания сигнала в главный поток
    def __init__(self, etype, eid, value = None):
        wx.PyCommandEvent.__init__(self, etype, eid)


class PanelMultiplePrint(wx.Panel, threading.Thread):
    def __init__(self, parent, file, data):
        
        threading.Thread.__init__(self)
        
        self.parent = parent
        self.model = parent.model
        self.fileName = file
        self.file = file
        self.setting = self.parent.setting
        
        wx.Panel.__init__(self, self.parent.PanelMain, size = self.parent.PanelMain.GetSize())
        self.SetBackgroundColour(self.setting['colour'])
        
        self.listOcc = copy.deepcopy(data)
        
        self.countList = len(self.listOcc)
        # Для отслеживания оставшегося времени печати
        self.countNotPrint = self.countList
        # Скорость печати для выбранного принтера
        self.timePrint = 0
        self.statusThread = 'Create'
        self.wayThread = {  'Create' : ( self.DrawPanel, [self.CreateMainPanels, self.AddWidgetsToTopPanel, self.AddWidgetsToButtomPanel]),
                            'Change' : ( self.DrawPanel, [self.AddWidgetsToTopPanel]),
                            'Print'  : self.PrintAllDocs,
                            'Sort'   : self.Sort,
                            'Export' : self.Export,
                            }
        
        self.Bind(SIGNAL_START, self.GetSignal)
        self.Bind(CREATE_BTN, self.onCreateBtn)
        
        self.ani = LoaderImage(self.setting['loader'])
        self.ani.ag.Play()
        self.ani.Show(True)
        
        self.start()
        
    def CreateMainPanels(self):
        # Создаем верхнюю и нижнюю панели
        self.panelTop = wx.Panel(self, -1)
        self.panelTop.SetBackgroundColour(self.setting['colour'])
        self.panelBottom = wx.Panel(self, -1)
        self.panelBottom.SetBackgroundColour(self.setting['colour'])
        
        self.Vsizer = wx.BoxSizer(wx.VERTICAL)
        self.Vsizer.Add(self.panelTop, 3, flag = wx.EXPAND)
        self.Vsizer.Add(self.panelBottom, 1, flag = wx.EXPAND)
        self.SetSizer(self.Vsizer)
        self.Layout()
        
    def AddWidgetsToTopPanel(self):
        # Добавляем виджеты на верхнюю панель или заменяем
        # Если смена то уничтожаем панель и меняем заголовок у бокса и создаем панель снова, иначе создаем бокс и создаем панель
        if len(self.file) > 35:
            self.file = self.file[:3] + '...' + self.file[-28:]
        label = u'Список лицевых счетов, не отсортированный (' + self.file + ')'
        if self.statusThread == 'Change':
            self.panelTopList.Destroy()
            self.sbList.SetLabel(label)
        else:
            self.sbList = wx.StaticBox(self.panelTop, -1, label, (5, 0), (480, 235))

        self.panelTopList = wx.Panel(self.panelTop, -1, (15, 20), (470, 210))
        
    def AddWidgetsToButtomPanel(self):
        # Добавляем виджеты на нижнюю панель
        
        buttons = [ (u'Ожидает', self.setting['mpSleep'], u'Все напечатанные документы перевести в статус не напечатаные', self.OnOnAll),
                    (u'Следующий', self.setting['mpNext'], '', None),
                    (u'Идет печать', self.setting['mpGo'], '', None),
                    (u'Напечатан', self.setting['mpDone'], u'Все не напечатаные документы перевести в статус напечатанные', self.OnOffAll)
                    ]
        
        for index, (label, colour, help, function) in enumerate(buttons):
            x, y = (index%2, index/2)
            
            btn = wx.Button(self.panelBottom, -1, label, (x * 80 + 2 + 10, y * 20 + 2), (80, 20))
            btn.SetBackgroundColour(colour)
            btn.SetToolTip(wx.ToolTip(help))
            
            if function is not None:
                btn.Bind(wx.EVT_LEFT_DCLICK, function)
        
        
        font = wx.Font(9, 74, 93, wx.NORMAL)
        
        static = wx.StaticText(self.panelBottom, -1, u'Тип извещения:', pos=(186, 3))
        static.SetFont(font)
        
        tlist = [ templ for templ in self.model.objConfig.options('templates') if int( self.model.objConfig.get('templates', templ).split('*')[-1] ) ]
        self.Tchoice = wx.Choice(self.panelBottom, -1, (278, 0), (210, -1), choices = tlist)
        self.Tchoice.SetBackgroundColour(self.setting['colour'])
        self.Tchoice.SetSelection(0)
        
        static = wx.StaticText(self.panelBottom, -1, u'Принтер:', (217, 28))
        static.SetFont(font)
        
        
        plist = [ row.split('*')[1] for row in self.model.objConfig.options('printers') if int( self.model.objConfig.get('printers', row).split('*')[1] ) ]
        self.Pchoice = wx.Choice(self.panelBottom, -1, (278, 25), (210, -1), plist)
        self.Pchoice.SetBackgroundColour(self.setting['colour'])
        self.Pchoice.Bind(wx.EVT_CHOICE, self.OnSelectPrinter, self.Pchoice)
        self.Pchoice.SetSelection(0)
        self.updateTimePrint(plist[0])
        
        typeSort = (u'лицевой', u'фио', u'адрес')
        self.TypeSort = wx.Choice(self.panelBottom, -1, (8, 56), (75, -1), typeSort)
        self.TypeSort.SetBackgroundColour(self.setting['colour'])
        self.TypeSort.SetSelection(0)
        
        self.BtnSort = wx.Button(self.panelBottom, -1, u'сортировать', (85, 55))
        self.BtnSort.SetBackgroundColour(self.setting['colour'])
        self.BtnSort.Bind(wx.EVT_BUTTON, self.OnSort, self.BtnSort)
        
        self.BtnExport = wx.Button(self.panelBottom, -1, u'экспорт', (175, 55))
        self.BtnExport.SetBackgroundColour(self.setting['colour'])
        self.BtnExport.Bind(wx.EVT_BUTTON, self.OnExport, self.BtnExport)
        
        self.BtnArchive = wx.Button(self.panelBottom, -1, u'архив', (255, 55))
        self.BtnArchive.SetBackgroundColour(self.setting['colour'])
        self.BtnArchive.Bind(wx.EVT_BUTTON, self.OnArchive, self.BtnArchive)
        
        self.BtnChangeFile = wx.Button(self.panelBottom, -1, u'др.файл', (335, 55)) 
        self.BtnChangeFile.SetBackgroundColour(self.setting['colour'])
        self.BtnChangeFile.Bind(wx.EVT_BUTTON, self.OnChange, self.BtnChangeFile)
        
        self.BtnPrint = wx.Button(self.panelBottom, -1, u'печать', (415, 55))
        self.BtnPrint.SetBackgroundColour(self.setting['colour'])
        self.BtnPrint.Bind(wx.EVT_BUTTON, self.OnPrint, self.BtnPrint)
        
    def OnSelectPrinter(self, event):
        
        self.updateTimePrint(event.GetString())
    
    def updateTimePrint(self, printer):
        
        server = ''
        for option in self.model.objConfig.options('printers'):
            s, p = option.split('*')
            if printer == p:
                server = s
                break
        
        if server:
            self.timePrint = int( self.model.objConfig.get('printers', server + '*' + printer).split('*')[0] )
        
        # Поскольку выбор принтера запрещен при печати то 'Время печати: ...'
        self.parent.statusBar.SetStatusText(u'Время печати: ' + self.model.getTime(self.countNotPrint * self.timePrint), 0)
        
    def OnOffAll(self, event):
        
        self.changeColourBtns( self.setting['mpDone'] )
        self.countNotPrint = 0
        self.parent.statusBar.SetStatusText('', 0)
        
    def OnOnAll(self, event):
        
        self.changeColourBtns( self.setting['mpSleep'] )
        self.countNotPrint = self.countList
        self.parent.statusBar.SetStatusText( u'Время печати: ' + self.model.getTime(self.countNotPrint * self.timePrint), 0)
        
    def changeColourBtns(self, colour):
        
        for index, item in enumerate(self.listOcc):
            # Второй элемент в списке цвет хранит
            if item[1] != colour:
                
                self.listOcc[index] = ( self.listOcc[index][:1] + [colour] + self.listOcc[index][2:] )
                btn = self.FindWindowByName(str(index))
                btn.SetBackgroundColour(colour)
        self.parent.Enable()
        
    def run(self):
        
        # Короче если создание или изменение то посылаем событие иначе обработка в этом потоке
        # Посылаем сигнал т.к. в данном режиме выводиться анимация, при других нет
        if self.statusThread == 'Create' or self.statusThread == 'Change':
            evt = EventSignalStart(mySIGNAL_START, -1)
            wx.PostEvent(self, evt)
        else:
            self.wayThread[self.statusThread]()
        threading.Thread.__init__(self)
        
    def GetSignal(self, event):
        
        # Мы однозначно знаем что будет вызвана функция рисования, с функциональными аргументами
        f, args = self.wayThread[self.statusThread]
        f(args)
        
    def addInfo(self):
        
        length = len(self.listOcc)
        
        def upadateStatusBar(start):
            self.parent.statusBar.SetStatusText(u'Идет загрузка лицевых счетов ( ' + str(start) + ' / ' + str(length) + ' )', 0)
        
        # Поскольку файл может быть большим, то изъятие инфы из базы может занять несколько секунт, поэтому раз в count обработанных счетов прогружаем анимацию (wx.Yield())
        count = 5
        
        if self.countList < count:
            self.model.objDB.addColourFioAddressToList(self.listOcc, 0, self.countList)
            upadateStatusBar(0)
        else:
            for j in range(self.countList/count):
                self.model.objDB.addColourFioAddressToList(self.listOcc, j * count, count)
                upadateStatusBar(j * count)
                wx.Yield()
            module = self.countList % count
            if module != 0:
                self.model.objDB.addColourFioAddressToList(self.listOcc, (j + 1) * count, module)
                upadateStatusBar((j + 1) * count)
        
    def DrawPanel(self, functions):
        
        for function in functions:
            function()
            wx.Yield()
            
        self.parent.Enable(False)
        self.parent.statusBar.SetStatusText(u'Идет загрузка лицевых счетов, пожалуйста подождите...', 0)
        
        self.addInfo()
        
        # создание кнопок
        self.CreateButtonList()
        # кнопки созданы, прекращаем анимацию
        self.ani.close()
        
        self.parent.Enable()
        self.parent.SetFocus()
        self.parent.statusBar.SetStatusText('', 0)
        
    def CreateButtonList(self):
        
        length = len(self.listOcc)
        
        def upadateStatusBar(start):
            self.parent.statusBar.SetStatusText(u'Идет загрузка лицевых счетов ( ' + str(start) + ' / ' + str(length) + ' )', 0)
        
        self.sw = wx.ScrolledWindow(self.panelTopList, size = (465, 206), style = wx.VSCROLL)
        self.sw.SetBackgroundColour(self.setting['colour'])
        self.sw.SetScrollbars(1, 23, 275, ((self.countList * 23/ 6) + 23) / 23)
        
        for index, (occ, colour, firstname, name, patronymic, streetN, streetC, houseN, houseC, flatN, flatC) in enumerate(self.listOcc):
            if streetN == 0:
                streetN = ''
            
            data = {'occ'    : occ,
                    'colour' : colour,
                    'help'   : firstname + u' (Адрес: ' + str(streetN) + streetC + u' д.' + str(houseN) + houseC + u' кв.' + str(flatN) + flatC + ')',
                    'index'  : index
                    }
            
            evt = EventCreateBtn(myCREATE_BTN, -1, data = data)
            wx.PostEvent(self, evt)
            upadateStatusBar(index)
            wx.Yield()
            
        
        
    def onCreateBtn(self, event):
        
        # Создание одной кнопки по сигналу CREATE_BTN посылаемый от CreateButtonList
        index = event.data['index']
        y, x = index / 6, index % 6
        
        btn = wx.Button(self.sw, -1, event.data['occ'], (x * 75, y * 23), wx.DefaultSize, name = str(index))
        btn.SetBackgroundColour(event.data['colour'])
        btn.SetToolTip(wx.ToolTip(event.data['help']))
        btn.Bind(wx.EVT_LEFT_DCLICK, self.LeftDclick)
        btn.Bind(wx.EVT_RIGHT_DCLICK, self.RightDclick)
        btn.Bind(wx.EVT_ENTER_WINDOW, self.EnterButton)
        btn.Bind(wx.EVT_LEAVE_WINDOW, self.LeaveButton)
        
    def OnPrint(self, event):
        
        if self.statusThread == 'Print':
            self.statusThread = ''
            self.BtnPrint.Disable()
        else:
            self.BtnPrint.SetLabel(u'Остановить')
            self.statusThread = 'Print'
            self.start()
    
    def PrintAllDocs(self):
        
        end = [u'ий', u'ия', u'ии', u'ии', u'ии', u'ий', u'ий', u'ий', u'ий', u'ий']
         
        def getEnding(n):
            
            if n < 10:
                return end[n]
            elif n < 20:
                return u'ий'
            elif n < 100:
                return end[str(n)[-1]]
            else:
                if 10 < int(str(n)[-2:]) < 20:
                    return u'ий'
                else:
                    return end[int(str(n)[-1])]
        
        def getTime(second):
            out, hour, min, sec = ['', '', '', '']
            hour = second / 3600
            second = second % 3600
            min = second / 60
            second = second % 60
            sec = second % 60
            
            if hour: out = out + str(hour) + u'ч '
            if min: out = out + str(min) + u'м '
            if sec: out = out + str(sec) + u'с '
            return out
        
        self.model.objLoger.info(self.model.objLoger.data['user'] + u' начинает массовую печать квитанций в количестве ' + str(self.countNotPrint) + u' шт. из файла: ' + self.fileName)
        template = self.Tchoice.GetStringSelection()
        printer = self.Pchoice.GetStringSelection()
        
        timePrint = 0
        for row in self.model.objConfig.options('printers'):
            serv, prin = row.split('*')
            if prin == printer:
                timePrint = int( self.model.objConfig.get('printers', row).split('*')[0] )
                break
        
        count = 0
        countDoc = self.countNotPrint
        
        self.DisableBtns()
        
        while self.statusThread == 'Print':
            # Перед печатью документа определяем текущую и следующую кнопку, разукрашиваем кнопки и обновляем массив
            current = self.FindNextPrint()
            
            self.parent.statusBar.SetStatusText(u'Осталось ' + str(self.countNotPrint) + u' квитанц' + u', время: ' + getTime(self.timePrint * self.countNotPrint), 0)
            if current is not None:
                
                btn = self.FindWindowByName(str(current))
                occ = int(self.listOcc[current][0])
                
                # Обновляем массив цветов и разукрашиваем текущую кнопку
                self.listOcc[current][1] = self.setting['mpGo']
                btn.SetBackgroundColour(self.setting['mpGo'])
                btn.Update()
                
                # Узнаем какой следующий желтый (т.е. готовится)
                next = self.FindNextPrint()
                
                if next is not None:
                    btnNext = self.FindWindowByName(str(next))
                    
                    if self.listOcc[next][1] == self.setting['mpSleep']:
                        self.listOcc[next][1] = self.setting['mpNext']
                        btnNext.SetBackgroundColour(self.setting['mpNext'])
                        btnNext.Update()
                    
                # Отправляем печать одного документа
                
                if self.model.generateFile(int(occ), template):
                    self.model.printing(printer)
                else:
                    msg = u'Произошла ошибка. Скорей всего выбран не тот тип извещенния для лицевого счета(' + str(occ) + u').\nДля подробной информации смотрите лог.'
                    dlg = wx.MessageDialog(None, msg, u'Ошибка связзанная с базой данных', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    
                    # обнуляем графику и списко текущего и следующего
                    self.listOcc[current][1] = self.setting['mpSleep']
                    btn.SetBackgroundColour(self.setting['mpSleep'])
                    btn.Update()
                    
                    self.listOcc[next][1] = self.setting['mpNext']
                    btnNext.SetBackgroundColour(self.setting['mpNext'])
                    btnNext.Update()
                    break
                    
                time.sleep(self.timePrint)
                # Уснатанвливаем статус выполнен
                self.listOcc[current][1] = self.setting['mpDone']
                btn.SetBackgroundColour(self.setting['mpDone'])
                btn.Update()
                self.countNotPrint = self.countNotPrint - 1
                count += 1
            else:
                break
                
        self.EnableBtns()
        self.model.objLoger.info(self.model.objLoger.data['user'] + u' прерывает массовую печать, отправив на печать ' + str(count) + u' шт. из файла: ' + self.fileName)
        
        self.parent.statusBar.SetStatusText('', 0)
        self.statusThread = ''
        self.BtnPrint.SetLabel(u'печать')
        self.BtnPrint.Enable()
        self.parent.statusBar.SetStatusText('', 0)
    
    def EnableBtns(self):
        
        self.parent.back.Enable()
        self.BtnSort.Enable()
        self.BtnChangeFile.Enable()
        self.BtnExport.Enable()
        self.BtnArchive.Enable()
        
    def DisableBtns(self):
        
        # Делаем запрет на возврат при печати
        self.parent.back.Enable(False)
        self.BtnSort.Disable()
        self.BtnChangeFile.Disable()
        self.BtnExport.Disable()
        self.BtnArchive.Disable()
        
    def FindNextPrint(self):
        
        # Ищем желтые
        for i in range(self.countList):
            if self.listOcc[i][1] == self.setting['mpNext']:
                return i
        
        # Если не нашли ищем первый белый
        for i in range(self.countList):
            if self.listOcc[i][1] == self.setting['mpSleep']:
                return i
    
    
    def OnChange(self, event):
        
        # Выбираем другой файл, необходимо изменить длину списка self.countList, установить self.wayThread в Change чтоб вызвать только AddWidgetsToTopPanel
        self.dlg = wx.FileDialog(self, message = u'Выбор файла, списка лицевых счетов', defaultDir = '', defaultFile = '', wildcard = '*.*', style = wx.OPEN)
        listOcc = []
        fileNamePath  = ''
        if self.dlg.ShowModal() == wx.ID_OK:
            fileNamePath = self.dlg.GetPath()
            listOcc = self.model.getListOCCFromFile(fileNamePath)
            if not listOcc:
                self.model.objLoger.error(self.model.objLoger.data['user'] + u' выбирает другой файл лицевых счетов: "' + fileNamePath + u'" но там не найдены лицевые счета, попробуйте указать другой файл')
                msg = u'В выбранном вами файле "' + fileNamePath + u'" не обнаружено ниодного лицевого счета, попробуйте указать другой файл.'
                dlg = wx.MessageDialog(None, msg, u'Ошибка загрузки лицевых счетов', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return
        else:
            return
            
        # Список не пустой значит перерисовываем кнопки
        self.listOcc = listOcc
        self.countList = len(listOcc)
        self.countNotPrint = self.countList
        self.file = fileNamePath
        self.ani = LoaderImage(self.setting['loader'])
        self.ani.ag.Play()
        self.ani.Show(True)
        self.statusThread = 'Change'
        self.start()
        
    def OnExport(self, event):
        
        self.statusThread = 'Export'
        self.start()
        
    
    def Export(self):
        
        self.parent.Enable(False)
        length = len(self.listOcc)
        
        def upadateStatusBar(start):
            self.parent.statusBar.SetStatusText(u'Идет экспорт лицевых счетов ( ' + str(start) + ' / ' + str(length) + ' )', 0)
        
        def check():
            
            temp = [ False for row in self.listOcc if len(row) != 11 ]
            if not len(temp):
                return True
            else:
                for index, row in enumerate(self.listOcc):
                    for i, r in enumerate(row):
                        if 'int' in str(type(r)):
                            row[i] = str(r)
                return False
            
        self.dlg = wx.FileDialog(self, message = u'Экспортируем список лицевых счетов', defaultDir = '', defaultFile = '', wildcard = '*.*', style = wx.FD_SAVE)
        if self.dlg.ShowModal() == wx.ID_OK:
            fileNamePath = self.dlg.GetPath()
            
            content = u'Экспорт: ' + self.sbList.GetLabel() + '\n\n'
            
            title = u'--№--|{0:-^24}|{1:-^80}|{2:-^40}\n'.format('occ', u'Адрес', u'ФИО')
            for index, ( occ, colour, firstname, name, patronymic, streetN, streetC, houseN, houseC, flatN, flatC ) in enumerate(self.listOcc):
                
                upadateStatusBar(index)
                
                if index % 40 == 0:
                    content += title 
                    
                if not streetN:
                    streetN = ''
                    
                address = str(streetN) + streetC + u', д. ' + str(houseN) + houseC + u', кв. ' + str(flatN) + flatC
                fio = firstname + ' ' + name + ' ' + patronymic
                
                content += u'{0:<5}|         {1:<15}|     {2:75}|   {3:22}\n'.format(str(index) + '.', occ, address, fio)
            
            with open(fileNamePath, 'w') as hf:
                hf.write(content.encode('utf-8'))
        
        self.parent.statusBar.SetStatusText(u'', 0)
        
        self.parent.Enable()
                
    def OnSort(self, event):
        
        # Поскольку сортировка мб долгая то запустим self.Sort() в другом потоке
        self.parent.statusBar.SetStatusText(u'Идет сортировка, пожалуйста подождите', 0)
        self.statusThread = 'Sort'
        self.start()
        
    def Sort(self):
        
        def check():
            temp = [ False for row in self.newListOcc if len(row) != 11 ]
            
            if not len(temp):
                return True
            else:
                pass
        
        typeSort = [(u'номеру',  self.model.sortListByOCC),
                    (u'фамилии', self.model.sortListByFio),
                    (u'адресу',  self.model.sortListByAddress)
                    ]
        
        
        choise = self.TypeSort.GetSelection()
        
        label = u'Список лицевых счетов, отсортированный по ' + typeSort[choise][0]
        self.newListOcc = typeSort[choise][1](copy.deepcopy(self.listOcc))
        
        if self.countList == len(self.newListOcc):
            
            content = u'Экспорт: ' + self.sbList.GetLabel() + '\n\n'
            self.parent.Enable(False)
            self.parent.statusBar.SetStatusText(u'Идет сортировка, пожалуйста подождите...', 0)
            
            for index, (occ, colour, firstname, name, patronymic, streetN, streetC, houseN, houseC, flatN, flatC ) in enumerate(self.newListOcc):
                btn = self.FindWindowByName(str(index))
                btn.SetLabel(str(occ))
                btn.SetBackgroundColour(colour)
                help = firstname + ' ' + name + ' ' + patronymic + u' (Адрес: ' + str(streetN) + streetC + u' д.' + str(houseN) + houseC + u' кв.' + str(flatN) + flatC + ')'
                btn.SetToolTip(wx.ToolTip(help))
                
            label += ' (' + self.file + ')'
            self.sbList.SetLabel(label)
            self.listOcc = self.newListOcc
            self.parent.statusBar.SetStatusText(u'', 0)
            self.parent.Enable()
            
        else:
            self.model.objLoger.error(u'Произошла ошибка при сортировке списка лицевых счетов. Старый и новый не совпадают по количеству, обратитесь к программисту.')
            
    def OnArchive(self, event):
        
        self.dlg = wx.DirDialog(self, message = u'Выбирете папку, куда сделать архивацию лицевых счетов', defaultPath="", style= wx.DD_DIR_MUST_EXIST)
        if self.dlg.ShowModal() == wx.ID_OK:
            fileNamePath = self.dlg.GetPath()
            
            self.parent.Update()
            template = self.Tchoice.GetStringSelection()
            
            dt = datetime.datetime.now()
            
            fileNamePath += '\\' + dt.strftime('%Y.%m.%d.%H.%M.%S') + '_' + template.replace('"','')
            
            try:
                os.mkdir(fileNamePath)
            except WindowsError as err:
                print err
                self.model.objLoger.error(u'Произошла ошибка при создании папки для архивации.')
                return
            
            self.parent.statusBar.SetStatusText(u'Идет архивация лицевых счетов, пожалуйста подождите...', 0)
            self.parent.Enable(False)
            for index, row in enumerate(self.listOcc):
                occ = row[0]
                file = fileNamePath + '\\' + occ + '.txt'
                if not self.model.generateFile(occ, template, setUserMarks = True, out = file):
                    msg = u'Произошла ошибка архивации. Скорей всего выбран не тот шаблон для лицевого счета.\nДля подробной информации смотрите лог.'
                    dlg = wx.MessageDialog(None, msg, u'Ошибка связзанная с базой данных', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    
                    try:
                        os.rename(fileNamePath, fileNamePath + '(error)')
                    except WindowsError as err:
                        self.model.objLoger.error(u'Произошла ошибка при создании папки для архивации.')
                        
                    for root, dirs, files in os.walk(fileNamePath + '(error)', topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(fileNamePath + '(error)')
                    
                    self.parent.statusBar.SetStatusText(u'', 0)
                    self.parent.Enable()
                    return
                self.parent.statusBar.SetStatusText(u'Идет архивация лицевых счетов, пожалуйста подождите...(' + str(index+1) + '/' + str(self.countList) + ')', 0)
                self.parent.Update()
            try:
                os.rename(fileNamePath, fileNamePath + '(arhive)')
                dlg = wx.MessageDialog(None, u'Архивация лицевых счетов прошла успешно', u'Успешное выполнение', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                
            except WindowsError as err:
                self.model.objLoger.error(u'Произошла ошибка при создании папки для архивации.')
            
            self.parent.statusBar.SetStatusText('', 0)
            self.parent.Enable()
            
    
    # Следующие функции предназначены для обработок событий мыши (двойные щелчки правой и левой, ввод и вывод из области)
    # LeftDclick, RightDclick, EnterButton, LeaveButton
    def LeftDclick(self, event):
 
        btnObj = event.GetEventObject()
        index = int(btnObj.GetName())
        colour = btnObj.GetBackgroundColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        
        if (colour == self.setting['mpNext']):
            self.listOcc[index] = ( self.listOcc[index][:1] + [self.setting['mpMouse']] + self.listOcc[index][2:] )
            btnObj.SetBackgroundColour(self.setting['mpMouse'])
        elif (colour == self.setting['mpMouse']):
            self.listOcc[index] = ( self.listOcc[index][:1] + [self.setting['mpNext']] + self.listOcc[index][2:] )
            btnObj.SetBackgroundColour(self.setting['mpNext'])
            
    def RightDclick(self, event):
        
        btnObj = event.GetEventObject()
        index = int(btnObj.GetName())
        colour = btnObj.GetBackgroundColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        
        # Если серый то уменьшаем список на 1
        if (colour == self.setting['mpMouse']):
            self.countNotPrint -= 1
            
        # Если зеленый то увеличиваем список на 1
        if (colour == self.setting['mpDone']):
            self.countNotPrint +=  1
            
        if self.statusThread == 'Print': 
            out = u'Оставшееся время: '
        else:
            out = u'Время печати: '
        
        if self.countNotPrint:
            self.parent.statusBar.SetStatusText( out + self.model.getTime(self.countNotPrint * self.timePrint), 0)
        else:
            self.parent.statusBar.SetStatusText('', 0)
        
        if (colour == self.setting['mpMouse']):
            self.listOcc[index] = ( self.listOcc[index][:1] + [self.setting['mpDone']] + self.listOcc[index][2:] )
            btnObj.SetBackgroundColour(self.setting['mpDone'])
        elif (colour == self.setting['mpDone']):
            self.listOcc[index] = ( self.listOcc[index][:1] + [self.setting['mpMouse']] + self.listOcc[index][2:] )
            btnObj.SetBackgroundColour(self.setting['mpMouse'])
        
    def EnterButton(self, event):
        
        btnObj = event.GetEventObject()
        index = int(btnObj.GetName())
        
        if self.listOcc[index][1] == self.setting['mpSleep']:
            self.listOcc[index] = ( self.listOcc[index][:1] + [self.setting['mpMouse']] + self.listOcc[index][2:] )
            btnObj.SetBackgroundColour(self.setting['mpMouse'])
            
    def LeaveButton(self, event):
        
        btnObj = event.GetEventObject()
        index = int(btnObj.GetName())
        
        if self.listOcc[index][1] == self.setting['mpMouse']:
            self.listOcc[index] = ( self.listOcc[index][:1] + [self.setting['mpSleep']] + self.listOcc[index][2:] )
            btnObj.SetBackgroundColour(self.setting['mpSleep'])