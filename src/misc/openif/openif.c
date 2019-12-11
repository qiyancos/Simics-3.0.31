/*
  Copyright 2004-2007 Virtutech AB
  
  The contents herein are Source Code which are a subset of Licensed
  Software pursuant to the terms of the Virtutech Simics Software
  License Agreement (the "Agreement"), and are being distributed under
  the Agreement.  You should have received a copy of the Agreement with
  this Licensed Software; if not, please contact Virtutech for a copy
  of the Agreement prior to using this Licensed Software.
  
  By using this Source Code, you agree to be bound by all of the terms
  of the Agreement, and use of this Source Code is subject to the terms
  the Agreement.
  
  This Source Code and any derivatives thereof are provided on an "as
  is" basis.  Virtutech makes no warranties with respect to the Source
  Code or any derivatives thereof and disclaims all implied warranties,
  including, without limitation, warranties of merchantability and
  fitness for a particular purpose and non-infringement.
 */
/*
 * openif.c
 *
 * Usage: openif <ifname>
 * 
 * Open a descriptor for capturing packets from the interface <ifname>
 * and a socket for writing raw packets. Pass both back through descriptor 0.
 * Errors are written to stderr.
 *
 * This program needs privileges to run (probably root).
 */

/* These are required for Solaris to include the Unix 95 definitions */
#define _XOPEN_SOURCE 500
#define _XOPEN_SOURCE_EXTENDED 1
#define __EXTENSIONS__ 1

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/uio.h>

#if defined __linux__
 #define LINUX
#elif defined __sun && defined __SVR4
 #define SOLARIS
#else
 #error Only works on Linux and Solaris hosts
#endif

#ifdef LINUX
#include <netpacket/packet.h>
#include <net/ethernet.h>
#include <netinet/in.h>
#include <linux/if.h>

static int
capture_device(char *ifname)
{
        int fd = socket(PF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
        if (fd < 0)
                perror("create capture socket");
        return fd;
}
#endif /* LINUX */

#ifdef SOLARIS
#include <sys/sockio.h>
#include <net/if.h>

static int
capture_device(char *ifname)
{
        int s;
        int fd;
        struct lifconf lifc;
        struct lifreq *lifr;
        /* We could allocate the buffer dynamically, but most system only have
           a small handful of network interfaces. The worst that can happen is
           that we refuse to open a valid interface. */
        char buf[8192];
        char devname[1024];

        /* First verify that the device is really the name of an interface */
        s = socket(AF_INET, SOCK_DGRAM, 0);
        if (s < 0) {
                perror("socket");
                return -1;
        }

        memset(buf, 0, sizeof buf);
        memset(&lifc, 0, sizeof lifc);
        lifc.lifc_family = AF_UNSPEC;
        lifc.lifc_flags = LIFC_EXTERNAL_SOURCE;
        lifc.lifc_len = sizeof buf;
        lifc.lifc_buf = buf;

        if (ioctl(s, SIOCGLIFCONF, &lifc) < 0) {
                perror("ioctl(SIOCGLIFCONF)");
                return -1;
        }

        for (lifr = lifc.lifc_req; (char *)(lifr + 1) <= buf + lifc.lifc_len;
             lifr++) {
                if (strcmp(ifname, lifr->lifr_name) == 0)
                        goto ifname_ok;
        }
        fprintf(stderr, "%s: No such host interface\n", ifname);
        return -1;

 ifname_ok:
        /* construct a device name by prefixing /dev/ to the interface */
        snprintf(devname, sizeof devname, "/dev/%s", ifname);
        fd = open(devname, O_RDWR);
        if (fd < 0) {
                /* Try the same name but without the number at the end */
                int i = strlen(devname) - 1;
                while (i >= 0 && devname[i] >= '0' && devname[i] <= '9')
                        i--;
                devname[i + 1] = '\0';
                fd = open(devname, O_RDWR);
                if (fd < 0)
                        perror("open");
        }
        return fd;
}
#endif /* SOLARIS */

/* Solaris apparently lacks these defines (Unix95) */
#ifndef CMSG_SPACE
#define CMSG_SPACE(size) (sizeof(struct cmsghdr) + (size))
#endif
#ifndef CMSG_LEN
#define CMSG_LEN(size) (sizeof(struct cmsghdr) + (size))
#endif

/* send cap_fd and out_fd through the pipe */
static int
send_fds(int cap_fd, int out_fd, int pipe)
{
        struct msghdr msg = {0};
        struct cmsghdr *cmsg;
        struct iovec iov[1];
        int fds[2];
        union {
                struct cmsghdr cm;
                char control[CMSG_SPACE(sizeof(fds))];
        } buf;
        char databuf[1] = {0};

        fds[0] = cap_fd;
        fds[1] = out_fd;

        /* Linux needs at least one data byte to be sent */
        iov[0].iov_base = databuf;
        iov[0].iov_len = sizeof databuf;
        msg.msg_iov = iov;
        msg.msg_iovlen = 1;

        msg.msg_control = &buf;
        msg.msg_controllen = sizeof buf;

        cmsg = CMSG_FIRSTHDR(&msg);
        cmsg->cmsg_level = SOL_SOCKET;
        cmsg->cmsg_type = SCM_RIGHTS;
        cmsg->cmsg_len = CMSG_LEN(sizeof fds);
        memcpy(CMSG_DATA(cmsg), fds, sizeof fds);

        msg.msg_controllen = cmsg->cmsg_len;
        if (sendmsg(pipe, &msg, 0) < 0) {
                perror("sendmsg");
                fprintf(stderr,
                        "File descriptor %d must be a valid socket for passing"
                        " descriptors\n", pipe);
                return 1;
        }
        return 0;
}

int
main(int argc, char **argv)
{
        char *ifname;
        int cap_fd, out_fd;

        if (geteuid() != 0) {
                fprintf(stderr,
                        "ERROR: The 'openif' helper must be run as root in"
                        " order to open the raw\nnetwork interface on the host"
                        " machine."
                        " See the Simics Install Guide for details.\n");
                return 1;
        }

        if (argc != 2) {
                fprintf(stderr,
                        "usage: openif ifname\n"
                        "This program is used by Simics to connect to the host"
                        " machine's network.\n"
                        "It cannot be used separately.\n");
                return 1;
        }
        ifname = argv[1];

        cap_fd = capture_device(ifname);
        if (cap_fd < 0)
                return 1;

        out_fd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
        if (out_fd < 0) {
                perror("create raw sending socket");
                return 1;
        }
        return send_fds(cap_fd, out_fd, 0);
}

