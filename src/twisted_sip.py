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
from threading import Thread
from twisted.web2 import server, http, resource, channel
from twisted.web2 import static, http_headers, responsecode
from twisted.web2 import error

import sys
import config
import ah_sip as sip


##########################################################################
#
# HTTP listener class
#
##########################################################################
class Http_Listener(Resource):

    isLeaf = True
    sip_client = sip.Sip(port=5081)

    def render_GET(self, request):
        request.headers['content_type'] = 'application/json';
        request.headers['Access-Control-Allow-Origin'] = 'localhost';
        
        if request.path == "/originate":
            status = self.sip_client.originate(request.args['extension'][0])
            return '{"message" : "Originate command completed.", "originate_reponse" : "'+status+'"}'

        elif request.path == "/hangup":
            status = self.sip_client.hangup()
            return '{"message" : "Hangup command completed.", "hangup_reponse" : "'+status+'"}'

        elif request.path == "/register":
            if self.sip_client == None:
                request.setResponseCode(error.SERVICE_UNAVAILABLE)
                return '{"severity" : "Critical", "message" : "Invalid SIP client!"}'
            else:
                status = self.sip_client.register(request.args['domain'][0],request.args['username'][0],request.args['password'][0],5080)
                return '{"message" : "Registration command completed.", "registration_status" : "'+status+'"}'

        elif request.path == "/disconnect":
            status = self.sip_client.disconnect()
            return '{"message" : "Hangup command completed.", "hangup_reponse" : "'+status+'"}'

        request.setResponseCode(error.NOT_FOUND)
        return '{"message" : "Not found"}'


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
    reactor.listenTCP(http_port, factory, interface=config.Twisted.host)
    reactor.run()


if __name__ == "__main__":
    main()
