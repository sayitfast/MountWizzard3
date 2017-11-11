############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################
import logging
import re
import ipaddress
from baseclasses import widget


class CheckIP(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self):
        pass

    def checkPort(self, uiPort):
        cursorPosition = uiPort.cursorPosition()
        if uiPort.text().strip() != '':
            port = int(uiPort.text())
        else:
            port = 0
        if 1 < port < 64535:
            valid = True
            uiPort.setStyleSheet(self.TEXT_COLOR_BLUE)
        else:
            valid = False
            uiPort.setStyleSheet(self.TEXT_COLOR_RED)
        uiPort.setText('{0}'.format(port))
        uiPort.setCursorPosition(cursorPosition)
        return valid, port

    def checkIP(self, uiIp):
        cursorPosition = uiIp.cursorPosition()
        IP = uiIp.text().strip()
        try:
            ipaddress.ip_address(IP)
            valid = True
            uiIp.setStyleSheet(self.TEXT_COLOR_BLUE)
        except Exception as e:
            valid = False
            uiIp.setStyleSheet(self.TEXT_COLOR_RED)
        finally:
            pass
        uiIp.setText('{0}'.format(IP))
        uiIp.setCursorPosition(cursorPosition)
        return valid, IP

    def checkMAC(self, uiMac):
        mac = uiMac.text()
        mac = re.sub('[.:-]', '', mac).lower()
        mac = ''.join(mac.split())
        if len(mac) != 12 or not mac.isalnum():
            valid = False
            uiMac.setStyleSheet(self.TEXT_COLOR_RED)
        else:
            valid = True
            uiMac.setStyleSheet(self.TEXT_COLOR_BLUE)
            mac = ":".join(["%s" % (mac[i:i + 2]) for i in range(0, 12, 2)])
        return valid, mac
