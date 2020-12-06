# -*- coding: utf-8 -*-

import wx

class PanelSettingDB(wx.Panel):
    def __init__(self, parent):
        
        self.parent = parent
        self.model = self.parent.parent.objModel
        self.setting = self.parent.setting
        
        wx.Panel.__init__(self, self.parent.PanelMain, size = self.parent.PanelMain.GetSize())
        self.SetBackgroundColour(self.setting['colour'])
        
        self.backPanel = wx.Panel(self, pos = (10,5), size=(485, 330))
        self.backPanel.SetBackgroundColour(self.setting['colour'])
        
        self.sbList = wx.StaticBox(self.backPanel, -1, u'Настройки базы данных', (5,0), size=(480, 290))
        
        names = ((u'Имя базы данных:', (104, 90)),
                 (u'Сервер базы данных:', (86, 120)),
                 (u'Имя входа:', (140, 150)),
                 (u'Пароль входа:', (121,180)),
                 )
        
        for label, pos in names:
            wx.StaticText(self.backPanel, -1, label, pos)
        
        namedb = self.model.objConfig.get('database', 'namedb')
        serverdb = self.model.objConfig.get('database', 'serverdb')
        botname, botpass, null = self.model.objEncryption.decoding( self.model.objConfig.get('database', 'bot') )
        
        self.nameDB = wx.TextCtrl(self.backPanel, -1, namedb, (200, 89), (200, 20))
        self.nameDB.SetBackgroundColour(self.setting['colour'])
        self.nameDB.Bind(wx.EVT_CHAR, self.OnChar, self.nameDB)
        
        self.serverDB = wx.TextCtrl(self.backPanel, -1, serverdb, (200, 119), (200, 20))
        self.serverDB.SetBackgroundColour(self.setting['colour'])
        self.serverDB.Bind(wx.EVT_CHAR, self.OnChar, self.serverDB)
        
        self.botName = wx.TextCtrl(self.backPanel, -1, botname, (200, 149), (200, 20))
        self.botName.SetBackgroundColour(self.setting['colour'])
        self.botName.Bind(wx.EVT_CHAR, self.OnChar, self.botName)
        
        self.botPsw = wx.TextCtrl(self.backPanel, -1, botpass, (200, 179), (200, 20))
        self.botPsw.SetBackgroundColour(self.setting['colour'])
        self.botPsw.Bind(wx.EVT_CHAR, self.OnChar, self.botPsw)
        
        self.btnSave = wx.Button(self.backPanel, -1, u'Сохранить', (400, 300))
        self.btnSave.Bind(wx.EVT_BUTTON, self.OnSave, self.btnSave)
        self.btnSave.SetBackgroundColour(self.setting['colour'])
        self.btnSave.Disable()
        
    def OnChar(self, event):
        
        self.btnSave.Enable()
        event.Skip()
        
    def OnSave(self, event):
        
        self.model.objConfig.set('database', 'namedb', self.nameDB.GetValue())
        self.model.objConfig.set('database', 'serverdb', self.serverDB.GetValue())
        bot = self.model.objEncryption.coding( self.botName.GetValue(), self.botPsw.GetValue(), u'Администратор')
        self.model.objConfig.set('database', 'bot', bot)
        self.model.objConfig.save()
        self.btnSave.Disable()
        
        
    