# -*- coding: utf-8 -*- 

import wx
import copy
import os

from Editor import Editor, PopupEditor
        
class PanelSettingTemplate(wx.Panel):
    def __init__(self, parent):
        
        self.parent = parent
        self.model = self.parent.model
        self.setting = self.parent.setting
        # Для отслеживания выбранной строки мышью
        self.selectedRow = -1
        
        wx.Panel.__init__(self, self.parent.PanelMain, size = self.parent.PanelMain.GetSize())
        self.SetBackgroundColour(self.setting['colour'])
        
        self.backPanel = wx.Panel(self, pos = (10,5), size=(485, 320))
        self.backPanel.SetBackgroundColour(self.setting['colour'])
        
        self.listctrl = wx.ListCtrl(self.backPanel, size = (485, 280), style=wx.LC_REPORT)
        self.listctrl.SetBackgroundColour(self.setting['colour'])
        
        self.listctrl.InsertColumn(0, '', wx.LIST_FORMAT_LEFT, 0)
        self.listctrl.InsertColumn(1, u'Название', wx.LIST_FORMAT_LEFT, 205)
        self.listctrl.InsertColumn(2, u'Файл', wx.LIST_FORMAT_LEFT, 200)
        self.listctrl.InsertColumn(3, u'Статус', wx.LIST_FORMAT_CENTER, 60)
        
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectedItem)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnDeselectedItem)
        
        self.il = wx.ImageList(16, 16, True)
        
        self.image_no = self.il.Add(wx.Image(self.setting['iconFalse'], wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.image_yes = self.il.Add(wx.Image(self.setting['iconTrue'], wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        
        templates = copy.deepcopy(self.model.objConfig.items('templates'))
        templates.sort( key = lambda x: x[0] )
        
        # Сделаем проверочку чтоб было 2 значения в записи конфига для шаблонов
        for index, (name, value) in enumerate(templates[:]):
            data = value.split('*')
            if len(data) != 2:
                templates[index] = (name, '0*0')
                self.model.obgLoger.error(u'шаблон "' + name + u'" иммет некоректную запись, путь к шаблону и статус для него обнулится')
            try:
                int(data[1])
            except ValueError:
                templates[index] = (name, '0*0')
            
        # Заносим информацию о шаблонах в таблицу
        for index, (name, value) in enumerate(templates):
            path, status = value.split('*')
            self.listctrl.InsertStringItem(index, '')
            self.listctrl.SetStringItem(index, 1, name)
            self.listctrl.SetStringItem(index, 2, path)
                
            if int(status):
                self.listctrl.SetItemColumnImage(index, 3, self.image_yes)
            else:
                self.listctrl.SetItemColumnImage(index, 3, self.image_no)
            
        
        self.listctrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        
        self.btnProperties = wx.Button(self.backPanel, -1, u'Свойства', (5, 295), name = 'btnProperties')
        self.btnProperties.Bind(wx.EVT_BUTTON, self.OnProperties, self.btnProperties)
        self.btnProperties.SetBackgroundColour(self.setting['colour'])
        self.btnProperties.Disable()
        
        self.btnEdit = wx.Button(self.backPanel, -1, u'Редактировать шаблон', (85, 295), name = 'btnEdit')
        self.btnEdit.Bind(wx.EVT_BUTTON, self.OnEdit, self.btnEdit)
        self.btnEdit.SetBackgroundColour(self.setting['colour'])
        self.btnEdit.Disable()
        
    def OnProperties(self, event):
        PopupTemplate(self, self.selectedRow)
        self.parent.Enable(False)
        
    def OnEdit(self, event):
        
        name = self.listctrl.GetItem(self.selectedRow, 1).GetText()
        file = self.listctrl.GetItem(self.selectedRow, 2).GetText()
        
        # По хорошему проверить надо существование файла
        
        if not os.path.isfile('.\\templates\\' + file):
            text = u'Файл ".\\templates\\' + file + u'" не найден для "' + name + u'" установите путь к существующему файлу'
            title = u'Ошибка поиска'
            dlg = wx.MessageDialog( None, text, title, wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            
            # Обнуление в таблице
            self.listctrl.SetStringItem(self.selectedRow, 2, '')
            self.listctrl.SetItemColumnImage(self.selectedRow, 3, self.image_no)
            # Обнуление в конфиге
            
            if self.model.objConfig.has_option('templates', name):
                self.model.objConfig.set('templates', name, '*0')
                self.model.objConfig.save()
        else:
            Editor(self, self.listctrl.GetItem(self.selectedRow, 1).GetText(), file)
            self.parent.Enable(False)
        
    def OnSelectedItem(self, event):
        self.btnProperties.Enable()
        self.selectedRow = event.GetIndex()
        
        if self.listctrl.GetItem(self.selectedRow, 3).GetImage():
            self.btnEdit.Enable()
        else:
            self.btnEdit.Disable()
        
    def OnDeselectedItem(self, event):
        self.selectedRow = -1
        
        
class PopupTemplate(wx.Frame):
    def __init__(self, parent, markEdit):
        
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED  )
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
        
        self.name = wx.StaticText(self.panelTop, -1, u'Название:', (20, 42))
        self.nameCtrl = wx.TextCtrl(self.panelTop, -1, "", (85, 42), (200, 20))
        self.nameCtrl.SetValue( self.parent.listctrl.GetItem(self.markEdit, 1).GetText() )
        self.nameCtrl.Disable()
        
        self.file = wx.StaticText(self.panelTop, -1, u'Файл:', (46, 78))
        self.fileCtrl = wx.TextCtrl(self.panelTop, -1, '', (85, 77), (200, 20))
        self.fileCtrl.SetValue( self.parent.listctrl.GetItem(self.markEdit, 2).GetText() )
        
        self.btnDialog = wx.Button(self.panelTop, -1, u'Обзор', (300, 74))
        self.btnDialog.Bind(wx.EVT_BUTTON, self.OnReview, self.btnDialog)
        self.btnDialog.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.status = wx.StaticText(self.panelTop, -1, u'Статус:', (26, 112))
        self.statusBox = wx.CheckBox(self.panelTop, -1, '', (85, 115))
        
        if self.parent.listctrl.GetItem(self.markEdit, 3).GetImage():
            self.statusBox.SetValue(1)
        else:
            self.statusBox.SetValue(0)
        
        font = wx.Font(10, 74, 93, wx.NORMAL)
        self.name.SetFont(font)
        self.file.SetFont(font)
        self.status.SetFont(font)
        
        btnClose = wx.Button(self.panelTop, -1, u'Отмена', (5, 210))
        btnClose.Bind(wx.EVT_BUTTON, self.OnClose, btnClose)
        btnClose.SetBackgroundColour(self.setting['popupTopColour'])
        
        btnSave = wx.Button(self.panelTop, -1, u'Сохранить', (310, 210))
        btnSave.Bind(wx.EVT_BUTTON, self.OnSave, btnSave)
        btnSave.SetBackgroundColour(self.setting['popupTopColour'])
        
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
        
    def OnReview(self, event):
        
        self.dlg = wx.FileDialog(self, message=u'Выбор шаблона', defaultDir='.\\templates', defaultFile='', wildcard='*.*', style=wx.OPEN)
        if self.dlg.ShowModal() == wx.ID_OK:
            fileNamePath = self.dlg.GetFilename()
            self.fileCtrl.SetValue(fileNamePath)
        
    
    def OnSave(self, event):
        
        def MessageDialogError(text, title, flag):
            dlg = wx.MessageDialog( None, text, title, flag )
            dlg.ShowModal()
            dlg.Destroy()
        
        name = self.nameCtrl.GetValue()
        file = self.fileCtrl.GetValue()
        status = self.statusBox.GetValue()
        
        # Проверяем существование файла (если установлен)
        if file and not os.path.isfile('.\\templates\\' + file):
            text = u'Файла "' + file + u'" нет в директории .\\templates, вы хотите создать его?'
            
            dlg = wx.MessageDialog( None, text, u'Файла не существует', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_ERROR )
            res = dlg.ShowModal()
            dlg.Destroy()
            
            if res == wx.ID_NO:
                MessageDialogError(u'Выберите существующий файл', u'Файла не существует', wx.OK | wx.ICON_INFORMATION)
                return
                
            elif res == wx.ID_YES:
                with open('.\\templates\\' + file, 'w'):
                    print 
                    
        # В противном случше обнуляем статус, если активный
        if not file and status:
            status = 0
        
        # Отображаем измения в таблице
        
        self.parent.listctrl.SetStringItem(self.markEdit, 2, file)
        if status:
            self.parent.listctrl.SetItemColumnImage(self.markEdit, 3, self.parent.image_yes)
        else:
            self.parent.listctrl.SetItemColumnImage(self.markEdit, 3, self.parent.image_no)
        
        # Делаем изменения в конфиге
        data = file + '*' + str( self.parent.listctrl.GetItem(self.markEdit, 3).GetImage() )
        self.parent.model.objConfig.set('templates', name,data)
        self.parent.model.objConfig.save()
        
        self.OnClose(None)
    
    def OnClose(self, event):
        self.parent.parent.Enable()
        self.Close()
        
