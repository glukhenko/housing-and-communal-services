# -*- coding: utf-8 -*- 

import random

class Encryption():
    def __init__(self, parent):
        self.model = parent
        
    def coding(self, login, psw, status):
        # Шифрует логин, пароль и статус пользователя (юзер или админ) в последовательность из 29 символов
        # [0]      [1-5] [6-27] [28]
        # смещение info  margin  typeUser
        # Выходная строка состоит из 29 символов, в нужных местах информационные биты, в других ж мусор
        # Рандомно выбираем от 0-9, какая цифра будет, на столько позиций сместиться в право каждый бит, также четность определяет
        # в 0 или в 1 будут информациионные биты (см далее). Есть 2 последовательности (логин с паролем и мусор)
        
        types = {u'Ограниченный пользователь' : '00',
                 u'Пользователь'              : '01',
                 u'Администратор'             : '11'
                }
                
        try:
            assert len(login) < 32 and len(psw) < 32 and types.has_key(status)
        except AssertionError:
            self.model.objLoger.error(u'model.Encryption: Ошибка шифрования "' + login + u'", потому что логин и пароль ограничены 32 разрядами, а длина введенного логина: ' + str(len(login)) + u', пароля:' + str(len(psw)))
            return None
        
        data = list( login + psw )
        garbage = self.generateSimbols(64 - len(data))
        parity = random.randint(1,9)
        
        # codeTrue == 1 означает что биты данных находятся в положении 1, а биты мусора в положении 0
        # codeFalse == 1 означает что биты данных находятся в положении 0, а биты мусора в положении 1
        codeTrue = 1 if parity % 2 == 0 else 0
        codeFalse = int(not codeTrue)
        
        codingLine = ''
        code = ''
        # Сигнализируют, есть ли данные в последовательностях
        flagData, flagGarbage = True, True
        
        while 1:
            if not flagData:
                # обработать оставшийся мусор
                codingLine += ''.join(garbage)
                code += str(codeFalse) * len(garbage)
                break
            elif not flagGarbage:
                # обработать оставшиеся данные
                codingLine += ''.join(data)
                code += str(codeTrue) * len(data)
                break
            else:
                mode = random.randint(0,1)
                if mode == codeTrue:
                    try:
                        codingLine += data.pop(0)
                        code += str(mode)
                    except IndexError:
                        flagData = False
                else:
                    try:
                        codingLine += garbage.pop(0)
                        code += str(mode)
                    except IndexError:
                        flagGarbage = False
        
        h = ''
        
        # Парсим строку кода по байтово, переводим в hex
        for i in range(8):
            temp = code[8*i:8*(i+1)]
            h += hex(int('1' + temp,2))[3:]
            
        margin = hex(len(login))[2:]
        if len(margin) == 1:
            margin = '0' + margin
        
        return str(parity) + h + margin + self.shift(codingLine, parity) + types[status]

    
    def generateSimbols(self, count):
        # "()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        # [                                            40-125                                   ][                        1040-1103                               ]
        
        sequence = []
        for i in range(count):
            if random.randint(0,1):
                sequence.append(self.utf8(random.randint(40,125)).decode('utf-8'))
            else:
                sequence.append(self.utf8(random.randint(1040,1103)).decode('utf-8'))
        
        return sequence
        
    
    def decoding(self, string):
        
        # Дешифрует логин, пароль и статус пользователя
        LENGTH = 85
        
        types = {'00' : u'Ограниченный пользователь',
                 '01' : u'Пользователь',
                 '11' : u'Администратор'
                }
        
        try:
            assert len(string) == LENGTH
        except AssertionError:
            self.model.objLoger.warning(u'Проблемы с дешифровкой пользователя "' + string + u'", длина: ' + str(len(string)) + u', обратитесь к разработчикам')
            return None
        
        parity = string[0]
        code = '0x1' + string[1:17]
        code = bin(int(code,16))[3:]
        margin = int(string[17:19],16)
        data = string[19:-2]
        data = self.shift(data, - int(parity))
        status = types[string[-2:]]
        
        codeTrue = 1 if int(parity) % 2 == 0 else 0
        
        position = [index for index, value in enumerate(code) if int(value) == codeTrue]
        login = ''.join([data[pos] for pos in position[:margin]])
        psw   = ''.join([data[pos] for pos in position[margin:]])
        return login, psw, status
        
    def shift(self, string, parity):
        
        result = ''
        for char in string:
            num = ord(char)
            num = num + parity
            if num > 0xFFFF:
                num = (num + ( 32 - 1 ) ) % 0xFFFF
            if num < 32:
                num = 0xFFFF + num - ( 32 - 1 )
            result += self.utf8(num)
        
        return result.decode('utf-8')
        
    
    def utf8(self, i):
        
        if i < 0x80:
            return chr(i)
        if i < 0x800:
            return chr(0xC0 | (i>>6) & 0x1F)+\
                chr(0x80 | i & 0x3F)
        if i < 0x10000L:
            return chr(0xE0 | (i>>12) & 0xF)+\
                chr(0x80 | (i>>6) & 0x3F)+\
                chr(0x80 | i & 0x3F)
        if i < 0x200000L:
            return chr(0xF0 | (i>>18) & 0x7)+\
                chr(0x80 | (i>>12) & 0x3F)+\
                chr(0x80 | (i>>6) & 0x3F)+\
                chr(0x80 | i & 0x3F)
        if i < 0x4000000L:
            return chr(0xF8 | (i>>24) & 0x3)+\
                chr(0x80 | (i>>18) & 0x3F)+\
                chr(0x80 | (i>>12) & 0x3F)+\
                chr(0x80 | (i>>6) & 0x3F)+\
                chr(0x80 | i & 0x3F)
        return chr(0xFC | (i>>30) & 0x1)+\
            chr(0x80 | (i>>24) & 0x3F)+\
            chr(0x80 | (i>>18) & 0x3F)+\
            chr(0x80 | (i>>12) & 0x3F)+\
            chr(0x80 | (i>>6) & 0x3F)+\
            chr(0x80 | i & 0x3F)
    