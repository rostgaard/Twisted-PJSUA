PJSIP_VERSION=2.1
BootstrapJS_Version=3.0.0
PREFIX=$(PWD)/pjproject
SUDO=sudo

all: dependencies

install: pjproject_python-install

clean:
	-rm -f *~ *pyc

dependencies: pjproject

buildclean:
	-rm -rf pjproject-$(PJSIP_VERSION)
	-rm pjproject

# Cached files
distclean: clean buildclean
	-rm pjproject-$(PJSIP_VERSION).tar.bz2

pjproject_python: pjproject
	make -C pjproject-$(PJSIP_VERSION)/pjsip-apps/src/python

pjproject_python-install: pjproject_python
	make -C pjproject-$(PJSIP_VERSION)/pjsip-apps/src/python install

pjproject: pjproject-$(PJSIP_VERSION)
	(cd pjproject-$(PJSIP_VERSION) && ./configure --prefix=$(PREFIX) CFLAGS=-fPIC CXXFLAGS=-fPIC)
	#(cd pjproject-$(PJSIP_VERSION) && ./configure --prefix=$(PREFIX))
	make -C pjproject-$(PJSIP_VERSION) dep
	make -C pjproject-$(PJSIP_VERSION)
	touch pjproject

pjproject-$(PJSIP_VERSION): pjproject-$(PJSIP_VERSION).tar.bz2
	@echo Extracting $@.tar.bz2 ...
	@tar xjf $@.tar.bz2 && (echo All OK.)
	@echo Applying 2.1 Hotfix...
	@-mv pjproject-$(PJSIP_VERSION).0 pjproject-$(PJSIP_VERSION)

pjproject-$(PJSIP_VERSION).tar.bz2:
	-wget -N http://www.pjsip.org/release/$(PJSIP_VERSION)/$@	

bootstrapjs: bootstrapjs-$(BootstrapJS_Version)

bootstrapjs-$(BootstrapJS_Version):
	wget -N https://github.com/twbs/bootstrap/archive/v$(BootstrapJS_Version).zip
