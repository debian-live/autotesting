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
	xmlstarlet tr ./tests-source/transform-to-test-list.xml ./tests-source/debian-live-all.xml  >$(DESTDIR)/usr/share/autotesting/tests/debian-live-all.xml 
	xmlstarlet tr ./tests-source/transform-to-test-list.xml ./tests-source/debian-live-i386-iso.xml  >$(DESTDIR)/usr/share/autotesting/tests/debian-live-i386-iso.xml
	xmlstarlet tr ./tests-source/transform-to-test-list.xml ./tests-source/debian-live-i386-iso-xfce.xml >$(DESTDIR)/usr/share/autotesting/tests/debian-live-i386-iso-xfce.xml
clean:

remove:
	rm $(DESTDIR)/usr/bin/autotesting
	rm -r $(DESTDIR)/usr/share/autotesting
