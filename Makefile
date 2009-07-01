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
	
clean:

remove:
	rm $(DESTDIR)/usr/bin/autotesting
	rm -r $(DESTDIR)/usr/share/autotesting
