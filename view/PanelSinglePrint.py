# -*- coding: utf-8 -*- 

import wx

from Preview import Preview

class PanelSinglePrint(wx.Panel):
    def __init__(self, parent, data):
        
        self.parent = parent
        self.setting = self.parent.setting
        self.model = self.parent.model
        
        self.occ, self.surname, self.name, self.patronymic, self.street, self.house, self.flat = data
        
        wx.Panel.__init__(self, self.parent.PanelMain, size = self.parent.PanelMain.GetSize())
        
        self.SetBackgroundColour(self.setting['colour'])
        
        data = ( (u'Номер лицевого счета:',    (25, 40)   ),
                 (str(self.occ),               (325, 40)  ),
                 (u'Фамилия:',                 (25, 60)   ),
                 (self.surname.strip()[:22],   (325, 60)  ),
                 (u'Имя:',                     (25, 80)   ),
                 (self.name.strip()[:22],      (325, 80)  ),
                 (u'Отчество:',                (25, 100)  ),
                 (self.patronymic.strip()[:22],(325, 100) ),
                 (u'Улица:',                   (25, 120)  ),
                 (self.street[:22],            (325, 120) ),
                 (u'Дом:',                     (25, 140)  ),
                 (self.house[:22],             (325, 140) ),
                 (u'Квартира:',                (25, 160)  ),
                 (self.flat[:22],              (325, 160) ),
                 (u'Тип извещения',            (25, 253)  ),
                 (u'Принтер',                  (25, 278)  ),
                )
        
        font = wx.Font(10, 74, 93, wx.NORMAL)
        
        for label, pos in data:
            st = wx.StaticText(self, -1, label, pos)
            st.SetFont(font)
        
        # Рамочка :)
        wx.StaticLine(self, -1, (15, 20), (462,1))
        wx.StaticLine(self, -1, (20, 15), (1,180))
        wx.StaticLine(self, -1, (470, 15), (1,180))
        wx.StaticLine(self, -1, (15, 190), (462,1))
        
        tlist = self.model.objConfig.options('templates')
        tlist = [ template for template in tlist if int(self.model.objConfig.get('templates', template).split('*')[-1])]
        self.Tchoice = wx.Choice(self, -1, pos = (125, 250), size = (200, -1), choices = tlist)
        self.Tchoice.SetSelection(0)
        
        plist = self.model.objConfig.options('printers')
        plist = [ printer.split('*')[-1] for printer in plist if int(self.model.objConfig.get('printers', printer).split('*')[-1]) ]
        self.Pchoice = wx.Choice(self, -1, pos=(125, 275), size = (200, -1) , choices=plist)
        self.Pchoice.SetSelection(0)
        
        self.printerBtn = wx.Button(self, -1, u'Печать', pos=(390, 280))
        self.printerBtn.SetBackgroundColour(self.setting['colour'])
        self.Bind(wx.EVT_BUTTON, self.OnPrinter, self.printerBtn)
        
    def printing(self):
        
        template = self.Tchoice.GetStringSelection()
        printer = self.Pchoice.GetStringSelection()
        
        if self.model.generateFile(self.occ, template):
            self.model.printing(printer)
        
    def OnPrinter(self, event):
        
        template = self.Tchoice.GetStringSelection()
        printer = self.Pchoice.GetStringSelection()
        
        if self.model.generateFile(self.occ, template, False):
            Preview(self)
            self.Enable(False)
            self.printerBtn.Disable()
        else:
            msg = u'Произошла ошибка. Скорей всего выбран не тот шаблон для лицевого счета.\nДля подробной информации смотрите лог.'
            dlg = wx.MessageDialog(None, msg, u'Ошибка связзанная с базой данных', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()