########################################################################
#
# SIP handle module
#
# 2012 - Ulrik Hoerlyk Hjort
########################################################################
import sys
import pjsua as pj
import threading
import config

######################################################
#
#
#
#
######################################################

def log_cb(level, str, len):
    print str,


# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):
    def __init__(self, sip, call=None):
        pj.CallCallback.__init__(self, call)
        self.sip = sip

    # Notification when call state has changed
    def on_state(self):
        print "Call is ", self.call.info().state_text,
        print "last code =", self.call.info().last_code, 
        print "(" + self.call.info().last_reason + ")"
        
    # Notification when call's media state has changed.
    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            self.sip.lib.conf_connect(call_slot, 0)
            self.sip.lib    .conf_connect(0, call_slot)
            print "Hello world, I can talk!"

######################################################
#
#
#
#
######################################################
class MyAccountCallback(pj.AccountCallback):
    sem = None


    ##################################################
    #
    #
    ##################################################
    def __init__(self, account):
        pj.AccountCallback.__init__(self, account)


    ##################################################
    #
    #
    ##################################################
    def wait(self):
        self.sem = threading.Semaphore(0)
        self.sem.acquire()

    ##################################################
    #
    #
    ##################################################
    def on_reg_state(self):
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()



######################################################
#
#
#
#
######################################################
class Sip():

    def getLib(self):
        return self.lib
    ##################################################
    #
    #
    ##################################################
    def __init__(self, port):
        self.lib  = pj.Lib()
        self.acc = None
        try:
            self.lib.init(log_cfg = pj.LogConfig(level=0, callback=log_cb))

            self.lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(port))
            self.lib.start()
            
        except pj.Error, e:
            print "Exception: " + str(e)
            self.lib.destroy()

    ##################################################
    #
    # Originates a new call
    # INPUT: string: extension, 
    #
    # RETURNS: string: (status, reason)
    ##################################################
    def originate (self, extension):

        try:
            if (self.acc_cb.account.info().reg_status < 200):
                return "Not connected!" 
            else:
                print "Dialing " "sip:"+extension+"@"+config.PBX_Host;
                self.current_call = self.acc.make_call("sip:"+extension+"@"+config.PBX_Host, MyCallCallback(sip=self))
                return "Sent request"

        except pj.Error, e:
            print "Exception: " + str(e)
            self.lib.destroy()

    def hangup (self):
        try:
            if (self.acc_cb.account.info().reg_status < 200):
                return "Not connected." 
            elif not self.current_call.is_valid():
                return "No call to end." 
            else:
                print "Hanging up " + self.current_call.info().uri
                self.current_call.hangup()
                return "Successfully sent hangup request."

        except pj.Error, e:
            print "Exception: " + str(e)
            self.lib.destroy()

    ##################################################
    #
    # register sip client
    # INPUT: string: sip server address, 
    #        string: username, 
    #        string: password, 
    #        int:    sip port
    #
    # RETURNS: string: (status, reason)
    ##################################################
    def register(self,sip_server,username, password, port):

        try:
            self.acc = self.lib.create_account(pj.AccountConfig(sip_server, username, password))

            self.acc_cb = MyAccountCallback(self.acc)
            self.acc.set_callback(self.acc_cb)
            self.acc_cb.wait()

            return "" + str(self.acc.info().reg_status) + "," + self.acc.info().reg_reason
        except pj.Error, e:
            print "Exception: " + str(e)
            self.lib.destroy()



    ##################################################
    #
    # disconnect from server
    #    
    # INPUT: None
    #
    # RETURNS: None
    ##################################################
    def disconnect(self):
            self.lib.destroy()
            self.lib = None


    ##################################################
    #
    #
    ##################################################
    def destroy(self):
            self.lib.destroy()
            self.lib = None


    ##################################################
    #
    #
    ##################################################
    def __del__(self):
            self.lib.destroy()
            self.lib = None
