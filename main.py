# -*- coding: utf-8 -*- 

import wx
import model.model as model

# Импортирование GUI окон
from view.AutorizationFrame import AutorizationFrame
from view.MainWindow import MainWindow

class Main():
    def __init__(self):
        
        self.user = None
        self.status = None
        
        # Инициализация модели
        self.objModel = model.Model('.\\MatrixPrinter.log', '.\\config.ini')
        
        self.app = wx.PySimpleApp(0)
        
        # Авторизация пользователя
        self.autorization()
        
    def autorization(self):
        
        self.objModel.objLoger.info(u'Происходит авторизация пользователя...')
        AutorizationFrame(self).Show()
        self.app.MainLoop()
        
        # По закрытии окна, если авторизация прошла успешно то в свойстве self.user появиться авторизируемый пользователь.
        if self.user is not None:
            self.objModel.objLoger.start(self.user)
            self.work()
        else:
            self.objModel.objLoger.critical(u'Авторизация прервана. Программа завершает свою работу.')
            exit(1)
            
    def work(self):
        MainWindow(self).Show()
        self.app.MainLoop()
        
if __name__ == "__main__":
    Main()
    