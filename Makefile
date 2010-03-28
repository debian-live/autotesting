LIST = debian-live-all.xml debian-live-i386-iso.xml debian-live-i386-iso-xfce.xml debian-live-60alpha1-i386-iso-xfce.xml debian-live-60alpha1-all.xml debian-live-60alpha1-ppc-hdd-standard.xml

all: install

install: autotesting

autotesting:
	mkdir -p $(DESTDIR)/usr/bin
	cp ./autotesting.py $(DESTDIR)/usr/bin/autotesting
	chmod a+x $(DESTDIR)/usr/bin/autotesting
	mkdir -p $(DESTDIR)/usr/share/autotesting
	cp ./README $(DESTDIR)/usr/share/autotesting/README
	mkdir -p $(DESTDIR)/usr/share/autotesting/tests
	cp -r ./tests/* $(DESTDIR)/usr/share/autotesting/tests/
	# Not an expert on Makefile - feel free to improve.
	for template in $(LIST);do \
	xmlstarlet tr ./tests-source/transform-to-test-list.xml ./tests-source/"$$template" | xmlstarlet fo -s 2 - >$(DESTDIR)/usr/share/autotesting/tests/"$$template" ; \
	done
	
clean:

remove:
	rm $(DESTDIR)/usr/bin/autotesting
	rm -r $(DESTDIR)/usr/share/autotesting
