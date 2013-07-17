PJSIP_VERSION=2.0.1
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
	make -C pjproject-$(PJSIP_VERSION) dep
	make -C pjproject-$(PJSIP_VERSION)
	touch pjproject

pjproject-$(PJSIP_VERSION): pjproject-$(PJSIP_VERSION).tar.bz2
	@echo Extracting $@.tar.bz2 ...
	@tar xjf $@.tar.bz2 && (echo All OK.) && touch pjproject-$(PJSIP_VERSION)

pjproject-$(PJSIP_VERSION).tar.bz2:
	-wget -H http://www.pjsip.org/release/$(PJSIP_VERSION)/$@	

