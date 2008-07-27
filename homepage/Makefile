# Makefile

WORKDIR = $(shell echo $(PWD))
DESTDIR = $(shell echo $(PWD) | sed -e 's/\.wml//')
SUBDIRS =

INCLUDES = $(WORKDIR)/includes

WMK = /usr/bin/wmk
WMKOPT = -I $(INCLUDES) -D IMGROOT=$(WORKDIR)/images -D DOCROOT="" --all 

WMLFILES = $(wildcard *.wml)
HTMLFILES = $(patsubst %.wml,%.html,$(WMLFILES))

existing-SUBS := $(shell for dir in $(wildcard $(SUBS)) ''; do test -d $$dir && echo $$dir; done)
existing-SUBS-build := $(addsuffix -build,$(existing-SUBS))
existing-SUBS-clean := $(addsuffix -clean,$(existing-SUBS))
existing-SUBS-cleandest := $(addsuffix -cleandest,$(existing-SUBS))


all:	make

$(existing-SUBS-build):
	$(MAKE) -C $(subst -build,,$@)

make:
	$(existing-SUBS-build)
	$(WMK) $(WMKOPT)
	rm -fv screenshots/*_sm.png

$(existing-SUBS-clean):
	$(MAKE) -C $(subst -clean,,$@) clean

clean: $(existing-SUBS-clean)
	rm -f $(HTMLFILES)
	rm -fv screenshots/*_sm.png
