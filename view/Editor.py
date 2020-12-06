# -*- coding: utf-8 -*-

import wx
import wx.stc
import time
import codecs
import string
import os

import copy

from Preview import Preview

class Editor(wx.Frame):
    def __init__(self, parent, name, file):
        
        self.parent = parent
        self.setting = parent.setting
        self.model = parent.model
        self.name = name
        self.file = file
        self.selectedRow = -1
        # В position храняться метки которые удалось найти в документе и их абсолютное положение в виде { '<H3>' : [(12,15)], '<H12>' : [(16, 20), (56, 60)]}
        self.position = {}
        
        title = u'Редактирование шаблона: .\\templates\\' + file
        wx.Frame.__init__(self, parent, -1, title, style = wx.DEFAULT_FRAME_STYLE) # , size = (1100, 900)
        
        size = wx.ScreenDC().GetSize()
        self.SetSize((size.x, size.y - 35))
        
        self.SetIcon(wx.Icon(self.setting['editorIcon'], wx.BITMAP_TYPE_PNG))
        self.SetMinSize((600, 250))
        
        self.intPrint2000 = self.model.objConfig.parseIntPrint2000()
        
        self.createMenuBar()
        self.initPanels()
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Center()
        self.Show()
        
    def createMenuBar(self):
        
        menuBar = wx.MenuBar()
        
        menuOperation = wx.Menu()
        self.save = menuOperation.Append(-1, u'{0:20}{1}'.format(u'Сохранить', 'Ctrl+S'))
        self.preview = menuOperation.Append(-1, u'{0:15}{1}'.format(u'Предпросмотр', 'F11'))
        menuOperation.AppendSeparator()
        self.exit = menuOperation.Append(-1, u'{0:25}{1}'.format(u'Выход', 'Esc'))
        
        menuSetting = wx.Menu()
        self.limit = menuSetting.Append(-1, u'Ограничитель')
        
        self.Bind(wx.EVT_MENU, self.OnSave, self.save)
        self.Bind(wx.EVT_MENU, self.OnPreview, self.preview)
        self.Bind(wx.EVT_MENU, self.OnExit, self.exit)
        self.Bind(wx.EVT_MENU, self.OnLimit, self.limit)
        
        menuBar.Append(menuOperation, u'Файл')
        menuBar.Append(menuSetting, u'Настройки')
        
        self.SetMenuBar(menuBar)
        
    def initPanels(self):
        
        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour(self.setting['popupTopColour'])
        
        gridsizer = wx.GridSizer()
        gridsizer.Add(self.panel, flag = wx.EXPAND)
        
        self.SetSizer(gridsizer)
        self.Layout()
        
        self.splitter = wx.SplitterWindow(self.panel, -1 , size = self.panel.GetSize(), style = wx.SP_LIVE_UPDATE)
        
        self.panelEditor = wx.Panel(self.splitter, -1)
        self.panelEditor.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.panelDictionary = wx.Panel(self.splitter, -1)
        self.panelDictionary.SetBackgroundColour(self.setting['popupTopColour'])
        self.panelDictionary.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.splitter.SplitVertically(self.panelEditor, self.panelDictionary)
        self.splitter.SetSashPosition(self.GetSize().x - 100, True)
        self.splitter.SetMinimumPaneSize(20)
        
        # Editor
        self.editor = wx.stc.StyledTextCtrl(self.panelEditor, -1)
        
        self.editor.StartStyling(2, 31)
        self.editor.SetForegroundColour(wx.Colour(90, 90, 90))
        
        self.editor.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.editor.SetMarginWidth(1, 30)
        self.editor.SetFoldMarginColour(1, '#ff0000')
        
        self.editor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL))
        self.editor.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        
        self.editor.SetEdgeColumn( int(self.model.objConfig.get('setting', 'limit')) )
        self.editor.Bind(wx.EVT_MOTION, self.OnMove)
        self.editor.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        
        with open('.\\templates\\' + self.file) as hf:
            content = hf.read()
            content = content.decode('utf-8')
            self.editor.SetText(content)
            
        # Dictionary
        self.listctrl = wx.ListCtrl(self.panelDictionary, -1, (5, 0), style=wx.LC_REPORT)
        
        self.listctrl.InsertColumn(0, u'Метка')
        self.listctrl.InsertColumn(1, u'Название')
        self.listctrl.InsertColumn(2, u'Код')
        self.listctrl.SetColumnWidth(0, 80)
        self.listctrl.SetColumnWidth(1, 200)
        self.listctrl.SetColumnWidth(2, 150)
        
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectedItem)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnDeselectedItem)
        
        self.userMarks = {}
        
        # Сделаем проверочку чтоб было 2 значения в записи конфига для пользовательских меток
        
        for key, value in self.model.objConfig.items('userMarks'):
            key = '<M' + key + '>'
            data = value.split('*')
            if len(data) != 2:
                self.userMarks[key] = ''
                self.model.obgLoger.error(u'пользовательская метка "' + name + u'" иммет некоректную запись, путь к шаблону и статус для него обнулится')
            self.userMarks[key] = value
            
        # Перед отображением похорошему надо б отсортировать ( воспользуемся списком )
        
        data = list(self.userMarks.items())
        data.sort( key = lambda x: int(x[0][2:-1]) )
        
        for index, (key, value) in enumerate(data):
            name, code = value.split('*')
            self.listctrl.InsertStringItem(index, '')
            self.listctrl.SetStringItem(index, 0, key)
            self.listctrl.SetStringItem(index, 1, name)
            self.listctrl.SetStringItem(index, 2, code)
        
        
        self.btnAdd = wx.Button(self.panelDictionary, -1, u'Добавить', (5, 500))
        self.btnAdd.Bind(wx.EVT_BUTTON, self.OnAdd, self.btnAdd)
        
        self.btnEdit = wx.Button(self.panelDictionary, -1, u'Свойства', (75, 550))
        self.btnEdit.Bind(wx.EVT_BUTTON, self.OnEdit, self.btnEdit)
        self.btnEdit.Disable()
        
        self.btnDelete = wx.Button(self.panelDictionary, -1, u'Удалить', (100, 600))
        self.btnDelete.Bind(wx.EVT_BUTTON, self.OnDelete, self.btnDelete)
        self.btnDelete.Disable()
        
        self.btnAdd.SetBackgroundColour(self.setting['popupTopColour']) 
        self.btnEdit.SetBackgroundColour(self.setting['popupTopColour'])
        self.btnDelete.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.Bind(wx.EVT_IDLE, self.onIDLE)
        
    def OnSave(self, event):
        
        content = ''
        for row in range(self.editor.GetLineCount()):
            temp = self.editor.GetLine(row).rstrip('\r\n') + '\n'
            content += self.editor.GetLine(row).rstrip('\r\n') + '\n'
            
        content = content.encode('utf-8')
        
        with open('.\\templates\\' + self.file, 'w') as hf:
            hf.write(content)
        
        text = u'Шаблон "' + self.file + u'" предназначеный для "' + self.name + u'" успешно сохранен'
        dlg = wx.MessageDialog(None, text, u'Успешное сохранение', wx.OK | wx.ICON_INFORMATION)
        res = dlg.ShowModal()
        dlg.Destroy()
        
        
    def OnPreview(self, event):
        
        dlg = wx.NumberEntryDialog(self, u'Выберите номер лицевого счета, который хотите просмотреть', u'occ: ', u'Выбор лицевого', 1, 1, 400000)
        res = dlg.ShowModal()
        dlg.Destroy()
        
        if res == wx.ID_OK:
            
            occ = dlg.GetValue()
            
            if not self.model.objDB.existOcc(occ):
                dlg = wx.MessageDialog(None, u'Номер лицевого счета \'' + str(occ) + u'\' не найден в базе данных.', u'Ошибка поиска', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return
                
            self.model.generateFile(occ, self.name, setUserMarks = False)
            self.Enable(False)
            Preview(self)
        
    
    def OnExit(self, event):
        
        self.parent.parent.Enable(True)
        self.Close()
        
    def OnLimit(self, event):
        
        limit = int(self.model.objConfig.get('setting', 'limit'))
        
        dlg = wx.NumberEntryDialog(self, u'Введите значение горизонтального ограничителя', u'Ширина: ', u'Установка границы', limit, 5, 200)
        res = dlg.ShowModal()
        dlg.Destroy()
        
        if res == wx.ID_OK:
            
            self.editor.SetEdgeColumn(dlg.GetValue())
            if self.model.objConfig.has_option('setting', 'limit'):
                self.model.objConfig.set('setting', 'limit', dlg.GetValue())
            self.model.objConfig.save()
            
    def OnKeyDown(self, event):
        
        if event.ControlDown() and event.GetKeyCode() == 83:
            self.OnSave(None)
        elif event.GetKeyCode() == 350:
            self.OnPreview(None)
        elif event.GetKeyCode() == 27:
            self.OnExit(None)
        
        event.Skip()    
        
        
    def OnMove(self, event):
        
        pos = event.GetPosition()
        
        # метод PositionFromPoint для asci версии wx, где не надо использовать self.getAbsolutePosition()
        index = self.editor.PositionFromPointClose(pos.x, pos.y)
        
        if index == -1 or not index:
            self.editor.SetToolTipString('')
            return
        
        self.parseTextForMarks()
        
        text = self.editor.GetText()
        
        position = self.getAbsolutePosition(index)
        
        mark, (left, right) = self.mouseOverTag(position)
        
        if mark is not None and left <= position <= right:
            if mark in self.intPrint2000:
                self.editor.SetToolTipString(self.intPrint2000[mark])
            elif mark in self.userMarks:
                value = self.userMarks[mark].split('*')
                self.editor.SetToolTipString(value[0])
            elif mark == '<BAR>':
                self.editor.SetToolTipString(u'Штрих-код')
            else:
                help = u'Метка ' + mark + u' не определена в словаре'
                self.editor.SetToolTipString(help)
        else:
            self.editor.SetToolTipString('')
            
    def getAbsolutePosition(self, pos):

        text = self.editor.GetText()
        
        relativePosition = 0
        absolutePosition = 0
        
        for simbol in text:
            absolutePosition += 1
            code = ord(simbol)
            
            if 0 < code < 128:
                relativePosition += 1
            elif 128 <= code < 2048:
                relativePosition += 2
            elif 2048 <= code < 65536:
                relativePosition += 3
            
            if relativePosition == pos:
                break
            if relativePosition > pos:
                print '---VERY BAD with length in method getAbsolutePosition in editor'
        else:
            print '---VERY BAD 2 with length in method getAbsolutePosition in editor'
            
        return absolutePosition - 1
        
    
    def mouseOverTag(self, position):
        # Возвращает имя метки и ее позицию если курсор стоит над ней в виде (mark, (left, right)) иначе None
        # Возвращаем позицию, т.к. за меткой может быть закреплено несколько позиций, и чтоб не парсить второй раз
        
        for mark, positions in self.position.items():
            
            for left, right in positions:
                if left <= position <= right:
                    return mark, (left, right - 2)
                    
        return (None, (None, None) )
        
                
        
    def parseTextForMarks(self):
        text = self.editor.GetText()
        
        posOpen, posClose = (None, None)
        
        result = {}
        
        for index, simbol in enumerate(text, start=1):
            
            if simbol == '<':
                posOpen = index
                
            # Правую записываем в случае если левая существует
            if simbol == '>' and posOpen is not None:
                posClose = index
            
            # Записываем только если оба флага существуют и расстояния между ними не более 5 символов
            if posOpen and posClose and (posClose-posOpen) <=5:
                
                key = text[posOpen-1:posClose]
                
                
                if key in result:
                    result[key].append( (posOpen, posClose) )
                else:
                    result[key] = [ (posOpen, posClose) ]
                             
                posOpen, posClose = (None, None)
        
        self.position = result
        
    def OnAdd(self, event):
        
        PopupEditor(self)
        self.Enable(False)
        
    def OnEdit(self, event):
        
        PopupEditor(self, self.listctrl.GetItem(self.selectedRow, 0).GetText())
        self.Enable(False)
        
    def OnDelete(self, event):
        
        mark = self.listctrl.GetItem(self.selectedRow, 0).GetText()
        title = self.listctrl.GetItem(self.selectedRow, 1).GetText()
        code = self.listctrl.GetItem(self.selectedRow, 2).GetText()
        
        text = u'Вы действительно хотите удалить ' + str(mark[2:-1]) + u' метку: "' + title + u'" c кодом: "' + code + '"?'
        
        dlg = wx.MessageDialog(None, text, u'Подтверждение удаления', wx.YES_NO | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()
        
        if res == wx.ID_YES:
            self.listctrl.DeleteItem(self.selectedRow)
            
            if mark in self.userMarks:
                self.userMarks.pop(mark)
        
            if self.model.objConfig.has_option('userMarks', mark[2:-1]):
                self.model.objConfig.remove_option('userMarks', mark[2:-1])
                self.model.objConfig.save()
        
    def onIDLE(self, event):
        
        if self.panel.GetSize() != self.splitter.GetSize():
            self.splitter.SetSize(self.panel.GetSize())
        
        self.editor.SetSize(self.panelEditor.GetSize())
        self.listctrl.SetSize((self.panelDictionary.GetSize().x - 10, self.panelDictionary.GetSize().y - 35))
        
        
        self.btnAdd.SetPosition((5, self.GetSize().y - 85))
        self.btnEdit.SetPosition((85, self.GetSize().y - 85))
        self.btnDelete.SetPosition((165, self.GetSize().y - 85))
        
    def OnSelectedItem(self, event):
        
        self.selectedRow = event.GetIndex()
        self.btnEdit.Enable()
        self.btnDelete.Enable()
        
    def OnDeselectedItem(self, event):
        
        self.selectedRow = -1
        self.btnEdit.Disable()
        self.btnDelete.Disable()
        
    def OnClose(self, event):
        
        self.parent.parent.Enable(True)
        event.Skip()

class PopupEditor(wx.Frame):
    def __init__(self, parent, markEdit = None):
        
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, size = (400, 250), style = style)
        self.Center()
        self.parent = parent
        self.markEdit = markEdit
        self.setting = parent.setting
        
        self.panel = wx.Panel(self, -1, size = self.GetSize())
        self.panel.SetBackgroundColour(self.setting['popupBackColour'])
        
        self.panel.Bind(wx.EVT_MOTION, self.OnMouse, self.panel)
        
        self.panelTop = wx.Panel(self.panel, -1, pos = (5, 5),  size = (390, 240))
        self.panelTop.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.panelTop.Bind(wx.EVT_MOTION, self.OnMouse, self.panelTop)
        
        self.markStatic = wx.StaticText(self.panelTop, -1, u'Номер метки:', (50, 42))
        self.markChoice = wx.Choice(self.panelTop, -1, pos=(120, 40), size=(60, -1)) # , choices = self.listMarks
        self.markChoice.SetSelection(0)
        
        self.mark = wx.StaticText(self.panelTop, -1, u'Название метки:', (33, 77))
        self.markCtrl = wx.TextCtrl(self.panelTop, -1, '', (120, 75), (250, 20))
        
        self.code = wx.StaticText(self.panelTop, -1, u'Код метки:', (61, 113))
        self.codeCtrl = wx.TextCtrl(self.panelTop, -1, '', (120, 110), (250, 20))
        
        self.btnHelp = wx.Button(self.panelTop, -1, u'Справка', (5, 180)) # (310, 180)
        self.btnHelp.Bind(wx.EVT_BUTTON, self.OnHelp, self.btnHelp)
        self.btnHelp.SetBackgroundColour(self.setting['popupTopColour'])
        
        titleAdd = u'Сохранить' if markEdit is not None else u'Добавить'
        
        btnClose = wx.Button(self.panelTop, -1, u'Отмена', (5, 210))
        btnClose.Bind(wx.EVT_BUTTON, self.OnClose, btnClose)
        
        btnClose.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.btnAdd = wx.Button(self.panelTop, -1, titleAdd, (310, 210))
        self.btnAdd.Bind(wx.EVT_BUTTON, self.OnInsert, self.btnAdd)
        self.btnAdd.SetBackgroundColour(self.setting['popupTopColour'])
        
        # Надо заполнить список меток. Выдаем диапазон 1-100 кроме тек которые уже заняты busyMarks и + markEdit (если задан)
        
        busyMarks = self.parent.userMarks.keys()
        
        self.listMarks = [ '<M' + str(i) + '>' for i in range(1, 100) if '<M' + str(i) + '>' not in busyMarks]
        
        # Если режим редактирования, включаем редактируемый в список
        if self.markEdit is not None:
            self.listMarks.append(self.markEdit)
        
        self.listMarks.sort(key = lambda x: int(x[2:-1]))
        
        self.markChoice.SetItems(self.listMarks)
        
        if self.markEdit is not None:
            self.markChoice.SetSelection(self.listMarks.index(self.markEdit))
            self.markCtrl.SetValue( self.parent.listctrl.GetItem(self.parent.selectedRow, 1).GetText() )
            self.codeCtrl.SetValue( self.parent.listctrl.GetItem(self.parent.selectedRow, 2).GetText() )
        else:
            self.markChoice.SetSelection(0)
        
        self.valid = set(string.digits)
        self.valid.add(' ')
        self.valid.add(';')
        
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
    
    
    def OnInsert(self, event):
        
        def MessageDialogError(text):
            dlg = wx.MessageDialog(None, text, u'Ошибка добавления', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        
        def insert(index, mark, name, code):
            # В таблицу
            self.parent.listctrl.InsertStringItem(index, mark)
            self.parent.listctrl.SetStringItem(index, 1, name)
            self.parent.listctrl.SetStringItem(index, 2, code)
            # В конфигурационный файл
            self.parent.model.objConfig.set('userMarks', mark[2:-1], name + '*' + code)
            self.parent.model.objConfig.save()
            # В внутренний словарь (чтоб сразу отображались изменения)
            self.parent.userMarks[mark] = name
        
        def remove(mark):
            # Из таблицы
            self.parent.listctrl.DeleteItem(self.parent.selectedRow)
            # Из конфигурационного файла
            self.parent.model.objConfig.remove_option('userMarks', mark[2:-1])
            self.parent.model.objConfig.save()
            # Из внутреннего словаря (чтоб сразу отображались изменения)
            self.parent.userMarks.pop( mark )
            
        def where(id):
            # Определяет куда вставлять в таблице (чтоб всю таблицу не перезагружать)
            temp = [ self.parent.listctrl.GetItem(row, 0).GetText() for row in range(self.parent.listctrl.GetItemCount()) ]
            temp = [ int(mark[2:-1]) for mark in temp ]
            temp.append(id)
            temp.sort()
            return temp.index(id)
            
        # Перед добавлением в listctrl проверяем установлено ли название и валидное ли поле кода
        
        mark = self.listMarks[ self.markChoice.GetSelection() ]
        title = self.markCtrl.GetValue()
        code = self.codeCtrl.GetValue()
        
        if not title:
            MessageDialogError(u'Вы не установили название метки')
            return
        
        if '*' in title:
            MessageDialogError(u'Запрещено использовать в названии метки символ звездочки \'*\'')
            return
        
        if not code:
            MessageDialogError(u'Вы не установили код метки')
            return
        else:
            # Поле заполнено, проверяем на валидность
            
            result = set(code[:]) - self.valid
            
            if result:
                text = u'В поле ввода \'код метки\' допустимы только цифры, пробел и точка с запятой, но были обнаружены следующие запрещенные символы: \n'
                for index, item in enumerate(result, start = 1):
                    text += str(index) + ' - "' + item + '"\n'
                text += u'\nДля получения информации воспользуйтесь подсказкой \'Помощь\''
                MessageDialogError(text)
                return
        
        if self.markEdit is not None:
            markOld = self.parent.listctrl.GetItem(self.parent.selectedRow, 0).GetText()
            remove(markOld)
            insert( where(int(mark[2:-1])), mark, title, code )
        else:
            insert( where(int(mark[2:-1])), mark, title, code )
            
        self.OnClose(None)
        
    def OnClose(self, event):
        
        self.parent.Enable()
        self.Close()
        
    def OnHelp(self, event):
        text = u'При добавлении кода в систему необходимо установить номер метки, называние метки и код метки. Значение метки (в виде кода) '\
               u'динамически вставляется при отправке отчета на печать. Для использования доступно 99 меток, т.е. от <M1> до <M99>\n\n'\
               u'Название метки не используется при печати и предназначено для пользователя (для отличия одного кода от другого)\n'\
               u'Код метки - управляющая последовательность, предназначенная для матричного принтера. Т.е. при печати на места меток вставляются коды.\n\n'\
               u'-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n'\
               u'ПРАВИЛА ВВОДА КОДА.\n\n'\
               u'При вводе кода учтите, что коды вводяться через пробел в десятиричной системе счисления. Для ввода нескольких команд используйте разделитель ';'. '\
               u'Т.е. для ввода доступны следующие символы: все цифры, пробел и разделитель (;). При вводе других символов произойдет ошибка ввода.\n\n'\
               u'-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n'\
               u'ПРИМЕРЫ ВВОДА РАЗЛИЧНЫХ КОМАНД\n\n'\
               u'Пример №1. Установим границы печати со 2 колонки по 153.\n'\
               u'Код команды в 10 системе счисления (27 88 2 153)\n'\
               u'В поле ввода нужно ввести:27 88 2 153\n\n'\
               u'Пример №2. Пример ввода нескольких команд. Установим межстрочное расстояние, после чего установим границы страницы.\n'\
               u'Поскольку код установки границ мы рассматривали, рассмотрим установку межстрочного расстояния\n'\
               u'Код команды 27 65 n, где n - отношение n/72. Возьмем к примеру n = 4\n'\
               u'Код команды в 10 системе счисления (27 65 4)\n'\
               u'В итоге в поле ввода нужно ввести:27 65 4;27 88 2 153\n\n'
     
        dlg = wx.MessageDialog(None, text, u'Справочная информация о добавлении метки', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        