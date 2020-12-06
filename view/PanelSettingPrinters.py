# -*- coding: utf-8 -*-

import wx
import copy
import threading

import re
import os
import subprocess

class PanelSettingPrinters(wx.Panel, threading.Thread):
    def __init__(self, parent):
        
        threading.Thread.__init__(self)
        
        self.parent = parent
        self.model = self.parent.model
        self.setting = self.parent.setting
        self.selectedRow = -1
        
        wx.Panel.__init__(self, self.parent.PanelMain, size = self.parent.PanelMain.GetSize())
        self.SetBackgroundColour(self.setting['colour'])
        
        self.backPanel = wx.Panel(self, -1, pos = (10,5), size=(485, 320))
        self.backPanel.SetBackgroundColour(self.setting['colour'])
        
        self.listctrl = wx.ListCtrl(self.backPanel, size = (485, 280), style=wx.LC_REPORT)
        self.listctrl.SetBackgroundColour(self.setting['colour'])
        
        self.listctrl.InsertColumn(0, '', wx.LIST_FORMAT_LEFT, 0)
        self.listctrl.InsertColumn(1, u'Имя сервера', wx.LIST_FORMAT_LEFT, 150)
        self.listctrl.InsertColumn(2, u'Имя принтера', wx.LIST_FORMAT_LEFT, 155)
        self.listctrl.InsertColumn(3, u'Скорость', wx.LIST_FORMAT_LEFT, 110)
        self.listctrl.InsertColumn(4, u'Статус', wx.LIST_FORMAT_CENTER, 50)
        
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectedItem)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnDeselectedItem)
        
        self.il = wx.ImageList(16, 16, True)
        
        self.image_no = self.il.Add(wx.Image(self.setting['iconFalse'], wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.image_yes = self.il.Add(wx.Image(self.setting['iconTrue'], wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        
        self.printers = self.model.objConfig.items('printers')
        
        self.printers.sort( key = lambda x: x[0].lower())
        
        # Сделам проверочку чтоб ключ был из 2-х значений, так же как и значение
        for index, (key, value) in enumerate(self.printers[:]):
            keys = key.split('*')
            if len(keys) != 2:
                self.model.obgLoger.error(u'принтер "' + key + u'" иммет некоректную запись, в следствие чего будет удален')
                self.printers.pop(index)
                continue
            values = value.split('*')
            if len(values) != 2:
                self.model.obgLoger.error(u'принтер "' + key + u'" иммет некоректное значение, в следствие чего будет обнулен по дефолту')
                values = ['30', '0']
                
            self.printers[index] = ( keys[0], keys[1], values[0], values[1])
                
        # Заносим в таблицу
        for index, (server, printer, speed, status) in enumerate(self.printers):
            
            self.listctrl.InsertStringItem(index, '')
            self.listctrl.SetStringItem(index, 1, server)
            self.listctrl.SetStringItem(index, 2, printer)
            self.listctrl.SetStringItem(index, 3, speed)
             
            if status == '1':
                self.listctrl.SetItemColumnImage(index, 4, self.image_yes)
            else:
                self.listctrl.SetItemColumnImage(index, 4, self.image_no)
            
        
        self.listctrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        
        self.btnAdd = wx.Button(self.backPanel, -1, u'Добавить', (5, 295), name = 'btnAdd')
        self.btnAdd.Bind(wx.EVT_BUTTON, self.OnAdd, self.btnAdd)
        
        self.btnProperties = wx.Button(self.backPanel, -1, u'Свойства', (85, 295), name = 'btnProperties')
        self.btnProperties.Bind(wx.EVT_BUTTON, self.OnProperties, self.btnProperties)
        self.btnProperties.Disable()
        
        self.btnPing = wx.Button(self.backPanel, -1, u'Пинг сервера', (285, 295), name = 'btnPing')
        self.btnPing.Bind(wx.EVT_BUTTON, self.OnPing, self.btnPing)
        self.btnPing.Disable()
        
        self.btnTestPage = wx.Button(self.backPanel, -1, u'Тестовая страница', (165, 295), name = 'btnTestPage')
        self.btnTestPage.Bind(wx.EVT_BUTTON, self.OnTestPage, self.btnTestPage)
        self.btnTestPage.Disable()
        
        self.btnDelete = wx.Button(self.backPanel, -1, u'Удалить', (405, 295), name = 'btnDelete')
        self.btnDelete.Bind(wx.EVT_BUTTON, self.OnDelete, self.btnDelete)
        self.btnDelete.Disable()
        
        self.btnAdd.SetBackgroundColour(self.setting['colour']) 
        self.btnProperties.SetBackgroundColour(self.setting['colour'])
        self.btnPing.SetBackgroundColour(self.setting['colour'])
        self.btnTestPage.SetBackgroundColour(self.setting['colour'])
        self.btnDelete.SetBackgroundColour(self.setting['colour'])
        
        
    def OnAdd(self, event):
    
        self.parent.Enable(False)
        PopupPrinter(self)
        
    def OnProperties(self, event):
    
        self.parent.Enable(False)
        PopupPrinter(self, self.selectedRow)

    def OnDelete(self, event):
        
        server = self.listctrl.GetItem(self.selectedRow, 1).GetText()
        printer = self.listctrl.GetItem(self.selectedRow, 2).GetText()
        
        text = u'Вы действительно хотите удалить сетевой принтер "' + printer + u'" который установлен на сервере "' + server + '"?'
        
        dlg = wx.MessageDialog(None, text, u'Подтверждение удаления', wx.YES_NO | wx.ICON_INFORMATION)
        res = dlg.ShowModal()
        dlg.Destroy()
        
        if res == wx.ID_YES:
            
            # Удаляем в таблице
            self.listctrl.DeleteItem(self.selectedRow)
            # Из конфигурационного файла
            self.parent.model.objConfig.remove_option('printers', server + '*' + printer )
            self.parent.model.objConfig.save()
            
        
    def run(self):
        
        # Пинганем сервак принтера
        
        row = self.selectedRow
        
        self.parent.Enable(False)
        def MessageDialogInfo(msg):
            dlg = wx.MessageDialog(None, msg, u'Состояние сети', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        
        def MessageDialogError(msg):
            dlg = wx.MessageDialog(None, msg, u'Состояние сети', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        
        def offPrinter():
            
            server = self.listctrl.GetItem(row, 1).GetText()
            printer = self.listctrl.GetItem(row, 2).GetText()
            time = self.listctrl.GetItem(row, 3).GetText()
            status = self.listctrl.GetItem(row, 4).GetImage()
            
            if status:
                # Заменяем в таблице
                self.listctrl.SetItemColumnImage(row, 4, self.image_no)
                # Заменяем в конфигурационном файле
                self.model.objConfig.set('printers', server + '*' + printer, time + '*0')
                self.model.objConfig.save()
            
        host = self.listctrl.GetItem(self.selectedRow, 1).GetText()
        self.parent.statusBar.SetStatusText(u'Проверка связи с ' + host + u', подождите', 0)
        stat, msg = self.ping(host)
        
        if stat:
            MessageDialogInfo(msg)
        else:
            MessageDialogError(msg)
            offPrinter()
        
        self.parent.Enable()
        self.parent.statusBar.SetStatusText(u'', 0)
        threading.Thread.__init__(self)
        
    def ping(self, host):
        
        ping = subprocess.Popen(
            ["ping", host.encode('cp1251')],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            shell = True
        )
        
        out, error = ping.communicate()
        
        regular = re.compile('[\d]{1,3}%')
        result = regular.findall(out)
        
        if not len(result):
            return 0, host + u' не найден в сети'
        else:
            if result[0] == '0%':
                return 1, u'Стабильное соединение с ' + host
            elif result[0] == '100%':
                return 0, u'Соединение с ' + host + u' отсутствует'
            else:
                return 1, u'Нестабильное соединение с ' + host
        
    def OnPing(self, event):
        
        self.btnPing.Disable()
        self.start()
        
    def OnTestPage(self, event):
        
        server = self.listctrl.GetItem(self.selectedRow, 1).GetText()
        printer = self.listctrl.GetItem(self.selectedRow, 2).GetText()
        
        content = u'Тестовая страница для матричного принтера, посланная из программы работы с матричным принтером\n\n'
        
        content += u'Имя сервера к которому подключен сетевой принтер: ' + server + '\n'
        content += u'Имя сетевого принтера: ' + printer + '\n\n'
        content += u'Начальник проекта Дашко Андрей Валерьевич\n'
        content += u'Разработчик Глухенко Антон Владимирович\n\n'
        content += u'Квадрат А, г. Салехард'
        
        with open(".\\tmp\\temp.txt", "w") as hf:
            hf.write(content.encode('cp1251'))
            
        self.model.printing(printer)
        
    def OnSelectedItem(self, event):
        
        self.selectedRow = event.GetIndex()
        
        self.btnProperties.Enable()
        self.btnPing.Enable()
        self.btnDelete.Enable()
        
        if self.listctrl.GetItem(self.selectedRow, 4).GetImage():
            self.btnTestPage.Enable()
        
    def OnDeselectedItem(self, event):
        
        self.selectedRow = -1
        
        self.btnProperties.Disable()
        self.btnPing.Disable()
        self.btnTestPage.Disable()
        self.btnDelete.Disable()
        
class PopupPrinter(wx.Frame, threading.Thread):
    def __init__(self, parent, markEdit = None):
        
        threading.Thread.__init__(self)
        
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED )
        wx.Frame.__init__(self, None, size = (400, 250), style = style)
        self.Center()
        self.parent = parent
        self.markEdit = markEdit
        self.setting = self.parent.setting
        
        self.panel = wx.Panel(self, -1, size = self.GetSize())
        self.panel.SetBackgroundColour(self.setting['popupBackColour'])
        
        self.panel.Bind(wx.EVT_MOTION, self.OnMouse, self.panel)
        
        self.panelTop = wx.Panel(self.panel, -1, pos = (5, 5),  size = (390, 240))
        self.panelTop.SetBackgroundColour(self.setting['popupTopColour'])
        self.panelTop.Bind(wx.EVT_MOTION, self.OnMouse, self.panelTop)
        
        self.server = wx.StaticText(self.panelTop, -1, u'Имя сервера', (15, 42))
        self.serverCtrl = wx.TextCtrl(self.panelTop, -1, "", (120, 42), (200, 20))
        self.serverCtrl.Bind(wx.EVT_CHAR, self.OnChar, self.serverCtrl)
        
        self.printer = wx.StaticText(self.panelTop, -1, u'Имя принтера', (15, 78))
        self.printerCtrl = wx.TextCtrl(self.panelTop, -1, "", (120, 77), (200, 20))
        
        self.speed = wx.StaticText(self.panelTop, -1, u'Скорость (сек.)', (15, 114))
        
        self.speedSC = wx.SpinCtrl(self.panelTop, -1, '', (120, 113), (50, -1))
        self.speedSC.SetRange(0, 60)
        self.speedSC.SetValue(30)
        
        self.response = wx.StaticText(self.panelTop, -1, u'', (150, 149))
        
        self.status = wx.StaticText(self.panelTop, -1, u'Статус', (15, 148))
        self.statusBox = wx.CheckBox(self.panelTop, -1, '', (120, 151))
        
        self.statusBox.Bind(wx.EVT_CHECKBOX, self.OnSwitch, self.statusBox)
        
        font = wx.Font(10, 74, 93, wx.NORMAL)
        self.server.SetFont(font)
        self.printer.SetFont(font)
        self.speed.SetFont(font)
        self.status.SetFont(font)
        
        self.btnClose = wx.Button(self.panelTop, -1, u'Отмена', (5, 210))
        self.btnClose.Bind(wx.EVT_BUTTON, self.OnClose, self.btnClose)
        self.btnClose.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.btnAddEdit = wx.Button(self.panelTop, -1, u'Добавить', (310, 210))
        self.btnAddEdit.Bind(wx.EVT_BUTTON, self.OnAddEdit, self.btnAddEdit)
        self.btnAddEdit.SetBackgroundColour(self.setting['popupTopColour'])
        
        if markEdit is not None:
            
            server = self.parent.listctrl.GetItem(markEdit, 1).GetText()
            self.serverCtrl.SetValue(server)
            
            printer = self.parent.listctrl.GetItem(markEdit, 2).GetText()
            self.printerCtrl.SetValue(printer)
            
            speed = self.parent.listctrl.GetItem(markEdit, 3).GetText()
            self.speedSC.SetValue(int(speed))
            
            if self.parent.listctrl.GetItem(markEdit, 4).GetImage():
                self.statusBox.SetValue(True)
            else:
                self.statusBox.SetValue(False)
            
            self.btnAddEdit.SetLabel(u'Сохранить')
        
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
        
    def OnChar(self, event):
        
        if self.statusBox.GetValue():
            self.statusBox.SetValue(False)
        
        event.Skip()
        
    def run(self):
        
        self.btnClose.Disable()
        self.btnAddEdit.Disable()
        
        status = self.statusBox.GetValue()
        
        def MessageDialogError(text):
            dlg = wx.MessageDialog(None, text, u'Ошибка настройки принтера', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        
        if status:
            server = self.serverCtrl.GetValue()
            stat, msg = self.parent.ping(server)
            
            if stat:
                self.response.SetLabel(u'сервер доступен')
            else:
                MessageDialogError(u'Сервер ' + server + u' недоступен, принтер не может быть активирован')
                self.statusBox.SetValue(0)
                self.response.SetLabel('')
                
        self.btnClose.Enable()
        self.btnAddEdit.Enable()
                
        threading.Thread.__init__(self)
        
    def OnSwitch(self, event):
        
        if self.statusBox.GetValue():
        
            server = self.serverCtrl.GetValue()
            response = u'Проверка связи с ' + server
            
            if len(response) > 30:
                response = response[:28] + '...'
            
            self.response.SetLabel(response)
                
            self.start()
    
    def OnAddEdit(self, event):
        
        def MessageDialogError(text):
            dlg = wx.MessageDialog(None, text, u'Ошибка настройки принтера', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        
        def insert(server, printer, time, status):
            # В таблицу
            index = self.parent.listctrl.GetItemCount()
            self.parent.listctrl.InsertStringItem(index, '')
            self.parent.listctrl.SetStringItem(index, 1, server)
            self.parent.listctrl.SetStringItem(index, 2, printer)
            self.parent.listctrl.SetStringItem(index, 3, time)
            
            if status:
                self.parent.listctrl.SetItemColumnImage(index, 4, self.parent.image_yes)
            else:
                self.parent.listctrl.SetItemColumnImage(index, 4, self.parent.image_no)
            
            # В конфигурационный файл
            self.parent.model.objConfig.set('printers', server + '*' + printer, time + '*' + str(status))
            self.parent.model.objConfig.save()
        
        def remove(server, printer):
            # Из таблицы
            self.parent.listctrl.DeleteItem(self.parent.selectedRow)
            # Из конфигурационного файла
            self.parent.model.objConfig.remove_option('printers', server + '*' + printer )
            self.parent.model.objConfig.save()
        
        server = self.serverCtrl.GetValue()
        printer = self.printerCtrl.GetValue()
        speed = self.speedSC.GetValue()
        status = self.statusBox.GetValue()
        
        if not server:
            MessageDialogError(u'Вы не установили имя сервера к которому подключен сетевой принтер')
            return
        
        if not printer:
            MessageDialogError(u'Вы не установили имя сетевого принтера')
            return
        
        reserved = self.parent.model.objConfig.options('printers')
        
        if self.markEdit is not None:
            oldServer = self.parent.listctrl.GetItem(self.markEdit, 1).GetText()
            oldPrinter = self.parent.listctrl.GetItem(self.markEdit, 2).GetText()
            reserved.remove(oldServer + '*' + oldPrinter)
            
        # Повтор
        if server + '*' + printer in reserved:
            MessageDialogError(u'Сетевой принтер "' + printer + u'" на сервере "' + server + u'" уже существует. Задайте другое имя для сетевого принтера')
            return
        
        if self.markEdit is not None:
            remove(server, printer)
            insert(server, printer, str(speed), int(status))
        else:
            insert(server, printer, str(speed), int(status))
            
        self.OnClose(None)
        
    def OnClose(self, event):
        self.parent.parent.Enable()
        self.Close()
        