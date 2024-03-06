DESTDIR ?= /app
LIBDIR ?= lib

CC ?= gcc
FLAGS = -Wall -Wextra -shared -fPIC

OUT_GNOMEVFS2 = libgnomevfs-2.so.0
OUT_GNOME2 = libgnome-2.so.0

all: libgnomevfs2 libgnome2

libgnomevfs2: libgnomevfs2-stub.c
	$(CC) $(FLAGS) $(CFLAGS) -o $(OUT_GNOMEVFS2) $<

libgnome2: libgnome2-stub.c
	$(CC) $(FLAGS) $(CFLAGS) -o $(OUT_GNOME2) $<

install: all
	install -Dm755 $(OUT_GNOMEVFS2) -t $(DESTDIR)/$(LIBDIR)
	install -Dm755 $(OUT_GNOME2) -t $(DESTDIR)/$(LIBDIR)

clean:
	rm -f $(OUT_GNOMEVFS2) $(OUT_GNOME2)

.PHONY: all libgnomevfs2 libgnome2 install clean
