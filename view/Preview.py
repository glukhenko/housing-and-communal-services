# -*- coding: utf-8 -*- 

import wx
import os

class Preview(wx.Frame):
    def __init__(self, parent):
        
        self.parent = parent
        self.setting = self.parent.setting
        
        wx.Frame.__init__(self, None, -1, u'Предпросмотр' ) # size=(1000, 800)
        self.SetIcon(wx.Icon(self.setting['iconPreview'], wx.BITMAP_TYPE_PNG))
        
        size = wx.ScreenDC().GetSize()
        self.SetSize((size.x, size.y - 35))
        self.panel = wx.Panel(self, -1)
        self.text = wx.TextCtrl(self.panel, -1, size = (size.x - 8, size.y - 45), style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        
        content = ''
        path = '.\\tmp\\temp.txt'
        
        if os.path.isfile(path):
            with open(path) as hf:
                content = hf.read()
            
        self.font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL)
        
        self.text.SetValue(content)
        self.text.SetFont(self.font)
        
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetFieldsCount(1)
        self.statusBar.SetStatusText(u"ESC - выход  |  '-' - уменьшить размер текста  |  '+' - увеличить размер текста  |  F9 - Отправить на печать")
        
        gridsizer = wx.GridSizer()
        gridsizer.Add(self.panel, flag = wx.EXPAND)
        self.SetSizer(gridsizer)
        self.Layout()
        
        self.text.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        
        self.Center()
        self.Show()
        
    def OnClose(self, event):
        
        self.parent.Enable()
        self.Destroy()
        
    def OnResize(self, event):
        
        size = event.GetSize()
        self.text.SetSize((size.x - 20, size.y - 65))
        
    def OnKeyDown(self, event):
        
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        elif event.GetKeyCode() == wx.WXK_F9:
            # F9
            if self.parent.__class__.__name__ == 'PanelSinglePrint':
                self.parent.printing()
                self.Close()
            elif self.parent.__class__.__name__ == 'Editor':
                dlg = wx.MessageDialog(None, u'Печать запрещена при редактировании шаблона', u'Ошибка отправки на печать', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
        elif event.GetKeyCode() == 45:
            # -
            size = self.font.GetPointSize()
            self.font.SetPointSize(size-1)
            self.text.SetFont(self.font)
            
        elif event.GetKeyCode() == 43:
            # +
            size = self.font.GetPointSize()
            self.font.SetPointSize(size+1)
            self.text.SetFont(self.font)
        
        event.Skip()
        