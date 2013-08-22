# Twisted PJSUA

Hybrid of Python Twisted and PJSUA SIP library.
The purpose of this is to provide a REST-like interface for controlling the SIP library via a browser.

## Overall requirements 
 - python development package
 - pip
 - asound (if you want sound on Linux)
 - depenencies

The following command should take care of the dependencies on Debian/Ubuntu
 sudo apt-get install python-pip libasound2-dev && \
 sudo pip install twisted-web2

### WebUI Requirements
 - jQuery
 - Bootstrap.js

Both should be placed in lib/ of the webroot.

## Build instruction

Start by building the PJSIP/PJSUA library and the corresponding Python egg.
  make pjproject_python

Then install it with the following command. Note: This only install the Python egg - not the PJSIP library.
 sudo make pjproject_python-install

Now you should be able to run the src/twisted_sip.py script with
 python src/twisted_sip.py

The standard configuration listens on localhost:9002

 - Enjoy.
