"""
# @Author   : DaoQ You

# @File     : selenium_helpers.py

# @Project  : webauto

# @Software : PyCharm Community Edition
"""
# !/usr/bin/python
# -*- coding:utf-8 -*-

import time
import os
import io
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from web_log import log

BROWSERDRIVER = None
WAITTIMEOUT = 120

class WebElement(object):
    """
    Defined Web element
    """
    PATH = ""
    DISPLAYNAME = ""
    
    def __init__(self, displayname, path):
        global PATH
        global DISPLAYNAME
        self.PATH = path
        self.DISPLAYNAME = displayname
        
    def inside(self, container):
        """
        web element inside web element
        
        :param container:
        
        :return:
        """
        return WebElement(self.DISPLAYNAME + " inside " +
                          container.DISPLAYNAME, container.PATH + self.PATH)


class TerminalManager(object):
    """
    Terinal Manager
    """
    olderhandle = ''
    m_terminallist = []
    #global BROWSERDRIVER
    def __init__(self):
        #global BROWSERDRIVER
        BROWSERDRIVER = webdriver

    def getterminal(self, title, timeout):
        """
        Get terminal

        :param title:

        :param timeout:

        :return:
        """
        print(type(BROWSERDRIVER))
        print(BROWSERDRIVER.current_window_handle)
        if(len(self.m_terminallist) == 0):
            self.m_terminallist.append(BROWSERDRIVER.current_window_handle)
        oldhandle = BROWSERDRIVER.current_window_handle
        result = BROWSERDRIVER.window_handles
        if(result != None and len(result) > 0):
            log().log("Avaliable new handles: {0}".format(len(result)))
            log().log("Avaliable new handles: {0}".format(str(result)))
            self.olderhandle = result[0]
            for item in result:
                BROWSERDRIVER.switch_to_window(item)
                waitduration = timeout
                while((BROWSERDRIVER.title in dir()) and waitduration > 0):
                    time.sleep(1)
                    waitduration = waitduration - 1
                if(BROWSERDRIVER.title.lower() == title.lower()):
                    ssh = SshTerminal(item, self)
                    self.m_terminallist.append(item)
                    return ssh
            log().log("Could not find window with title {0}".format(title))
            BROWSERDRIVER.switch_to_window(oldhandle)
            log().log("Old handle {0}".format(oldhandle))
        return None

    def closeterminal(self, handle):
        """
        Close terminal

        :param handle:

        :return:
        """
        log().log("Closing terminal handle: {0}".format(handle))
        self.m_terminallist.remove(handle)
        log().log("Closed terminal handle: {0}".format(handle))
        #log().log("terminallists: {0}".format(str(self.m_terminallist[-1])))
        #BROWSERDRIVER.switch_to_window(self.m_terminallist[-1])
        log().log("terminallists: {0}".format(str(self.olderhandle)))
        BROWSERDRIVER.switch_to_window(self.olderhandle)

class SshTerminal(object):
    """
    SSH Terminal
    """
    global WAITTIMEOUT
    m_handle = ""
    m_height = 0
    m_width = 0
    m_terminalmanager = None
    MAX_LINES = 5
    def __init__(self, handle, tm):
        WAITTIMEOUT = 10
        self.m_handle = handle
        self.m_terminalmanager = tm
        self.__attachssh()

    def close_sshterminal(self):
        """
        Close ssh termianl

        :return:
        """
        BROWSERDRIVER.switch_to_window(self.m_handle)
        BROWSERDRIVER.close()
        self.m_terminalmanager.closeterminal(self.m_handle)

    def run(self, cmd):
        """
        Run command

        :param cmd:

        :return:
        """
        cmd = cmd.strip()
        waitduration = WAITTIMEOUT
        #Get all lines
        alllinescmd = str.format("return openSsh.term.lines")
        resultbeforetmp = BROWSERDRIVER.execute_script(alllinescmd)
        #Find current prompt position
        cmdstrpos = str.format("return openSsh.term.lines.length - openSsh.term.rows + openSsh.term.y;")
        promptbeforetmp = BROWSERDRIVER.execute_script(cmdstrpos)
        promptbefore = int(promptbeforetmp)
        print("prompt befor line: {0}".format(promptbefore))
        #print ("result befor line: {0}".format(resultbeforetmp))
        startposmaker = self.__create_postion_maker(promptbefore, cmd, resultbeforetmp)
        print("startposmaker: {0}".format(startposmaker))
        print("startposmaker length: {0}".format(len(startposmaker.split('\n'))-1))
        startposmakerlen = len(startposmaker.split('\n'))-1
        self.__print_all()
        log().log("Command to be executed: {0}".format(cmd))
        jscommand = str.format("return openSsh.term.send('{0}\\n');".format(cmd))
        BROWSERDRIVER.execute_script(jscommand)
        time.sleep(1)
        #Wait the operation to complete
        lastcnt = len(resultbeforetmp)
        resulttmp = len(resultbeforetmp)
        while(lastcnt != resulttmp and waitduration > 0):
            lastcnt = resulttmp
            time.sleep(1)
            waitduration = waitduration - 1
            resultctmp = BROWSERDRIVER.execute_script("return openSsh.term.lines.length;")
            resulttmp = int(resultctmp)
            log().log("Waiting: lastcnt {0}, newcount {1}, waitduration {2} ".format(lastcnt, resulttmp, waitduration))
        #Get attribute all output
        resultaftertmp = BROWSERDRIVER.execute_script(alllinescmd)
        #Find current prompt position
        promptaftertmp = BROWSERDRIVER.execute_script(cmdstrpos)
        promptafter = int(promptaftertmp)
        log().log("Prompt before {0}, after {1}".format(promptbefore, promptafter))
        self.__print_all()
        print("resultbeforetmp {0}".format(len(resultbeforetmp)))
        print("resultaftertmp {0}".format(len(resultaftertmp)))
        #if(len(resultbeforetmp) > len(resultaftertmp)):
        if(promptafter > promptbefore):
            pos = self.__get_last_prompt_position(startposmaker, resultaftertmp)
            if(promptbefore != pos):
                log().log("Scrolled. old startpos {0}, new startpos {1}".format(promptbefore, pos))
                promptbefore = pos
        #Copy the output
        currentpos = -1
        screenstringlist = []
        resultaftertmp = BROWSERDRIVER.execute_script(alllinescmd)
        print("resultaftertmp {0}".format(resultaftertmp))
        for item in resultaftertmp:
            currentpos += 1
            if(currentpos <= promptbefore or currentpos >= promptafter):
                continue
            if(item != None):
                screenstringlist.append(self.__convert_sshline_tostring(item).rstrip())
        print("screenstringlist length {0}".format(len(screenstringlist)))
        screenstringlistlen = len(screenstringlist)
        cmdresult = ''
        if(screenstringlistlen > startposmakerlen):
            for j in range(screenstringlistlen - startposmakerlen):
                cmdresult += ''.join(screenstringlist[startposmakerlen + j] + '\n')
        print("screenstringlist {0}".format(screenstringlist))
        #return str.join("\n",screenstringlist)
        return cmdresult

    @staticmethod
    def __attachssh():
        waittime = WAITTIMEOUT
        ypos1 = -1
        last_Ypos = ypos1
        while(ypos1 <= 0):
            try:
                if(waittime <= 0):
                    break
                last_Ypos = ypos1
                log().log("Waiting for the terminal to be ready")
                time.sleep(3 if(waittime >= 3)else waittime * 1)
                ypos1str = BROWSERDRIVER.execute_script("return openSsh.term.y")
                ypos1 = int(ypos1str)
                #logger.debug("Pos: %s"%ypos1str)

                log().log("Pos: %s"%ypos1str)
                waittime -= 3
            except Exception as e:
                log().log(str(e))

    def __create_postion_maker(self, pos, command, lines):
        #cnt = 0 if pos < self.MAX_LINES else pos - self.MAX_LINES
        cnt = 0
        stringbuffer = []
        #stringbuffer = io.BytesIO()
        for i in range(cnt, pos):
            #stringbuffer.write(self.__convert_sshline_tostring(lines[i]).strip())
            stringbuffer.append(self.__convert_sshline_tostring(lines[i]).strip())
        #stringbuffer.append(self.__convert_sshline_tostring(lines[pos]).strip() + " " + command)
        log().log("ssh string: {0}".format(str(stringbuffer).strip()))
        result = ''
        for j in range(len(stringbuffer)):
            strl = list(stringbuffer[j])
            strc = ''.join(strl)
            strs = strc.split(' ')
            oresult = ''
            #print "strs length {0}".format(len(strs))
            for k in range(len(strs)):
                if(k == 0):
                    oresult = '' + strs[k]
                elif(k != 0 and (strs[k].strip() != '')):
                    oresult += ' ' + strs[k]
            result += oresult + "\n"
            log().log("ssh string oresult: {0}".format(oresult))
        log().log("ssh string result: {0}".format(result))
        #return str(stringbuffer).strip()
        return result

    @staticmethod
    def __convert_sshline_tostring(line):
        line_str_bytes = io.BytesIO()
        for ln in line:
            line_str_bytes.write(str(ln[1]))
        return line_str_bytes.getvalue()

    @staticmethod
    def __print_all():
        cmdstrpos = "return openSsh.term.lines.length;"
        promptbeforetmp = BROWSERDRIVER.execute_script(cmdstrpos)
        log().log("lines.length: {0}".format(promptbeforetmp))

        cmdstrpos = "return openSsh.term.y;"
        promptbeforetmp1 = BROWSERDRIVER.execute_script(cmdstrpos)
        log().log("Y: {0}".format(promptbeforetmp1))

        cmdstrpos = "return openSsh.term.rows;"
        promptbeforetmp2 = BROWSERDRIVER.execute_script(cmdstrpos)
        log().log("rows: {0}".format(promptbeforetmp2))

        cmdstrpos = "return openSsh.term.ybase;"
        promptbeforetmp3 = BROWSERDRIVER.execute_script(cmdstrpos)
        log().log("ybase: {0}".format(promptbeforetmp3))

    def __get_last_prompt_position(self, maker, lines):
        position = 0
        for i in range(len(lines)-1, -1, -1):
            strmaker = io.BytesIO()
            j = 0
            for j in range(self.MAX_LINES +1):
                if((j+i) < len(lines)):
                    strmaker.write(self.__convert_sshline_tostring(lines[i + j]).strip())
                    strval = str(strmaker)
                    if((strval.strip()) != ""):
                        if(strval == maker):
                            log().log("Finding ssh string: {0}".format(strval))
                            position = i + j
                            log().log("New position: {0}".format(position))
                            return position
        return position


class BrowserClient(object):
    """
    Basic functions defined here
    Including: initiate browser, get_profile,
    """
    global WAITTIMEOUT
    WAITTIMEOUT = 10
    def __init__(self):
        pass

    def local_client(self, browser_type, use_cache):
        """
        Start browser on local machine

        :param browserType: String, values: firefox, chrome, ie, edge

        :param useCache: Boolean, values: True, False

        :return:
        """
        global BROWSERDRIVER
        profile = self.get_profile(browser_type)
        if(browser_type.lower() == 'firefox'):
            if(use_cache):
                firefox_profile = webdriver.FirefoxProfile(profile)
                BROWSERDRIVER = webdriver.Firefox(firefox_profile)
            else:
                BROWSERDRIVER = webdriver.Firefox()
        elif(browser_type.lower() == 'chrome'):
            if(use_cache):
                chromeoptions = webdriver.ChromeOptions()
                cmd = "user-data-dir=" + profile
                chromeoptions.add_argument(cmd)
                BROWSERDRIVER = webdriver.Chrome(chrome_options=chromeoptions)
            else:
                BROWSERDRIVER = webdriver.Chrome()
        elif(browser_type.lower() == 'ie'):
            BROWSERDRIVER = webdriver.Ie()
        elif(browser_type.lower() == 'edge'):
            BROWSERDRIVER = webdriver.Edge()
        BROWSERDRIVER.maximize_window()
        log().selenium_log_to_file(level="DEBUG")

    @staticmethod
    def remote_client(hub_server, browser_type):
        """
        Start browser on the remote machine

        :param hubServer: String, the ip of the remote machine which run the hub server

        :param browserType: String, values: firefox, chrome, ie, edge

        :return:
        """
        global  BROWSERDRIVER
        BROWSERDRIVER = webdriver.Remote(
            command_executor='http://' + hub_server + ':4444/wd/hub',
            desired_capabilities={'browserName': browser_type, 'javascriptEnabled': True},
            keep_alive=True)
        log().selenium_log_to_file(level="DEBUG")

    @staticmethod
    def get_profile(browser_type):
        """
        Get the browser profile

        :param browserType: String, values: firefox, chrome, ie, edge

        :return:
        """
        profile = ""
        appdata_path = os.environ["AppData"]
        if(browser_type.lower() == 'firefox'):
            filepath = appdata_path + "\\Mozilla\\Firefox\\Profiles"
            profile = filepath + "\\" + os.listdir(filepath)[0]
        elif(browser_type.lower() == 'chrome'):
            str_split = appdata_path.split("\\")
            end = str_split[len(str_split)-1]
            profile = appdata_path[0:len(appdata_path) - len(end)] + "Local\\Google\\Chrome\\User Data"
        return profile

    @staticmethod
    def open_url(url):
        """
        Open url

        :param url: String, the url to be be opened

        :return:
        """
        BROWSERDRIVER.get(url)

    @staticmethod
    def get_title():
        """
        Get the browser title

        :return: String
        """
        return BROWSERDRIVER.title

    def get_value(self, element):
        """
        Get the attribute value

        :param element: WebElement

        :return: String
        """
        ele = self.waitfor_element(element, 10)
        return ele.get_attribute('value')

    def get_attribute(self, element, attribute):
        """
        Get value of the attribute

        :param element:

        :param attribute:

        :return:
        """
        ele = self.waitfor_element(element, 10)
        return ele.get_attribute(attribute)


    def get_elememt_attribute(self, element, attribute):
        """
        Get the element attribute

        :param element: WebElement

        :param attribute: String, such as: value, class,

        :return: String
        """
        ele = self.waitfor_element(element, 10)
        return ele.get_attribute(attribute)

    def get_text(self, element):
        """
        Get the text of the element

        :param element: WebElement

        :return: String
        """
        ele = self.waitfor_element(element, 10)
        return ele.text

    @staticmethod
    def get_url():
        """
        Get the webdriver url

        :return: String
        """
        return BROWSERDRIVER.current_url

    @staticmethod
    def refresh():
        """
        Refresh the page

        :return:
        """
        BROWSERDRIVER.refresh()

    @staticmethod
    def get_cookies():
        """
        Get the browser cookies

        :return: cookies
        """
        return BROWSERDRIVER.get_cookies()

    @staticmethod
    def get_cookie(name):
        """
        Get the specified browser cookie

        :param name: cookie name

        :return: cookie
        """
        return BROWSERDRIVER.get_cookie(name)

    @staticmethod
    def close_currentwindow():
        """
        Close current page

        :return:
        """
        BROWSERDRIVER.close()

    @staticmethod
    def quit():
        """
        Close the browser

        :return:
        """
        BROWSERDRIVER.quit()

    @staticmethod
    def save_screenshot(filename):
        """
        Get the browser screenshot and save to a file

        :param filename: String

        :return:
        """
        BROWSERDRIVER.get_screenshot_as_file(filename)

    @staticmethod
    def waitfor_element_by_name(name):
        """
        Wait for element by name

        :param name: Element name value

        :return: WebElement
        """
        print(WAITTIMEOUT)
        ELEMENT = WebDriverWait(BROWSERDRIVER, WAITTIMEOUT, 1).until(lambda x: x.find_element_by_name(name), NoSuchElementException)
        return ELEMENT

    @staticmethod
    def waitfor_element_by_xpath(path, timeout):
        """
        Wait for element by xpath

        :param path: element xpath

        :param timeout: int(second)

        :return: WebElement
        """
        redo = 1
        log().log("Searching {0}".format(path))
        while(redo < timeout):
            ELEMENT = WebDriverWait(BROWSERDRIVER, WAITTIMEOUT, 1).until(lambda x: x.find_element_by_xpath(path), NoSuchElementException)
            if(ELEMENT.is_enabled() and ELEMENT.is_displayed()):
                log().log("Found {0}".format(path))
                #redo = False
                return ELEMENT
            else:
                log().log("Found but not visible. [Displayed = {0}, Enabled = {1}]".format(ELEMENT.is_displayed(), ELEMENT.is_enabled()))
                #redo = True
                time.sleep(1)

    @staticmethod
    def find_elements_by_xpath(path):
        """
        Find elements by xpath

        :param path:

        :return:
        """
        log().log("Searching {0}".format(path))
        try:
            elements = WebDriverWait(BROWSERDRIVER, WAITTIMEOUT, 1).until(lambda x: x.find_elements_by_xpath(path), NoSuchElementException)
            return elements
        except TimeoutException:
            log().log("Timeout waiting for {0}".format(path))
        except StaleElementReferenceException:
            elements = WebDriverWait(BROWSERDRIVER, WAITTIMEOUT, 1).until(lambda x: x.find_elements_by_xpath(path), NoSuchElementException)
            return elements

    def waitfor_element(self, element, timeout):
        """
        Wait for element

        :param element:

        :return:
        """
        ELEMENT = self.waitfor_element_by_xpath(element.PATH, timeout)
        return ELEMENT

    def waitfor_element_disappear(self, element):
        """
        Wait for element

        :param element:

        :return:
        """
        count = 1
        try:
            while count != 0:
                time.sleep(1)
                elements = BROWSERDRIVER.find_elements_by_xpath(element.PATH)
                count = len(elements)
                log().log("Elements: {0}".format(count))
                for ele in elements:
                    if ele.is_displayed():
                        count = 1
                    else:
                        count = 0
        except Exception as e:
            log().log("Exception: {0}".format(str(e)))

    @staticmethod
    def is_element_displayed(element):
        """
        Check the element is displayed

        :param element:

        :return:
        """
        try:
            ELEMENT = WebDriverWait(BROWSERDRIVER, WAITTIMEOUT, 1).until(lambda x: x.find_element_by_xpath(element.PATH), NoSuchElementException)
            return ELEMENT.is_displayed()
        except TimeoutException:
            log().log("Timeout waiting for {0} displayed".format(element.DISPLAYNAME))

    def is_element_enabled(self, element):
        """
        Check the element is enabled

        :param element:

        :return:
        """
        ele = self.waitfor_element(element, 10)
        return ele.is_displayed()

    def is_element_exist(self, element):
        """
        Check the element is exist

        :param element:

        :return:
        """
        is_exist = False
        try:
            ele = self.waitfor_element(element, 10)
            if(ele != None):
                is_exist = True
        except TimeoutException:
            log().log("Timeout waiting for {0}".format(element.DISPLAYNAME))
        return is_exist

    @staticmethod
    def waitfor_timeout(timeout):
        """
        Wait for timeout

        :param timeout: int(seconds)

        :return:
        """
        time.sleep(timeout)

    def fill(self, element, text):
        """
        Input text to the element

        :param element: WebElment

        :param text: String

        :return:
        """
        redo = True
        while(redo):
            ele = self.waitfor_element(element, 10)
            ele.clear()
            ele.send_keys(text)
            value = self.get_value(element)
            if(value != text):
                log().log("Value of {0} is incorrectly set to {1}. Try again to set the value to {2}".format(element.DISPLAYNAME, value, text))
                ele.clear()
                redo = True
            else:
                redo = False
        log().log("Enter [{0}] into {1}".format(text, element.DISPLAYNAME))

    def click(self, element):
        """
        Click element

        :param element: WebElement

        :return:
        """
        try:
            ele = self.waitfor_element(element, 10)
            ele.click()
            log().log("Clicked {0} ".format(element.DISPLAYNAME))
        except NoSuchElementException:
            log().log("The element {0} with xpath {1} dose not exists.".format(element.DISPLAYNAME, element.PATH))

    def click_elements(self, element):
        """
        Click elements

        :param element: WebElement

        :return:
        """
        elements = self.find_elements_by_xpath(element.PATH)
        #print len(elements)
        for element in elements:
            if(element.is_enabled() and element.is_displayed()):
                log().log("Found element {0} ".format(element.text))
                element.click()
                log().log("Clicked {0} ".format(element.text))

    def send_combination_keys(self, element, majkey, secondarykey):
        """
        Send short key to the element

        :param element:

        :param majkey:

        :param secondarykey:

        :return:
        """
        try:
            ele = self.waitfor_element(element, 10)
            mainkey = majkey.lower()
            keymap = {"ctr": lambda: Keys.CONTROL, "shift": lambda: Keys.SHIFT, "alt": lambda: Keys.ALT,
                      "enter": lambda: Keys.ENTER, "up": lambda: Keys.UP, "down": lambda: Keys.DOWN}
            ele.send_keys(keymap[mainkey](), secondarykey)
        except NoSuchElementException:
            log().log("The element {0} with xpath {1} dose not exists.".format(element.DISPLAYNAME, element.PATH))

    @staticmethod
    def switch_window_by_title(title):
        """
        Switch the browser page by title

        :param title:

        :return:
        """
        BROWSERDRIVER.switch_to_window(title)

    @staticmethod
    def switch_window_by_handle(handle):
        """
        Switch the browser page by handle

        :return:
        """
        log().log("Clicked {0} ".format(handle))
        BROWSERDRIVER.switch_to_window(handle)

    @staticmethod
    def waitfor_title(title, timeout):
        """
        Wait for the page title

        :param title:

        :param timeout:

        :return:
        """
        try:
            WebDriverWait(BROWSERDRIVER, timeout).until(EC.title_contains(title))
        except TimeoutException:
            log().log("Timeout waiting for title {0}".format(title))

    @staticmethod
    def forward():
        """
        Forward the page

        :return:
        """
        BROWSERDRIVER.forward()

    @staticmethod
    def back():
        """
        Back the page

        :return:
        """
        BROWSERDRIVER.back()

    @staticmethod
    def execute_script(script):
        """
        Execute the script on the browser

        :param script:

        :return:
        """
        try:
            result = BROWSERDRIVER.execute_script(script)
            return result
        except Exception as e:
            log().log(str(e))

    @staticmethod
    def get_latest_window_handle():
        """
        Get the latest page window handle

        :return:
        """
        handler = ""
        try:
            count = len(BROWSERDRIVER.window_handles)
            print(count)
            log().log("Current window count is {0}".format(count))
            log().log("Current window title is {0}".format(BROWSERDRIVER.title))
            log().log("Current window handler is {0}".format(BROWSERDRIVER.current_window_handle))
            handler = BROWSERDRIVER.window_handles[count - 1]
            return handler
        except Exception as e:
            str(e)

    @staticmethod
    def get_main_window_handle():
        """
        Get the main page window handle

        :return:
        """
        handler = ""
        try:
            handler = BROWSERDRIVER.current_window_handle
            return handler
        except Exception as e:
            str(e)
