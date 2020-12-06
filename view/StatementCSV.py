# -*- coding: utf-8 -*- 

# В конфиге храняться значения в виде key = value в секциях [scvdata]
# где key - Имя столбца в выходной таблице
# value = id_in*width*align*id_out
# В некоторых функциях извращаюсь, чтобы гарантировать прямую последовательность id_out
# т.е. 1,2,3,4 но не 1,4,5,6 и не 2,3,4,5 В общем строго от min до max
# извращения происходят когда удаляются, добавляются и редактируются настройки

import wx

import copy
import os
import threading
import time
import datetime

from Editor import Editor, PopupEditor
        
class StatementCSV(wx.Panel, threading.Thread):
    def __init__(self, parent, file):
        
        threading.Thread.__init__(self)
        self.printing = False
        
        self.parent = parent
        self.model = self.parent.parent.objModel
        self.setting = self.parent.setting
        self.selectedRow = -1
        self.file = file
        
        wx.Panel.__init__(self, self.parent.PanelMain, size = self.parent.PanelMain.GetSize())
        self.SetBackgroundColour(self.setting['colour'])
        
        self.backPanel = wx.Panel(self, pos = (10,5), size=(485, 330))
        self.backPanel.SetBackgroundColour(self.setting['colour'])
        
        self.title = [ (u'Имя', wx.LIST_FORMAT_LEFT, 265),
                       (u'id csv', wx.LIST_FORMAT_CENTER, 50),
                       (u'Ширина', wx.LIST_FORMAT_CENTER, 75),
                       (u'Выравнивание', wx.LIST_FORMAT_CENTER, 90)
                     ]
        
        self.listctrl = wx.ListCtrl(self.backPanel, size = (485, 200), style=wx.LC_REPORT)
        self.listctrl.SetBackgroundColour(self.setting['colour'])
        
        # Заполнение заголовков таблицы
        for index, (name, align, width) in enumerate(self.title):
            self.listctrl.InsertColumn(index, name, align, width)
        
        data = self.model.objConfig.items('csvdata')
        data.sort( key = lambda x: int(x[1].split('*')[-1]) )
        
        # Заполнение ячеек таблицы
        for index, (name, value) in enumerate(data):
            idCsv, width, alignment, idOut = value.split('*')
            self.listctrl.InsertStringItem(index, name)
            self.listctrl.SetStringItem(index, 1, idCsv)
            self.listctrl.SetStringItem(index, 2, width)
            self.listctrl.SetStringItem(index, 3, alignment)
        
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectedItem)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnDeselectedItem)
        
        self.csvSettings = dict( self.model.objConfig.items('csv') )
        
        # Создание кнопок
        btns = [( u'добавить', (5, 215), 'btnAdd', self.OnAdd, True),
                ( u'свойства', (85, 215), 'btnProperties', self.OnProperties, False),
                ( u'удалить', (165, 215), 'btnDelete', self.OnDelete, False),
                ( u'настройки', (400, 215), 'btnSetting', self.OnSetting, True),
                ( u'печать', (400, 298), 'btnPrint', self.OnPrint, True)
                ]
        
        for label, pos, name, handler, status in btns:
            btn = wx.Button(self.backPanel, -1, label, pos, name = name)
            btn.Bind(wx.EVT_BUTTON, handler, btn)
            btn.SetBackgroundColour(self.setting['colour'])
            btn.Enable(status)
        
        if len(file) > 50:
            file = file[:10] + '...' + file[-40:]
        
        font1 = wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL) # 10, wx.MODERN, wx.NORMAL, wx.NORMAL
        font2 = wx.Font(10, 74, 93, wx.NORMAL)
        
        text = [(u'Файл: ' + file, (5, 258), font1),
                (u'Управляющая компания: ', (30, 280), font2),
                (u'Принтер: ', (121, 300), font2)
                ]
        
        for label, pos, font in text:
            txt = wx.StaticText(self.backPanel, -1, label, pos)
            txt.SetFont(font)
            
        wx.StaticLine(self.backPanel, -1, (0, 250), (482,1))
        
        self.ctrlCompany = wx.TextCtrl(self.backPanel, -1, u'Введите управляющую компанию', size=(200, -1), pos=(185, 278))
        self.ctrlCompany.SetBackgroundColour(self.setting['colour'])
        self.ctrlCompany.Bind(wx.EVT_LEFT_DOWN, self.OnCleanField, self.ctrlCompany)
        
        plist = self.model.objConfig.options('printers')
        plist = [ printer.split('*')[-1] for printer in plist if int(self.model.objConfig.get('printers', printer).split('*')[-1]) ]
        self.Pchoice = wx.Choice(self.backPanel, -1, pos = (185, 300), size = (200, -1), choices = plist)
        self.Pchoice.SetBackgroundColour(self.setting['colour'])
        self.Pchoice.SetSelection(0)
        
    def run(self):
        
        end = [u'ов', u'', u'а', u'а', u'а', u'ов', u'ов', u'ов', u'ов', u'ов']
        
        def finish():
            
            self.FindWindowByName('btnPrint').Enable()
            self.FindWindowByName('btnPrint').SetLabel(u'печать')
            threading.Thread.__init__(self)
            self.printing = False
        
        def getEnding(n):
            
            if n < 10:
                return end[n]
            elif n < 20:
                return u'ов'
            elif n < 100:
                return end[int(str(n)[-1])]
            else:
                if 10 < int(str(n)[-2:]) < 20:
                    return u'ов'
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
            
        def Error(text):
            dlg = wx.MessageDialog(None, text, u'Ошибка чтения', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            finish()
        
        usePrinter = self.Pchoice.GetStringSelection()
        printers = [ '*'.join([key, value]).split('*') for key, value in self.model.objConfig.items('printers') ]
        
        id = -1
        for index, (server, printer, timer, status) in enumerate(printers):
            if printer == usePrinter:
                id = index
            
        if id == -1:
            finish()
            return
        
        server, printer, timer, status = printers[id]
        
        if not os.path.isfile(self.file):
            Error(u'Программа не может найти файл "' + self.file + u'". Выберите файл заново.')
        else:
            with open(self.file) as hf:
                data = [ row.rstrip().decode('cp1251').split(';') for row in hf.readlines() if row.strip()]
            
            countInPage = int(self.model.objConfig.get('csv', 'countInPage'))
            leftIndent = ' ' * int(self.model.objConfig.get('csv', 'leftIndent'))
            separator = self.model.objConfig.get('csv', 'separator')
            separatorLine = leftIndent + separator + separator.join( [ '-' * int(self.listctrl.GetItem(i, 2).GetText()) for i in range(self.listctrl.GetItemCount()) ] ) + separator + '\n'
            
            process = self.model.objConfig.get('csv', 'process')
            pages = len(data) / countInPage + 1
            
            titles = [ self.listctrl.GetItem(i, 0).GetText()[: int(self.listctrl.GetItem(i, 2).GetText()) ] for i in range(self.listctrl.GetItemCount()) ]
            dt = datetime.datetime.now()
            content = leftIndent + u'Ведомость ввода показаний счетчиков для инспектора\n'
            content += leftIndent + u'  упр. компания: ' + self.ctrlCompany.GetLabel() + u', дата печати: ' + dt.strftime('%d-%m-%Y %H:%M') + '\n'   
            content += separatorLine
            
            title = leftIndent + separator
            for i in range(self.listctrl.GetItemCount()):
                width = int(self.listctrl.GetItem(i, 2).GetText())
                title += u'{' + str(i) + u':^' + str(width) + u'}+'
            title = title.format(*titles)
            content += title + '\n'
            content += separatorLine
            
            aligns = { u'слева' : '<', u'по центру' : '^', u'справа' : '>'}
            
            format = leftIndent + separator
            for i in range(self.listctrl.GetItemCount()):
                idCsv = int(self.listctrl.GetItem(i, 1).GetText())
                width = int(self.listctrl.GetItem(i, 2).GetText())
                align = self.listctrl.GetItem(i, 3).GetText()
                format += u' {' + str(idCsv) + u':' + aligns[align] + str(width - 2) + u'} +'
            
            # min - для дополнения списка data, не хочется создавать дефолтное значение по не сущ инд.
            min = max([ int(self.listctrl.GetItem(i, 1).GetText()) for i in range(self.listctrl.GetItemCount()) ] )
            # следующие id необходимы для шаманства, см далее
            idSpecificCsv = int(self.model.objConfig.get('csvdata', process).split('*')[0])
            idSpecificRow = int(self.model.objConfig.get('csvdata', process).split('*')[-1])
            
            # Погенерируем страницы, и поотправляем на печать
            for page in range(pages):
                if not self.printing:
                    break
                
                text = content
                for i in range(countInPage):
                    try:
                        items = data[page * countInPage + i]
                        
                        while len(items) < min:
                            items.append('')
                        items.insert(0, '')
                        # Здесь шаманим над столбцом, изза того что кв. и лицевой счет в одной колонке
                        temp = items[idSpecificCsv].split(' ')
                        # Подсчитаем количество пробелов между квартирой и лицевым
                        n = int(self.listctrl.GetItem(idSpecificRow - 1, 2).GetText()) - 2 - len(temp[0]) - len(temp[-1])
                        items[idSpecificCsv] = temp[0] + ' ' * n + temp[-1]
                        # Шаманство заканчивается
                        
                        # Укорачиваем длинные строки, под длину указанную в таблице
                        for i in range(self.listctrl.GetItemCount()):
                            index = int(self.listctrl.GetItem(i, 1).GetText())
                            width = int(self.listctrl.GetItem(i, 2).GetText())
                            if items[index].strip():
                                items[index] = items[index][:width - 2]
                        
                        text += format.format(*items) + '\n'
                        text += separatorLine
                        
                    except IndexError:
                        break
                    
                with open('.\\tmp\\temp.txt', 'w') as hf:
                    hf.write(text.encode('cp1251'))
                
                self.model.printing(usePrinter)
                self.parent.statusBar.SetStatusText(u'Осталось ' + str(pages - page) + u' лист' + getEnding(pages - page) + u', время: ' + getTime(int(timer) * (pages - page)), 0)
                time.sleep(int(timer))
                
            self.parent.statusBar.SetStatusText('')
            finish()
            
    def OnSelectedItem(self, event):
        
        self.selectedRow = event.GetIndex()
        self.FindWindowByName('btnProperties').Enable()
        self.FindWindowByName('btnDelete').Enable()
        
    def OnDeselectedItem(self, event):
        
        self.selectedRow = -1
        self.FindWindowByName('btnProperties').Disable()
        self.FindWindowByName('btnDelete').Disable()
        
    def OnAdd(self, event):
        
        self.parent.Enable(False)
        PopupTemplate(self)
        
    def OnProperties(self, event):
        
        self.parent.Enable(False)
        PopupTemplate(self, int(self.selectedRow))
        
    def OnPrint(self, event):
        
        btn = self.FindWindowByName('btnPrint')
        
        if self.printing:
            # идет печать останавливаем
            btn.SetLabel(u'печать')
            self.printing = False
            btn.Disable()
        else:
            # печать не идет, запускаем поток по началу печати
            btn.SetLabel(u'остановить')
            self.printing = True
            self.start()
            
    def OnCleanField(self, event):
        
        if self.ctrlCompany.GetValue() == u'Введите управляющую компанию':
            self.ctrlCompany.SetValue('')
        
        event.Skip()
        
    def OnSetting(self, event):
        
        self.parent.Enable(False)
        PopupTemplate(self, editSettings = True)
        
    def OnDelete(self, event):
        
        count = self.listctrl.GetItemCount()
        idRow = self.selectedRow
        
        content = u'Вы действительно хотете удалить запись с именем "' + self.listctrl.GetItem(idRow, 0).GetText() + u'"?'
        
        dlg = wx.MessageDialog(None, content, u'Запрос удаления данных', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_ERROR)
        res = dlg.ShowModal()
        dlg.Destroy()
        
        if res == wx.ID_YES:
            name = self.listctrl.GetItem(self.selectedRow, 0).GetText()
            # Из таблицы
            self.listctrl.DeleteItem(self.selectedRow)
            # Из конфигурационного файла
            self.model.objConfig.remove_option('csvdata', name)
            
            self.refreshRowId()
            
    def refreshRowId(self):
        
        # Применяется для сдвига в них выходных id значений, в конфигурационном файле для секции csvdata
        count = self.listctrl.GetItemCount()
        
        for i in range(count):
            nameTemp = self.listctrl.GetItem(i, 0).GetText()
            value = self.model.objConfig.get('csvdata', nameTemp).split('*')
            value[-1] = str(i + 1)
            self.model.objConfig.set('csvdata', nameTemp, '*'.join(value))
            
        self.model.objConfig.save()
        
class PopupTemplate(wx.Frame):
    def __init__(self, parent, rowEdit = None, editSettings = False):
        
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, size = (400, 250), style = style)
        self.Center()
        self.parent = parent
        self.rowEdit = rowEdit
        self.setting = self.parent.setting
        self.editSettings = editSettings
        
        self.panel = wx.Panel(self, -1, size = self.GetSize())
        self.panel.SetBackgroundColour(self.setting['popupBackColour'])
        
        self.panel.Bind(wx.EVT_MOTION, self.OnMouse, self.panel)
        
        self.panelTop = wx.Panel(self.panel, -1, pos = (5, 5),  size = (390, 240))
        self.panelTop.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.panelTop.Bind(wx.EVT_MOTION, self.OnMouse, self.panelTop)
        
        if self.editSettings:
            self.createSettingWidjets()
        else:
            self.createMainWidjets()
        
        btnClose = wx.Button(self.panelTop, -1, u'отмена', (5, 210))
        btnClose.Bind(wx.EVT_BUTTON, self.OnClose, btnClose)
        btnClose.SetBackgroundColour(self.setting['popupTopColour'])
        
        btnAddEdit = wx.Button(self.panelTop, -1, u'сохранить', (310, 210))
        btnAddEdit.Bind(wx.EVT_BUTTON, self.OnSave, btnAddEdit)
        btnAddEdit.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.Show()
        
    def OnMouse(self, event):
        
        if not event.Dragging():
            self._dragPos = None
            return
        
        if not self._dragPos:
            self._dragPos = event.GetPosition()
        else:
            pos = event.GetPosition()
            displacement = self._dragPos - pos
            self.SetPosition( self.GetPosition() - displacement )
        
    def createMainWidjets(self):
        
        text = [(u'Имя: ', (92, 30)),
                (u'id csv: ', (84, 60)),
                (u'Ширина: ', (70, 90)),
                (u'Выравнивание: ', (28, 120)),
                (u'id вых: ', (80, 150)),
                ]
        
        font = wx.Font(10, 74, 93, wx.NORMAL)
        
        for label, pos in text:
            txt = wx.StaticText(self.panelTop, -1, label, pos)
            txt.SetFont(font)
        
        self.name = wx.TextCtrl(self.panelTop, -1, '', (130, 29), (200, -1))
        
        self.scIdCsv = wx.SpinCtrl(self.panelTop, -1, '', (130, 59), (50, -1))
        self.scIdCsv.SetRange(0, 20)
        
        self.scWidth = wx.SpinCtrl(self.panelTop, -1, '', (130, 89), (50, -1))
        self.scWidth.SetRange(1, 50)
        
        aligns = [u'слева', u'по центру', u'справа']
        self.alignChoice = wx.Choice(self.panelTop, -1, pos=(130, 119), size = (100, -1), choices = aligns)
        
        self.scIdOut = wx.SpinCtrl(self.panelTop, -1, '', (130, 149), (50, -1))
        
        if self.rowEdit is None:
            # Добавляется
            self.scIdCsv.SetValue(0)
            self.scWidth.SetValue(10)
            self.alignChoice.SetSelection(0)
            self.scIdOut.SetValue(self.parent.listctrl.GetItemCount() + 1)
            self.scIdOut.SetRange(1, self.parent.listctrl.GetItemCount() + 1)
        else:
            # Редактируется, вставляем редактируемые значения
            self.name.SetValue(self.parent.listctrl.GetItem(self.rowEdit, 0).GetText())
            self.scIdCsv.SetValue(int(self.parent.listctrl.GetItem(self.rowEdit, 1).GetText()))
            self.scWidth.SetValue(int(self.parent.listctrl.GetItem(self.rowEdit, 2).GetText()))
            self.alignChoice.SetSelection(aligns.index(self.parent.listctrl.GetItem(self.rowEdit, 3).GetText()))
            self.scIdOut.SetValue(self.rowEdit + 1)
            self.scIdOut.SetRange(1, self.parent.listctrl.GetItemCount())
        
    def createSettingWidjets(self):
        
        default = u'не обрабатывать'
        text = [(u'Количество строк на стр.: ', (75, 40)),
                (u'Начальный(левый) отступ: ', (76, 70)),
                (u'Символ разделитель: ', (112, 100)),
                (u'Специфическая обработка текста: ', (25, 130))
                ]
        
        font = wx.Font(10, 74, 93, wx.NORMAL)
        for label, pos in text:
            txt = wx.StaticText(self.panelTop, -1, label, pos)
            txt.SetFont(font)
        
        self.scCountInPage = wx.SpinCtrl(self.panelTop, -1, '', (255, 39), (50, -1))
        self.scCountInPage.SetBackgroundColour(self.setting['popupTopColour'])
        self.scCountInPage.SetRange(1, 100)
        self.scCountInPage.SetValue(int(self.parent.model.objConfig.get('csv', 'countInPage')))
        
        self.scLeftIndent = wx.SpinCtrl(self.panelTop, -1, '', (255, 69), (50, -1))
        self.scLeftIndent.SetBackgroundColour(self.setting['popupTopColour'])
        self.scLeftIndent.SetRange(1, 50)
        self.scLeftIndent.SetValue(int(self.parent.model.objConfig.get('csv', 'leftIndent')))
        
        self.tcSeparator = wx.TextCtrl(self.panelTop, -1, '', (255, 99), (50, -1))
        self.tcSeparator.SetBackgroundColour(self.setting['popupTopColour'])
        self.tcSeparator.SetValue(self.parent.model.objConfig.get('csv', 'separator'))
        
        fields = [ self.parent.listctrl.GetItem(index, 0).GetText() for index in range(self.parent.listctrl.GetItemCount()) ]
        fields.insert(0, default)
        self.choice = wx.Choice(self.panelTop, -1, pos = (255, 129), size = (120, -1), choices = fields)
        self.choice.SetBackgroundColour(self.setting['popupTopColour'])
        
        if self.parent.csvSettings['process'] not in fields:
            self.parent.model.objConfig.set('csv', 'process', default)
            self.parent.model.objConfig.save()
        
        self.choice.SetStringSelection(self.parent.model.objConfig.get('csv', 'process'))
        
    def OnSave(self, event):
        
        if self.editSettings:
            self.saveSettings()
        else:
            self.saveData()
        
    def saveSettings(self):
        
        self.parent.model.objConfig.set('csv', 'countInPage', self.scCountInPage.GetValue())
        self.parent.model.objConfig.set('csv', 'leftIndent', self.scLeftIndent.GetValue())
        self.parent.model.objConfig.set('csv', 'separator', self.tcSeparator.GetValue())
        self.parent.model.objConfig.set('csv', 'process', self.choice.GetStringSelection())
        self.parent.model.objConfig.save()
        self.OnClose(None)
        
    def saveData(self):
        
        def MessageDialogError(text):
            
            dlg = wx.MessageDialog(None, text, u'Ошибка настройки шаблона', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        
        # старое имя потребуется для конфига
        if self.rowEdit is not None:
            oldName = self.parent.listctrl.GetItem(self.rowEdit, 0).GetText()
        name = self.name.GetValue()
        scIdCsv = str(self.scIdCsv.GetValue())
        scWidth = str(self.scWidth.GetValue())
        alignChoice = self.alignChoice.GetStringSelection()
        scIdOut = self.scIdOut.GetValue()
        
        if not name.strip():
            MessageDialogError(u'Вы не установили имя, попробуйте снова')
            return
        
        names = [ self.parent.listctrl.GetItem(index, 0).GetText() for index in range(self.parent.listctrl.GetItemCount()) ]
        
        if self.rowEdit is not None:
            names.remove( self.parent.listctrl.GetItem(self.rowEdit, 0).GetText() )
        
        if name in names:
            MessageDialogError(u'Имя "' + name + u'" уже используется, попробуйте задать другое')
            return
        
        if self.rowEdit is None: 
            self.parent.listctrl.InsertStringItem(scIdOut - 1, '')
            value = '*'.join( [str(scIdCsv), str(scWidth), alignChoice, str(scIdOut - 1)] )
            self.parent.model.objConfig.set('csvdata', name, value)
        else:
            # для таблицы проверяем рассположение, если что удаляем и вставляем
            if self.rowEdit != scIdOut - 1:
                self.parent.listctrl.DeleteItem(self.rowEdit)
                self.parent.listctrl.InsertStringItem(scIdOut - 1, '')
            # для конфигурационного файла проверяем имена, если имя изменилось то удаляем и создаем пункт
            if name != oldName:
                self.parent.model.objConfig.remove_option('csvdata', oldName)
            value = '*'.join([str(scIdCsv), str(scWidth), alignChoice, str(scIdOut)])
            self.parent.model.objConfig.set('csvdata', name, value)
            
        self.parent.listctrl.SetStringItem(scIdOut - 1, 0, name)
        self.parent.listctrl.SetStringItem(scIdOut - 1, 1, scIdCsv)
        self.parent.listctrl.SetStringItem(scIdOut - 1, 2, scWidth)
        self.parent.listctrl.SetStringItem(scIdOut - 1, 3, alignChoice)
        
        self.parent.refreshRowId()
        self.OnClose(None)
        
    def OnClose(self, event):
        
        self.parent.parent.Enable()
        self.Close()
        