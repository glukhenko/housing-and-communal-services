# -*- coding: utf-8 -*- 

import wx

class PanelUser(wx.Panel):
    def __init__(self, parent, ID=-1, label='', pos=wx.DefaultPosition):
        
        self.parent = parent
        self.setting = self.parent.setting
        self.model = self.parent.model
        
        wx.Panel.__init__(self, self.parent.PanelMain, ID, pos, size = self.parent.PanelMain.GetSize()) #, wx.NO_BORDER
        
        self.selectedRow = None
        
        self.SetBackgroundColour(self.setting['colour'])
        
        self.backPanel = wx.Panel(self, pos = (10,5), size=(485, 320))
        self.backPanel.SetBackgroundColour(self.setting['colour'])
        
        self.users = [ self.model.objEncryption.decoding(value) for key, value in self.model.objConfig.items('users') if self.model.objEncryption.decoding(value) is not None ]
        
        self.users.sort( key = lambda x: x[0].lower())
        
        self.listctrl = wx.ListCtrl(self.backPanel, size = (485, 280), style=wx.LC_REPORT)
        self.listctrl.SetBackgroundColour(self.setting['colour'])
        
        self.listctrl.InsertColumn(0, '', wx.LIST_FORMAT_LEFT, 0)
        self.listctrl.InsertColumn(1, u'Имя', wx.LIST_FORMAT_LEFT, 160)
        self.listctrl.InsertColumn(2, u'Пароль', wx.LIST_FORMAT_LEFT, 155)
        self.listctrl.InsertColumn(3, u'Статус', wx.LIST_FORMAT_CENTER, 165)
        
        for index, (login, psw, status) in enumerate(self.users):
            
            self.listctrl.InsertStringItem(index, '')
            self.listctrl.SetStringItem(index, 1, login)
            self.listctrl.SetStringItem(index, 2, psw)
            self.listctrl.SetStringItem(index, 3, status)
            
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectedItem)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnDeselectedItem)
        
        self.btnAdd = wx.Button(self.backPanel, -1, u'Добавить', (5, 295), name = 'btnAdd')
        self.btnAdd.Bind(wx.EVT_BUTTON, self.OnAdd, self.btnAdd)
        self.btnAdd.SetBackgroundColour(self.setting['colour'])
        
        self.btnProperties = wx.Button(self.backPanel, -1, u'Свойства', (85, 295), name = 'btnProperties')
        self.btnProperties.Bind(wx.EVT_BUTTON, self.OnProperties, self.btnProperties)
        self.btnProperties.SetBackgroundColour(self.setting['colour'])
        self.btnProperties.Disable()
        
        self.btnDelete = wx.Button(self.backPanel, -1, u'Удалить', (165, 295), name = 'btnDelete')
        self.btnDelete.Bind(wx.EVT_BUTTON, self.OnDelete, self.btnDelete)
        self.btnDelete.SetBackgroundColour(self.setting['colour'])
        self.btnDelete.Disable()
        
    def OnAdd(self, event):
        
        self.parent.Disable()
        PopupUser(self)
        
    def OnProperties(self, event):
        
        self.parent.Disable()
        PopupUser(self, self.selectedRow)
        
    def OnDelete(self, event):
        
        def convertEnd(value):
            dictionary = {u'Администратор' : u'администратора',
                          u'Пользователь'  : u'пользователя',
                          u'Ограниченный пользователь' : u'ограниченного пользователя'
                            }
            return dictionary[value]
        
        name = self.listctrl.GetItem(self.selectedRow, 1).GetText()
        psw = self.listctrl.GetItem(self.selectedRow, 2).GetText()
        status = self.listctrl.GetItem(self.selectedRow, 3).GetText()
        
        content = u'Вы действительно хотете удалить ' + convertEnd(status) + u' "' + name  + u'" из программы?"'
        dlg = wx.MessageDialog(None, content, u'Запрос удаления данных', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_ERROR)
        
        res = dlg.ShowModal()
        dlg.Destroy()
        
        if res == wx.ID_YES:
            # Из таблицы
            self.listctrl.DeleteItem(self.selectedRow)
            # Из списка
            id = self.model.objConfig.getIdUser(name, psw, status)
            self.model.objConfig.remove_option('users', id)
            self.model.objConfig.save()
            
    def OnSelectedItem(self, event):
        
        self.btnProperties.Enable()
        self.btnDelete.Enable()
        self.selectedRow = event.GetIndex()
        
    def OnDeselectedItem(self, event):
        
        self.btnProperties.Disable()
        self.btnDelete.Disable()
        self.selectedRow = -1
    
class PopupUser(wx.Frame):
    def __init__(self, parent, rowEdit = None):
        
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, size = (400, 250), style = style)
        self.Center()
        self.parent = parent
        self.rowEdit = rowEdit
        self.setting = self.parent.setting
        self.model = self.parent.model
        
        self.panel = wx.Panel(self, -1, size = self.GetSize())
        self.panel.SetBackgroundColour(self.setting['popupBackColour'])
        
        self.panel.Bind(wx.EVT_MOTION, self.OnMouse, self.panel)
        
        self.panelTop = wx.Panel(self.panel, -1, pos = (5, 5),  size = (390, 240))
        self.panelTop.SetBackgroundColour(self.setting['popupTopColour'])
        
        self.panelTop.Bind(wx.EVT_MOTION, self.OnMouse, self.panelTop)
        
        self.name = wx.StaticText(self.panelTop, -1, u'Имя:', (87, 42))
        self.nameCtrl = wx.TextCtrl(self.panelTop, -1, "", (115, 40), (200, 20))
        
        self.psw = wx.StaticText(self.panelTop, -1, u'Пароль:', (69, 82))
        self.pswCtrl = wx.TextCtrl(self.panelTop, -1, "", (115, 80), (200, 20))
        
        self.status = wx.StaticText(self.panelTop, -1, u'Статус:', (70, 122))
        ulist = [u'Ограниченный пользователь', u'Пользователь', u'Администратор']
        
        self.Uchoice = wx.Choice(self.panelTop, -1, pos=(115, 120), size = (200, -1), choices = ulist)
        self.Uchoice.SetSelection(0)
        
        btnAddEdit = wx.Button(self.panelTop, -1, u'Добавить', (310, 210))
        btnAddEdit.Bind(wx.EVT_BUTTON, self.OnAddEdit, btnAddEdit)
        btnAddEdit.SetBackgroundColour(self.setting['popupTopColour'])
        
        btnClose = wx.Button(self.panelTop, -1, u'Отмена', (10, 210))
        btnClose.Bind(wx.EVT_BUTTON, self.OnClose, btnClose)
        btnClose.SetBackgroundColour(self.setting['popupTopColour'])
        
        if rowEdit is not None:
            
            name = self.parent.listctrl.GetItem(self.rowEdit, 1).GetText()
            self.nameCtrl.SetValue(name)
            psw = self.parent.listctrl.GetItem(self.rowEdit, 2).GetText()
            self.pswCtrl.SetValue(psw)
            status = self.parent.listctrl.GetItem(self.rowEdit, 3).GetText()
            self.Uchoice.SetSelection(ulist.index(status))
            btnAddEdit.SetLabel(u'Сохранить')
            
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
    
    def OnAddEdit(self, event):
        
        def MessageDialogError(text):
            dlg = wx.MessageDialog(None, text, u'Ошибка при работе с пользователем', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        
        def add(name, password, status):
            index = where(name)
            # В таблицу
            self.parent.listctrl.InsertStringItem(index, '')
            self.parent.listctrl.SetStringItem(index, 1, name)
            self.parent.listctrl.SetStringItem(index, 2, password)
            self.parent.listctrl.SetStringItem(index, 3, status)
            # В конфигурационный файл, берем id = max + 1 для нового пользователя
            id = max( self.parent.model.objConfig.options('users'), key = lambda x: int(x) )
            id = str(int(id) + 1)
            self.parent.model.objConfig.set('users', id, self.model.objEncryption.coding(name, password, status))
            self.parent.model.objConfig.save()
        
        def edit(name, password, status):
            oldName = self.parent.listctrl.GetItem(self.rowEdit, 1).GetText()
            oldPassword = self.parent.listctrl.GetItem(self.rowEdit, 2).GetText()
            oldStatus = self.parent.listctrl.GetItem(self.rowEdit, 3).GetText()
            # В таблице
            self.parent.listctrl.SetStringItem(self.rowEdit, 1, name)
            self.parent.listctrl.SetStringItem(self.rowEdit, 2, password)
            self.parent.listctrl.SetStringItem(self.rowEdit, 3, status)
            # В конфигурационном файле
            id = self.parent.model.objConfig.getIdUser(oldName, oldPassword, oldStatus)
            self.parent.model.objConfig.set('users', id, self.model.objEncryption.coding(name, password, status))
            self.parent.model.objConfig.save()
            
        def where(name):
            # Определяет куда вставлять в таблице (чтоб всю таблицу не перезагружать)
            temp = [ self.parent.listctrl.GetItem(row, 1).GetText().lower() for row in range(self.parent.listctrl.GetItemCount()) ]
            temp.append(name.lower())
            temp.sort()
            return temp.index(name.lower())
        
        name = self.nameCtrl.GetValue()
        psw = self.pswCtrl.GetValue()
        status = self.Uchoice.GetStringSelection()
        
        if not name:
            MessageDialogError(u'Вы не ввели имя пользователя')
            return
        
        if not psw:
            MessageDialogError(u'Вы не ввели пароль пользователя')
            return
        
        if len(name) >= 31 or len(psw) >= 31:
            MessageDialogError(u'Максимальная длина для поля ввода имени и пароля: 30 символов')
            return
        
        names = [ self.model.objEncryption.decoding(value)[0].lower() for key, value in self.model.objConfig.items('users') ]
        
        if self.rowEdit is not None:
            names.remove( self.parent.listctrl.GetItem(self.parent.selectedRow, 1).GetText().lower() )
        
        if name.lower() in names:
            MessageDialogError(u'Имя "' + name.lower() + u'" уже занято, введите другое имя')
            return
        
        if self.rowEdit is not None:
            edit(name, psw, status)
        else:
            add(name, psw, status)
        
        self.OnClose(None)
        
    def OnClose(self, event):
        self.parent.parent.Enable()
        self.Close()
        
        