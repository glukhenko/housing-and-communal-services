# -*- coding: utf-8 -*- 

import wx
import wx.animate

class LoaderImage(wx.Frame):
    def __init__(self, img = ''):
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, title='LoaderImage', style = style)
        self.SetTransparent( 220 )
        self.ag = wx.animate.GIFAnimationCtrl(self, -1, img, pos=(0, 0))
        self.SetSize(self.ag.GetSize())
        self.ag.GetPlayer().UseBackgroundColour(True)     
        self.Center()
    
    def close(self):
        self.Close() 