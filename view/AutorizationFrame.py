# -*- coding: utf-8 -*- 

import wx

class AutorizationFrame(wx.Frame):
    def __init__(self, parent=None):

        self.parent = parent
        self.setting = dict(self.parent.objModel.objConfig.items('setting'))
        
        wx.Frame.__init__(self, None, -1, u'Авторизация', size=(300,200), style= wx.DEFAULT_FRAME_STYLE ^(wx.MAXIMIZE_BOX | wx.RESIZE_BORDER) | wx.CLIP_CHILDREN )
        self.colour = self.setting['colour']
        self.SetBackgroundColour(self.colour)
        
        self.SetIcon(wx.Icon(self.setting['icon'], wx.BITMAP_TYPE_PNG))
        
        self.panel = wx.Panel(self, -1)
        
        self.sbList = wx.StaticBox(self.panel, -1, u'Вход в программу', (5,0), size=(283, 120))
        
        textLogin = wx.StaticText(self.panel, -1, u'Логин:', pos=(34, 45))
        self.ctrlLogin = wx.TextCtrl(self.panel, -1, "", size=(114, -1), pos=(70,43))
        self.ctrlLogin.SetBackgroundColour(self.colour)
        self.ctrlLogin.SetInsertionPoint(0)
        
        textPwd = wx.StaticText(self.panel, -1, u'Пароль:', pos=(28, 70))
        self.ctrlPwd = wx.TextCtrl(self.panel, -1, '', size=(115, -1), pos=(70, 68), style=wx.TE_PASSWORD)
        self.ctrlPwd.SetBackgroundColour(self.colour)
        
        self.button = wx.Button(self.panel, -1, u'Вход', pos=(200, 68))
        self.button.SetBackgroundColour(self.colour)
        self.button.Bind(wx.EVT_BUTTON, self.OnClick)
        
        bmp = wx.Image(self.setting['logo'], wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(self.panel, -1, bmp, (60, 130))
        
        self.Refresh()
        self.Center()

    def OnClick(self, event):
        # Логин и пароль обрезается до 32 если превышает это значение
        login = self.ctrlLogin.GetValue()
        password = self.ctrlPwd.GetValue()
        if (len(login) >= 32): login = login[:31]
        if (len(password) >= 32): password = password[:31]
        if not len(login):
            self.showDialog(u'Вы не ввели логин, попробуйте снова', u'Произошла ошибка авторизации')
            return
        elif not len(password):
            self.showDialog(u'Вы не ввели пароль, попробуйте снова', u'Произошла ошибка авторизации')
            return
        
        status = self.parent.objModel.objConfig.autorization(login, password)
        
        if status is None:
            self.showDialog(u'Пользователь не найден. Проверьте правильность ввода логина и пароля.', u'Произошла ошибка авторизации')
        else:
            if not self.parent.objModel.objDB.connectExist():
                if status != u'Администратор':
                    self.showDialog(login + u'! база данных недоступна, обратитесь к администратору для устранения неполадок.', u'Произошла ошибка соединения с базой данных')
                    self.Close()
                    return
                else:
                    self.showDialog(u'Неуспешное соединение с базой данных, просмотрите настройки подключения к базе.', u'Произошла ошибка соединения с базой данных')
                    
            self.parent.user = login
            self.parent.status = status
            self.Close()
        
        
    def showDialog(self, msg, title): 
        dlg = wx.MessageDialog(None, msg, title, wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        
        