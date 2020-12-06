# -*- coding: utf-8 -*- 

import os
import logging
import time

class Logger():
    
    def __init__(self, parent, file, session):
        
        # Сессия используется для указания пользователя и времени когда он начал работать. В качестве сессии берется время захода в программу
        self.parent = parent
        
        if not os.path.isfile(file):
            print 'error, dont exist log file'
            exit(1)
            
        
        logging.basicConfig(filename = file,
                            level = logging.DEBUG,
                            format = '%(asctime)-25s SID:%(session)-10s USER:%(user)-10s %(levelname)-12s %(message)s'
                            )
        self.data = {'session' : session[4:-3], 'user' : 'unknow'}
        
    def start(self, user):
        
        self.data['user'] = user
        logging.info(u'>>> Пользователь "' + self.data['user'] + u'" начинает сеанс работы с номером ' + self.data['session'], extra = self.data)
        
    def info(self, msg):
        
        logging.info(msg, extra = self.data)
        
    def warning(self, msg):
        
        logging.warning(msg, extra = self.data)
        
    def error(self, msg):
        
        logging.error(msg, extra = self.data)
        
    def critical(self, msg):
        
        logging.critical(msg, extra = self.data)
        
    def finish(self):
        
        logging.info(u'<<< Пользователь "' + self.data['user'] + u'" завершает сеанс работы с номером ' + self.data['session'], extra = self.data)
        self.data['user'] = u'бот'
    