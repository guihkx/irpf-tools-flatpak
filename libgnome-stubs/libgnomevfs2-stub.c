// SPDX-License-Identifier: CC0-1.0

/*
 * This is a stub of gnome_vfs_init(), from GnomeVFS 2: https://www.manpagez.com/html/gnome-vfs/gnome-vfs-2.24.1/gnome-vfs-2.0-gnome-vfs-init.php#gnome-vfs-init
 *
 * OpenJDK 11 loads the gnome_vfs_init() symbol dinamically, as a fallback for when the GTK2/GTK3 initialization fails:
 *
 * 1. https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/awt_Desktop.c#L49
 * 2. https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/gnome_interface.c#L52
 *
 * Since OpenJDK 11 only calls gnome_vfs_init() and nothing else from GnomeVFS 2, this is the only function that needs to be added here.
 *
 * For more details, please check out the README.md file.
 *
 */

int gnome_vfs_init(void)
{
    return 1;
}
