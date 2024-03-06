// SPDX-License-Identifier: CC0-1.0

/*
 * This is a stub of gnome_url_show(), from libgnome 2: https://developer-old.gnome.org/libgnome/stable/libgnome-gnome-url.html#gnome-url-show
 *
 * OpenJDK 11 loads the gnome_url_show() symbol right after loading gnome_vfs_init() (see also: libgnomevfs2-stub.c):
 *
 * https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/gnome_interface.c#L52
 *
 * Which will then be called later, only in one place:
 *
 * https://github.com/openjdk/jdk11u-dev/blob/jdk-11%2B28/src/java.desktop/unix/native/libawt_xawt/xawt/awt_Desktop.c#L81
 *
 * Since OpenJDK 11 only calls gnome_url_show() and nothing else from libgnome 2, this is the only function that needs to be added here.
 *
 * For more details, please check out the README.md file.
 *
 */

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#define err(fmt, ...) fprintf(stderr, "%s(): error: " fmt "\n", __func__, ##__VA_ARGS__);

int gnome_url_show(const char *url, __attribute__((unused)) void **error)
{
    pid_t pid;
    int wstatus, ret;
    char *xdg_open[] = { "/usr/bin/xdg-open", (char *)url, NULL };

    pid = fork();

    if (pid < 0) {
        err("fork failed: %s", strerror(errno));
        return 0;
    }
    if (pid == 0) {
        /* child */
        if (execvp(xdg_open[0], xdg_open) == -1) {
            err("spawning xdg-open failed: %s", strerror(errno));
            exit(1);
        }
    }
    /* parent */
    if (waitpid(pid, &wstatus, 0) == -1) {
        /* failed to wait on child process */
        err("waitpid failed: %s\n", strerror(errno));
        return 0;
    }
    if (WIFEXITED(wstatus)) {
        ret = WEXITSTATUS(wstatus) == 0;
    } else {
        err("xdg-open terminated abnormally");
        ret = 0;
    }
    return ret;
}
