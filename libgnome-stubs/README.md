## About

This directory contains C sources with dumb implementations of APIs present in two defunct projects: [libgnome](https://developer-old.gnome.org/libgnome/stable/) and [GnomeVFS](https://www.manpagez.com/html/gnome-vfs/gnome-vfs-2.24.1/).

For GnomeVFS, the only API symbol implemented is [`gnome_vfs_init()`](https://www.manpagez.com/html/gnome-vfs/gnome-vfs-2.24.1/gnome-vfs-2.0-gnome-vfs-init.php#gnome-vfs-init).

For libgnome, the only API symbol implemented is [`gnome_url_show()`](https://developer-old.gnome.org/libgnome/stable/libgnome-gnome-url.html#gnome-url-show).

Keep reading to understand the point of all this.

## The problem

All Java apps running under Flatpak that use the [`java.awt.Desktop.browse()`](https://docs.oracle.com/en/java/javase/11/docs/api/java.desktop/java/awt/Desktop.html#browse(java.net.URI)) API, are broken.

That API can be used to, among other things, open URLs with the default web browser, which in [IRPF](https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/download/pgd/dirpf)🇧🇷's case, is a must have:

Recent editions of IRPF implement [single sign-on (SSO)](https://en.wikipedia.org/wiki/Single_sign-on), which works by launching the default web browser and loading an authentication page from the Brazilian government.

Users can then log in, and IRPF will get an authentication token.

But because that Java API is essentially broken under Flatpak, that SSO feature won't work.

## Context and history (feel free to skip)

Back in 2022, I used to package IRPF apps using the [GNOME Runtime](https://docs.flatpak.org/en/latest/available-runtimes.html#gnome).

It was the logical thing to do after I learned that OpenJDK 11 [relies](https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/awt_Desktop.c#L78) on GTK's [`gtk_show_uri()`](https://docs.gtk.org/gtk3/func.show_uri.html) API to open URLs (when a Java app uses the `java.awt.Desktop.browse()` API, of course). 

At the time, only the GNOME Runtime would include GTK 3 libraries. As of today, that's not true anymore: The [Freedesktop Runtime](https://docs.flatpak.org/en/latest/available-runtimes.html#freedesktop) now includes GTK 3 libraries too.

Anyway, if we read the documentation of GTK's [`gtk_show_uri_on_window()`](https://docs.gtk.org/gtk3/func.show_uri_on_window.html#description) (a replacement for the now deprecated `gtk_show_uri()`), we'll find this:

>[...] you need to install `gvfs` to get support for uri schemes such as `http://` [...]

I thought: "Fine, I know the GNOME Runtime includes gvfs anyway". But as I later learned, it's not *that* simple...

In 2023, I got a [bug report](https://github.com/flathub/br.gov.fazenda.receita.irpf/issues/53) from a Fedora Kinoite (KDE) user, that the SSO feature wasn't working for him.

And sure enough, after I set up Kinoite in a VM, I was able to confirm that IRPF wasn't able to open URLs with the default web browser.

The (apparent) reason for that, is because gvfs needs to be installed *and running on the host*! I.e., having gvfs libraries only on the Flatpak side is not enough to open URLs!

But expecting users to install a system component just to make URLs open, is ludicrous: It can be slightly annoying if they use an immutable distro, or just plain impossible if they lack permission to install system packages.

## Solutions

The *real* solution, in my opinion, should be implemented in OpenJDK itself: Perhaps they could fall back to [`xdg-open`](https://man.archlinux.org/man/xdg-open.1.en) when `gtk_show_uri()` fails.

Another alternative, would be patching this behavior in Flatpak's [OpenJDK 11 extension](https://github.com/flathub/org.freedesktop.Sdk.Extension.openjdk11): In fact, [a pull request](https://github.com/flathub/org.freedesktop.Sdk.Extension.openjdk11/pull/16) is already open to deal with this problem, but I don't think it will go anywhere...

A third "solution" (also known as a "ugly hack"), is implemented here, by these C stubs! Read the next section to understand how and why this works.

## Okay, so WTF is this?

First, I'll describe how OpenJDK 11 decides to open URLs when a Java app uses the `java.awt.Desktop.browse()` API:

OpenJDK [tries to load](https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/awt_Desktop.c#L46) GTK 3 libraries.

If that works, OpenJDK [will use](https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/awt_Desktop.c#L78) the `gtk_show_uri()` API from GTK 3 to open URLs. But remember: This requires the gvfs daemon to be running on the host to work properly, so it's not an interesting path for us.

If GKT 3 fails to load, OpenJDK [tries to load](https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/awt_Desktop.c#L49) GnomeVFS and libgnome.

If that works, OpenJDK [will use](https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/awt_Desktop.c#L81) the `gnome_url_show()` API from libgnome to open URLs.

But as stated in the beginning of this README, GnomeVFS and libgnome are both defunct (and unmaintained) libraries.

So, the idea here is to make naïve/dumb implementations of `gnome_vfs_init()` (from GnomeVFS) and `gnome_url_show()` (from libgnome).

Then, we build and install these two fake libraries to `/app/lib`, and then invoke `java` with the `-Djdk.gtk.version=2` option, which forces the OpenJDK to try to load GTK 2 libraries (which we don't provide).

And because GTK 2 loading is guaranteed to fail, OpenJDK will then fall into our GnomeVFS/libgnome trap, and use our stub implementations instead!
