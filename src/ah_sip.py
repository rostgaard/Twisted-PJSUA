########################################################################
#
# SIP handle module
#
# 2013 AdaHeads K/S
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
class CallEventHandler(pj.CallCallback):
    def __init__(self, sip, call=None):
        pj.CallCallback.__init__(self, call)
        self.sip = sip

    # Notification when call state has changed
    def on_state(self):
        if not self.sip._callList.has_key(self.call.info().sip_call_id):
            self.sip._callList[self.call.info().sip_call_id] = self.call
            
        print "callstatechange: " + str(self.call.info().state) + " " + self.call.info().state_text 
        if self.call.info().state == pj.CallState.DISCONNECTED:
            del self.sip._callList[self.call.info().sip_call_id]
        
    # Notification when call's media state has changed.
    def on_media_state(self):
        print "callmediastatechange: " + str(self.call.info().media_state) 
        if self.call.info().media_state == pj.MediaState.ACTIVE or self.call.info().media_state == pj.MediaState.REMOTE_HOLD:
            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            self.sip.lib.conf_connect(call_slot, 0)
            self.sip.lib.conf_connect(0, call_slot)
    
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
    def __init__(self, account, sip):
        pj.AccountCallback.__init__(self, account)
        self._sip = sip

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

    def on_incoming_call(self, call):
        #TODO: Check if there is at least one active account.
        self._sip._callList[call.info().sip_call_id] = call
        print "MyAccountCallback: Got new call"
        my_cb = CallEventHandler(sip=self._sip)
        call.set_callback(my_cb)
        
        if config.Client.auto_answer:
            call.answer()

class NotConnected(Exception):
    pass

######################################################
#
#
#
#
######################################################
class Sip():

    lib       = None
    _callList = {}
    isReady   = False
        
    class Account:
        """SIP Account"""

        username              = None
        domain                = None
        _sip_handle           = None
        _pjsua_account_handle = None
        _pjsua_config         = None
        _accountCallback      = None

        ##################################################
        #
        # Originates a new call
        # INPUT: string: extension, 
        #
        # RETURNS: string: (status, reason)
        ##################################################
        def originate (self, extension):
            try:
                if (self._accountCallback.account.info().reg_status < 200):
                    return "Not connected!" 
                else:
                    print "Dialing " "sip:"+str(extension)+"@"+config.PBX_Host;
                    self.current_call = self._pjsua_account_handle.make_call("sip:"+str(extension)+"@"+config.PBX_Host, CallEventHandler(sip=self._sip_handle))
                    return "Sent request"
    
            except pj.Error, e:
                print "Exception: " + str(e)
                self._sip_handle.destroy()

        def __init__ (self, username, password, domain, sip_handle):
            self.username    = username
            self.domain      = domain
            self._sip_handle = sip_handle 
            self._accountCallback = MyAccountCallback(self, self._sip_handle)
        
            # Register the account in the PJSUA lib.
            self._pjsua_config = pj.AccountConfig(domain=self.domain, username=self.username, password=password)
            self._pjsua_config.reg_timeout = 1
             
        def __eq__ (self, other):
            return self.username == other.username and self.domain == other.domain;
        
        def register(self):
            if self._pjsua_account_handle == None:
                self._pjsua_account_handle = self._sip_handle.lib.create_account (self._pjsua_config , cb=self._accountCallback)
                self._sip_handle.isReady = True                
            else:
                self._pjsua_account_handle.set_registration(renew=True)
                
            self._accountCallback.wait()
            return self._pjsua_account_handle.info().reg_status

        def unregister(self):
            if self._pjsua_account_handle != None:
                self._pjsua_account_handle.set_registration (renew=False)      
        
        @property
        def fields(self):
            if self._pjsua_account_handle != None:
                return {"account" : self.username+'@'+self.domain, "info" : self._pjsua_account_handle.info().__dict__}
            else:
                return {"account" : self.username+'@'+self.domain, "info" : None}
                

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
            mc = pj.MediaConfig()
            mc.clock_rate = config.PJSUA.clock_rate 
            mc.snd_clock_rate = config.PJSUA.clock_rate

            self.lib.init(log_cfg = pj.LogConfig(level=config.PJSUA.log_level, callback=log_cb), media_cfg=mc)

            self.lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(port))
            self.lib.start()
            
        except pj.Error, e:
            print "Exception: " + str(e)
            self.lib.destroy()

    @property
    def _is_connected(self):
        if not hasattr(self, 'acc_cb'):
            return False
        else:
            return self.acc_cb.account.info().reg_status == 200
        
        return False

    def park (self,call):
        try:
            #if (not self._is_connected):
            #    raise NotConnected('No account connected')
            #else:
                call.hold();
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
