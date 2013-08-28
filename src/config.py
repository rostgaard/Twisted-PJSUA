PBX_Host = "raspberrpi"

class Client:
    auto_answer = False
    call_limit  = True #Limits the number of calls a client can have to one.
    next_call_extension = 5901

class PBX:
    #host     = "raspberrypi"
    host     = "responsum.pbx.jay.net"
    username = "1000"
    secret   = "1234"

class PJSUA:
    log_level  = 2
    clock_rate = 44100 
    port       = 5081
    
class Twisted:
    port     = 9002    
    host     = "localhost"
        