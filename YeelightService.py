#! /usr/bin/env python
# coding:UTF8
#author :zhaohui mail:zhaohui-sol@foxmail.com\

from bluepy.btle import Peripheral,DefaultDelegate
import logging,time

logging.basicConfig(level=logging.DEBUG)

class YeelightService:
    """
    YeelightService is the yeelight control util for python

    author zhaohui.sol
    """

    SERVICE = "0000FFF0-0000-1000-8000-00805F9B34FB"

    CHAR_CONTROL = "0000FFF1-0000-1000-8000-00805F9B34FB"

    CHAR_DELAY = "0000FFF2-0000-1000-8000-00805F9B34FB"

    CHAR_DELAY_QUERY = "0000FFF3-0000-1000-8000-00805F9B34FB"

    CHAR_DELAY_NOTIFY = "0000FFF4-0000-1000-8000-00805F9B34FB"

    CHAR_QUERY = "0000FFF5-0000-1000-8000-00805F9B34FB"

    CHAR_NOTIFY = "0000FFF6-0000-1000-8000-00805F9B34FB"

    CHAR_COLOR_FLOW = "0000FFF7-0000-1000-8000-00805F9B34FB"

    CHAR_NAME = "0000FFF8-0000-1000-8000-00805F9B34FB"

    CHAR_NAME_NOTIFY = "0000FFF9-0000-1000-8000-00805F9B34FB"

    CHAR_COLOR_EFFECT = "0000FFFC-0000-1000-8000-00805F9B34FB"

    class NotifyDelegate(DefaultDelegate):

        def __init__(self):
            DefaultDelegate.__init__(self)
            self.queue = list()

        def register(self,callback):
            self.queue.append(callback)

        def deregister(self,callback):
            self.queue.remove(callback)

        def handleNotification(self,handle,data):
            logging.warning("notify data %s from %s." % (data,handle))
            res = dict()
            res['data'] = data
            res['handle'] = handle
            for c in self.queue:
                c(res)


    def __init__(self,address):
        """
        address is the yeelight blue ble hardware address
        """
        self.data = dict()
        self.address = address
        self.delegate = YeelightService.NotifyDelegate()
        self.peripher = Peripheral(deviceAddr = address)
        self.service = self.peripher.getServiceByUUID(YeelightService.SERVICE)
        self.peripher.withDelegate(self.delegate)

    def __character_by_uuid__(self,uuid):
        '''
        get character by a special uuid
        '''
        characters = self.service.getCharacteristics(forUUID=uuid)
        return characters[0] if characters else None

    def __write_character__(self,uuid,strdata):
        '''
        write data to a special uuid
        '''
        logging.info(u"write %s to %s." % (strdata,uuid))
        character = self.__character_by_uuid__(uuid)
        if character:
            character.write(strdata)
        else:
            pass

    def __read_character__(self,uuid):
        '''
        read data from a special uuid,may be it's wrong
        '''
        logging.info(u"read data from %s." % uuid)
        character = self.__character_by_uuid__(uuid)
        if character:
            return character.read()
        else:
            return None

    def __notify_character__(self,_to,_write):
        '''
        write data to the uuid and wait data notify
        '''
        res = dict()
        def callback(data):
            for k in data:
                res[k] = data[k]
        self.delegate.register(callback)
        self.__write_character__(_to,_write)
        if self.peripher.waitForNotifications(5):
            logging.info("notify incoming.")
            self.delegate.deregister(callback)
            return res
        else:
            logging.warning("notify timeout.")
            self.delegate.deregister(callback)
            return None

    def __format_request__(self,strdata,length = 18):
        '''
        format the data to a special length
        '''
        if strdata and length >= len(strdata) > 0:
            l = len(strdata)
            strdata += "".join(["," for i in range(length - l)])
            return strdata
        else:
            return "".join(["," for i in range(length)])

    def turn_on(self, brightness = 100):
        '''
        turn on the light with white and full brightness
        '''
        self.control(255,255,255,brightness)

    def turn_off(self):
        '''
        turn off the light
        '''
        self.control(0,0,0,0)

    def control(self,r,g,b,a):
        '''
        turn on the light with special color
        '''
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255
        assert 0 <= a <= 100
        self.__write_character__(YeelightService.CHAR_CONTROL,self.__format_request__("%d,%d,%d,%d"%(r,g,b,a),18))

    def delay_on(self,mins = 5):
        '''
        turn on the light with a min param delay
        '''
        assert 0 < mins < 24 * 60
        self.__write_character__(YeelightService.CHAR_DELAY,self.__format_request__("%d,1" % mins,8))

    def delay_off(self,mins = 5):
        '''
        turn off the light with a min param delay
        '''
        assert 0 < mins < 24 * 60
        self.__write_character__(YeelightService.CHAR_DELAY,self.__format_request__("%d,0" % mins,8))

    def delay_status(self):
        '''
        query the delay status , this method return a raw dict with two key 'handle' and 'data'
        see http://www.yeelight.com/download/yeelight_blue_message_interface_v1.0.pdf
        '''
        return self.__notify_character__(YeelightService.CHAR_DELAY_QUERY,self.__format_request__("RT",2))

    def control_status(self):
        '''
        query the light status , this method return a raw dict with two key 'handle' and 'data'
        see http://www.yeelight.com/download/yeelight_blue_message_interface_v1.0.pdf
        '''
        return self.__notify_character__(YeelightService.CHAR_QUERY,self.__format_request__("S",1))

    def start_color_flow(self,flows):
        '''
        start color flow with a list of params, each param should contain 5 element which is r,g,b,brightness,delay
        see http://www.yeelight.com/download/yeelight_blue_message_interface_v1.0.pdf
        '''
        assert len(flows) <= 9
        for i,e in enumerate(flows):
            assert len(e) == 5
            assert 0 <= e[0] <= 255
            assert 0 <= e[1] <= 255
            assert 0 <= e[2] <= 255
            assert 0 <= e[3] <= 100
            assert 0 <= e[4] <= 10
            self.__write_character__(YeelightService.CHAR_COLOR_FLOW,self.__format_request__("%d,%d,%d,%d,%d,%d" % (i,e[0],e[1],e[2],e[3],e[4]),20))
        self.__write_character__(YeelightService.CHAR_COLOR_FLOW,self.__format_request__("CB",20))

    def stop_color_flow(self):
        '''
        stop color flow
        '''
        self.__write_character__(YeelightService.CHAR_COLOR_FLOW,self.__format_request__("CE",20))

    def effect_smooth(self):
        '''
        make the color change smooth
        '''
        self.__write_character__(YeelightService.CHAR_COLOR_EFFECT,self.__format_request__("TS",2))

    def effect_immediate(self):
        '''
        make the color changes immediate
        '''
        self.__write_character__(YeelightService.CHAR_COLOR_EFFECT,self.__format_request__("TE",2))

    def effect_current_color(self):
        '''
        use the current color as a default startup color
        '''
        self.__write_character__(YeelightService.CHAR_COLOR_EFFECT,self.__format_request__("DF",2))














if __name__ == "__main__":
    x = YeelightService("78:A5:04:77:D0:43")
    x.turn_on()
    #time.sleep(5)
    #x.control(100,25,25,30)
    #time.sleep(5)
    #x.control(25,100,25,50)
    #time.sleep(5)
    #x.control(25,25,100,70)
    #time.sleep(5)
    #x.turn_off()
    x.start_color_flow([(250,0,0,50,3),(0,250,0,50,3),(0,0,250,50,3)])
    print x.delay_status()
    print x.control_status()





