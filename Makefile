LIST = build-60alpha1-i386-iso-hybrid-lxde-desktop-daily.xml build-60alpha1-amd64-iso-hybrid-all-monthly.xml build-60alpha1-powerpc-iso-all-monthly.xml build-60alpha1-i386-iso-hybrid-all-monthly.xml 

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
	xmlstarlet tr ./tests-source/build-stage1.xml ./tests-source/"$$template" | xmlstarlet tr ./tests-source/transform-to-test-list.xml | xmlstarlet fo -s 2 -  >$(DESTDIR)/usr/share/autotesting/tests/"$$template" ; \
	done
	# Make a full list
	cp ./tests-source/merge-list.xml ./tests-source/merge-tests.xml $(DESTDIR)/usr/share/autotesting/tests/
	xmlstarlet tr $(DESTDIR)/usr/share/autotesting/tests/merge-tests.xml $(DESTDIR)/usr/share/autotesting/tests/merge-list.xml >$(DESTDIR)/usr/share/autotesting/tests/full.xml
	rm $(DESTDIR)/usr/share/autotesting/tests/merge-tests.xml $(DESTDIR)/usr/share/autotesting/tests/merge-list.xml

	
clean:

remove:
	rm $(DESTDIR)/usr/bin/autotesting
	rm -r $(DESTDIR)/usr/share/autotesting
