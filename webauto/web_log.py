"""
# @Author   : DaoQ You

# @File     : web_log.py

# @Project  : webauto

# @Software : PyCharm Community Edition
"""
# !/usr/bin/python
# -*- coding:utf-8 -*-
import time
import traceback
import sys
import logging


class log(object):
    """
    Basic log
    """
    def __init__(self):
        pass

    def log(self, msg, filename="log.log"):
        """
        :param msg: String, the message to be wrote to the log

        :param filename: String, the log file name

        :return: N/A
        """
        try:
            msgstring = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + " " + msg
            print(msgstring)
            fso = open(filename, 'a')
            fso.write(msgstring)
            fso.write("\n")
            fso.close()
        except:
            self.capture_exception(filename)

    @staticmethod
    def capture_exception(filename="log.log"):
        """
        Capture the exception and log it in the log file

        :param filename: String, log file name

        :return:
        """
        with open(filename, 'a') as f:
        #print >> logs, time.strftime('%Y-%m-%d %X', time.localtime())
            print(time.strftime('%Y-%m-%d %X', time.localtime()), f)
            err = ''.join(traceback.format_exception(*sys.exc_info()))
            print(err, f)
        print("\n", f)
        #print >> logs, err
        #logs.write("\n")
        #logs.close()

    @staticmethod
    def selenium_log_to_file(level, filename="tracelog.log"):
        """
        Store the selemium log to the file

        :param level: String, level="DEBUG", "INFO", "WARNING", "ERROR",

        :param filename: String,

        :return:
        """
        logger = logging.getLogger("selenium")
        if (len(logger.handlers) > 0):
            return
        logger.setLevel(level)
        file_open = open(filename, 'a')
        log_handler = logging.StreamHandler(file_open)
        log_handler.setFormatter(logging.Formatter('[%(asctime)s.%(msecs)03d|%(levelname)-.3s] %(name)s: %(message)s', '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(log_handler)
