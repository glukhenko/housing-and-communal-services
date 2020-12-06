# -*- coding: utf-8 -*- 

import wx

class PanelFind(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        
        self.parent = parent
        self.model = self.parent.parent.objModel
        self.setting = self.parent.setting
        
        wx.Panel.__init__(self, self.parent.PanelMain, size = self.parent.PanelMain.GetSize())
        self.SetBackgroundColour(self.setting['colour'])
        
        self.backPanel = wx.Panel(self, -1, pos = (10,5), size=(485, 320))
        self.backPanel.SetBackgroundColour(self.setting['colour'])
        
        self.nb = wx.Notebook(self.backPanel)
        self.nb.SetBackgroundColour(self.setting['colour'])
        
        self.nb.AddPage(self.addressPanel(), u'Адрес')
        self.nb.AddPage(self.occPanel(), u'Номер лицевого счета')
        
        self.gridsizer = wx.GridSizer()
        self.gridsizer.Add(self.nb, 1, flag = wx.EXPAND)
        self.SetSizer(self.gridsizer)
        self.Layout()
        
    def addressPanel(self):
        
        panel = wx.Panel(self.nb)
        panel.SetBackgroundColour(self.setting['colour'])
        
        self.defaultStreet, self.defaultHouse, self.defaultFlat = self.model.objDB.getDefaultSHF()
        
        font = wx.Font(10, 74, 93, wx.NORMAL)
        
        slist = self.model.objDB.getListStreet()
        st = wx.StaticText(panel, -1, u'Улица:', pos=(105, 20))
        st.SetFont(font)
        self.Schoice = wx.Choice(panel, -1, pos=(150, 18), choices=slist)
        
        hlist = self.model.objDB.getListHouse(self.model.objDB.getIdStreet(self.defaultStreet))
        ht = wx.StaticText(panel, -1, u'Номер дома:', pos=(68, 60))
        ht.SetFont(font)
        self.Hchoice = wx.Choice(panel, -1, pos=(150,58), size = (150, -1), choices=hlist)
        
        flist = self.model.objDB.getListFlat(self.model.objDB.getIdStreet(self.defaultStreet), self.defaultHouse)
        ft = wx.StaticText(panel, -1, u'Номер квартиры:', pos=(35, 100))
        ft.SetFont(font)
        self.Fchoice = wx.Choice(panel, -1, pos=(150,98), size = (150, -1), choices=flist)
        
        button = wx.Button(panel, -1, u'Найти', pos=(320, 98))
        self.Bind(wx.EVT_BUTTON, self.OnFindAddress, button)
        button.SetBackgroundColour(self.setting['colour'])
        
        self.Schoice.Bind(wx.EVT_CHOICE, self.OnSelectStreet)
        self.Hchoice.Bind(wx.EVT_CHOICE, self.OnSelectHouse)
        
        self.Schoice.SetStringSelection(self.defaultStreet)
        self.Hchoice.SetStringSelection(self.defaultHouse)
        self.Fchoice.SetStringSelection(self.defaultFlat)
        
        return panel
        
    def OnSelectStreet(self, event):
        #При смене состояния улицы меняем список домов и квартир, и устанавливаем дому и квартире дефолтные значения
        idStreet = self.model.objDB.getIdStreet(self.Schoice.GetStringSelection())
		#получение списка домов для улицы, и установка деволтного дома для списка
        newhlist = self.model.objDB.getListHouse(idStreet)
        defaultH = self.model.objDB.getDefaultHouse(self.Schoice.GetStringSelection())
        
        self.Hchoice.Clear()
        self.Hchoice.AppendItems(newhlist)
        self.Hchoice.SetStringSelection(defaultH)
        #получение списка домов для дефолтного дома улицы, и установка дефолтной квартиры для списка
        newflist = self.model.objDB.getListFlat(idStreet, defaultH)
        defaultF = self.model.objDB.getDefaultFlat(self.Schoice.GetStringSelection(), defaultH)
        
        self.Fchoice.Clear()
        self.Fchoice.AppendItems(newflist)
        self.Fchoice.SetStringSelection(defaultF)
        
    def OnSelectHouse(self, event):
        #При смене состояния дома меняем список вкартир по новому дому и заданной улице
        newflist = self.model.objDB.getListFlat(self.model.objDB.getIdStreet(self.Schoice.GetStringSelection()), self.Hchoice.GetStringSelection())
        defaultF = self.model.objDB.getDefaultFlat(self.Schoice.GetStringSelection(), self.Hchoice.GetStringSelection())
        self.Fchoice.Clear()
        self.Fchoice.AppendItems(newflist)
        self.Fchoice.SetStringSelection(defaultF)
        
    def OnFindAddress(self, event):
        
        street = self.Schoice.GetStringSelection()
        house = self.Hchoice.GetStringSelection()
        flat = self.Fchoice.GetStringSelection()
        
        occ, f, i, o = self.model.objDB.getOCCFIOFromADDRESS(street, house, flat)
        self.parent.StartPrintDoc((occ, f, i, o, street, house, flat))
        
        
    def occPanel(self):
        
        panel = wx.Panel(self.nb)
        panel.SetBackgroundColour(self.setting['colour'])
        
        text = wx.StaticText(panel, -1, u'Номер лицевого счета:', (25, 20))
        
        font = wx.Font(10, 74, 93, wx.NORMAL)
        text.SetFont(font)
        
        self.occ = wx.TextCtrl(panel, -1, size=(70, -1), pos=(180, 20))
        find = wx.Button(panel, -1, u'Найти', pos=(260, 19))
        find.SetBackgroundColour(self.setting['colour'])
        find.Bind(wx.EVT_BUTTON, self.OnFindOcc, find)
         
        return panel
        
    def OnFindOcc(self, event):
        occ = self.occ.GetValue()
        
        if not len(occ):
            return
        
        try:
            occ = int(occ)
        except ValueError:
            msg = u'В поле ввода "Номер лицевого счета" следует вводить цифры. Попробуйте снова'
            dlg = wx.MessageDialog(None, msg, u'Ошибка ввода лицевого счета', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        if self.model.objDB.existOcc(occ):
            
            f, i, o, street, house, flat = self.model.objDB.getFIOAddressFromOCC(occ)
            self.parent.StartPrintDoc((occ, f, i, o, street, house, flat))
        else:
            msg = u'Житель с лицевым счетом "' + str(occ) + u'" не найден в базе. Обратитесь к администратору базы данных.'
            dlg = wx.MessageDialog(None, msg, u'Не найден лицевой счет', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            