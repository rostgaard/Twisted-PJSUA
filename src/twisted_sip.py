#######################################################################
#
# Twisted PJUSA main module
#
# 2013 - AdaHeads K/S
# 
# Originally by Ulrik Hoerlyk Hjort
########################################################################

from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource
#from twisted.web2 import error as HTTP_ERROR
import sys
import json
import config
import ah_sip as sip
import logging
from pjsua import CallState, MediaState
from ah_sip import NotConnected

class HTTP_ERROR ():
    BAD_REQUEST = 400
    NOT_FOUND   = 404
    SERVICE_UNAVAILABLE = 503    

class Event_Severities ():
    Information = "Information"
    Warning = "Warning"
    Error = "Error"
    Critical = "Critical"

##########################################################################
#
# HTTP listener class
#
##########################################################################


class Http_Listener(Resource):

    isLeaf = True
    sip_client = sip.Sip(port=5080)
    accounts = {}
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    ######
    # call/answer
    ##
    def answerCall(self, request):
        call_id = request.args['call_id'][0]
        call    = self.sip_client._callList[call_id]
                
        if config.Client.call_limit:
            # Hold all active calls
            for i in self.sip_client._callList:
                if self.sip_client._callList[i].info().media_state == MediaState.ACTIVE:
                    logging.info ("Implicitly put active call " + self.sip_client._callList[i].info().sip_call_id + " on hold due to new pickup.")
                    self.sip_client._callList[i].hold()

        if call.info().state == CallState.INCOMING:
            call.answer()
            message = "call " + call_id + " answered."
        else:
            request.setResponseCode(HTTP_ERROR.BAD_REQUEST)
            message = "call " + call_id + " already answered."
            
        logging.debug (message)
        return json.dumps ({"message" : message})

    ######
    # call/list
    ##
    def listCall(self,request):
        data = []
        #self.sip_client._callList[:] = [call for call in self.sip_client._callList if not x.is_valid()]
        for call in (self.sip_client._callList):
            if not self.sip_client._callList[call].is_valid():
                logging.error ("Skipping invalid call.")
                continue
                
            info = self.sip_client._callList[call].info()
            
            M_state = "Unknown"
            if info.media_state == 0:
                M_state = "NULL"
            elif info.media_state == 1:
                M_state = "ACTIVE"
            elif info.media_state == 2:
                M_state = "LOCAL_HOLD"
            elif info.media_state == 3:
                M_state = "REMOTE_HOLD"
            elif info.media_state == 4:
                M_state = "ERROR"
                
            direction = "UNKNOWN"
            if info.role == 0:
                direction = "outbound"
            elif info.role == 1:
                direction = "inbound"
                
            data.append({'call_id'        : info.sip_call_id,
                         'conf_slot'      : info.conf_slot,
                         'total_time'     : info.total_time,
                         'uri'            : info.uri,
                         'call_time'      : info.call_time,
                         'media_state'    : M_state,
                         'last_code'      : info.last_code,
                         'last_reason'    : info.last_reason,
                         'remote_contact' : info.remote_contact,
                         'state'          : info.state,
                         'state_text'     : info.state_text,
                         'contact'        : info.contact,
                         'role'           : info.role,
                         'direction'      : direction,
                         'media_dir'      : info.media_dir,
                         'remote_uri'     : info.remote_uri})

        return data

    ######
    # call/park
    ##
    def parkCall(self,request):
        call_id = request.args['call_id'][0]
        call    = self.sip_client._callList[call_id]

        call.hold()
        message = "call " + call_id + " held."
        #request.setResponseCode(HTTP_ERROR.BAD_REQUEST)
        #message = "call " + call_id + " already answered."
            
        logging.debug (message)
        return json.dumps ({"message" : message})
    
    ######
    # call/release
    ##
    def releaseCall(self, request):
        call_id = request.args['call_id'][0]
        call    = self.sip_client._callList[call_id]

        call.unhold()
        message = "call " + call_id + " released."
        #request.setResponseCode(HTTP_ERROR.BAD_REQUEST)
        #message = "call " + call_id + " already answered."
            
        logging.debug (message)
        return json.dumps ({"message" : message})

    ######
    # call/originate
    ##
    def pickupNextCall(self, request):
        status = None
        for i in self.accounts:
            if self.accounts[i].fields["info"]["is_default"]:
                status = self.accounts[i].originate(config.Client.next_call_extension)
                return {"message" : "Pickup command completed.", "originate_reponse" : status}
            else:
                return {"message" : "No account.", "originate_reponse" : status}


    ######
    # call/originate
    ##
    def originateCall(self, request):
        status = None
        for i in self.accounts:
            if self.accounts[i].fields["info"]["is_default"]:
                status = self.accounts[i].originate(request.args['extension'][0])
                return {"message" : "Originate command completed.", "originate_reponse" : status}
            else:
                return {"message" : "No account.", "originate_reponse" : status}
        return {"message" : "Originate command completed.", "originate_reponse" : status}

    ######
    # call/hangup
    ##
    def hangupCall(self, request):
        message = None
        try:
            call_id = request.args['call_id'][0]
            call    = self.sip_client._callList[call_id]
    
            call.hangup()
            message = "call " + call_id + " hung up."
        except KeyError:
            request.setResponseCode(HTTP_ERROR.NOT_FOUND)
            message = "call " + call_id + " already hung up."
            
        logging.debug (message)
        return {"message" : message}

    ######
    # account/add
    ##
    def addAccount(self, request):
        username = request.args['username'][0]
        password = request.args['password'][0]
        domain = request.args['domain'][0]
            
        new_account = sip.Sip.Account (username=username, password=password, domain=domain, sip_handle=self.sip_client)
        key = username + '@' + domain
            
        if not self.accounts.has_key(key):
            self.accounts.update ({key : new_account})
                
            return {"message" : 'Added account ' + username + '@' + domain + '.'} 
        else:
            request.setResponseCode(HTTP_ERROR.BAD_REQUEST)
            return {"message" : username + '@' + domain + " already added." }

    ######
    # account/add
    ##
    def listAccount(self,request):
        data = []
        for account in self.accounts:
            obj = self.accounts[account].fields
            data.append(obj)
                
        return data; 
    
    ######
    # account/remove
    ##
    def removeAccount(self,request):
        account = request.args['account'][0]
        if not self.accounts.has_key(account):
            request.setResponseCode(HTTP_ERROR.NOT_FOUND)
            return {"message" : account + " not found." }
        else:
            del self.accounts[account]
            return {"message" : account + " removed." }

    ######
    # account/register
    ##
    def registerAccount(self,request):
        try:
            account = request.args['account'][0]
            status = self.accounts[account].register()
            message = "Registration command completed."
                
            logging.debug (message + " (status " + str (status) + ")")
                
            if status != 200:
                request.setResponseCode(HTTP_ERROR.SERVICE_UNAVAILABLE)
                    
            return {"message" : status}
            
        except KeyError:                
            request.setResponseCode(HTTP_ERROR.NOT_FOUND)
                
            return {"message" : "Account " + account + " not found.", "registration_status" : None}

    ######
    # account/unregister
    ##
    def unregisterAccount(self,request):
        try:
            account = request.args['account'][0]
            self.accounts[account].unregister()
            message = "Unregistration command completed."
                
            logging.debug (message)
                
            return {"message" : message}
            
        except KeyError:                
            request.setResponseCode(HTTP_ERROR.NOT_FOUND)
                
            return {"message" : "Account " + account + " not found.", "registration_status" : None}

    ######
    # Error conditions
    ##        
    def checkForErrors(self, request):
        if self.sip_client == None:
            message = "Invalid SIP client!"
            severity = Event_Severities.Critical
            responseCode = HTTP_ERROR.SERVICE_UNAVAILABLE
            
            logging.debug (message)
            
            request.setResponseCode(responseCode)
            return {"severity" : severity , "message" : message}
    #####
    # HTTP Routes
    ##
    def render_GET(self, request):
        request.headers['content_type'] = 'application/json';
        request.headers['Access-Control-Allow-Origin'] = '*';
                
        try:
            response = self.checkForErrors(request)
            if response != None:
                None
        
            elif request.path == "/call/answer":
                response = self.answerCall(request)

            elif request.path == "/call/list":
                response = self.listCall(request)

            elif request.path == "/call/park":
                response = self.parkCall(request)

            elif request.path == "/call/release":
                response = self.releaseCall(request)

            elif request.path == "/call/pickup":
                response = self.pickupCall(request)

            elif request.path == "/call/pickup_next":
                response = self.pickupNextCall(request)

            elif request.path == "/call/originate":
                response = self.originateCall(request)

            elif request.path == "/call/hangup":
                response = self.hangupCall(request)

            elif request.path == "/account/remove":
                response = self.removeAccount(request)

            elif request.path == "/account/add":
                response = self.addAccount(request)
                
            elif request.path == "/account/list":
                response = self.listAccount(request)
        
            elif request.path == "/account/unregister":
                response = self.unregisterAccount(request)

            elif request.path == "/account/register":
                response = self.registerAccount(request)
            else:
                request.setResponseCode(HTTP_ERROR.NOT_FOUND)
                response = {"message" : "Not found"}                
            
            return json.dumps (response)
        
        except NotConnected:
            responseCode = HTTP_ERROR.SERVICE_UNAVAILABLE
            message = "No SIP account connected."

            logging.error (message)
            request.setResponseCode(responseCode)
                
            return json.dumps ({'message': message, "SIP_response" : None})


##########################################################################
#
#
#
##########################################################################
def main():
    if len(sys.argv) != 1:
        print "Usage: " + sys.argv[0] + " http_port"
        exit(0)

    http_port = int(config.Twisted.port)
    resource = Http_Listener()
    factory = Site(resource)
    reactor.listenTCP(http_port, factory)#, interface=config.Twisted.host)
    reactor.run()


if __name__ == "__main__":
    main()
