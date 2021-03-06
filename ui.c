/*
 * Copyright (c) 2001, 2004 Niels Provos <provos@citi.umich.edu>
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <sys/types.h>

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <sys/queue.h>
#ifdef HAVE_SYS_TIME_H
#include <sys/time.h>
#endif
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stdlib.h>
#include <fcntl.h>
#include <stdio.h>
#include <errno.h>
#include <err.h>
#include <unistd.h>
#include <syslog.h>
#include <string.h>

#include "config.h"

#include <event.h>
#include <dnet.h>

#include "honeyd.h"
#include "template.h"
#include "ui.h"
#include "parser.h"
#ifdef HAVE_PYTHON
#include "pyextend.h"
#endif

char *ui_file = UI_FIFO;

#define PROMPT		"InfH> "
#define WHITESPACE	" \t"

char *strnsep(char **, char *);
char tmpbuf[1024];

char *
make_prompt(void)
{
	static char tmp[128];
	extern int honeyd_nconnects;
	extern int honeyd_nchildren;

	snprintf(tmp, sizeof(tmp), "%dC %dP %s",
	    honeyd_nconnects, honeyd_nchildren,
	    PROMPT);

	return (tmp);
}

int
ui_write_prompt(struct uiclient *client)
{
	char *tmp = make_prompt();

	evbuffer_add(client->outbuf, tmp, strlen(tmp));
	event_add(client->ev_write, NULL);

	return (0);
}

int
ui_buffer_prompt(struct uiclient *client)
{
	char *tmp = make_prompt();

	evbuffer_add(client->outbuf, tmp, strlen(tmp));
	return (0);
}

void
ui_dead(struct uiclient *client)
{
	syslog(LOG_NOTICE, "%s: ui on fd %d is gone", __func__, client->fd);

	event_del(client->ev_read);
	event_del(client->ev_write);

	close(client->fd);
	evbuffer_free(client->inbuf);
	evbuffer_free(client->outbuf);
	free(client);
}

void
ui_handle_command(struct evbuffer *buf, char *original)
{
	/*char output[1024];*/
	char *command, *line = original;
	char output_error[12] = "BAD COMMAND\n";
	char output_success[8] = "SUCCESS\n";
	char output_fail[5] = "FAIL\n";

	command = strnsep(&line, WHITESPACE);
	FILE *fp;
	if (strcasecmp("update", command) == 0) {
		if ((fp = fopen(line, "r")) == NULL) {
			evbuffer_add(buf, output_fail, strlen(output_fail));
			return;
		}
		fclose(fp);
		template_free_all(TEMPLATE_FREE_DEALLOCATE);
		config_read(line);
		evbuffer_add(buf, output_success, strlen(output_success));
	} else {
		evbuffer_add(buf, output_error, strlen(output_error));
	}
	return;
}

void
ui_writer(int fd, short what, void *arg)
{
	struct uiclient *client = arg;
	struct evbuffer *buffer = client->outbuf;
	int n;

	n = evbuffer_write(buffer, fd);
	if (n == -1) {
		if (errno == EINTR || errno == EAGAIN)
			goto schedule;
		ui_dead(client);
		return;
	} else if (n == 0) {
		ui_dead(client);
		return;
	}

	evbuffer_drain(buffer, n);

 schedule:
	if (evbuffer_get_length(buffer))
		event_add(client->ev_write, NULL);
}

void
ui_handler(int fd, short what, void *arg)
{
	struct uiclient *client = arg;
	struct evbuffer *mybuf = client->inbuf;

	if (evbuffer_read(mybuf, fd, -1) <= 0)
	{
		ui_dead(client);
		return;
	}

	size_t length;
	char *line;
	line = evbuffer_readln(mybuf, &length, EVBUFFER_EOL_ANY);
	syslog(LOG_NOTICE, "-- InfH received command: %s", line);
	if (line == NULL)
	{
		line = evbuffer_readln(mybuf, &length, EVBUFFER_EOL_ANY);
	}
	while(line != NULL)
	{
		ui_handle_command(client->outbuf, line);

		evbuffer_drain(mybuf, length);
		line = evbuffer_readln(mybuf, &length, EVBUFFER_EOL_LF);
	}

	ui_write_prompt(client);
	event_add(client->ev_read, NULL);
}

void
ui_greeting(struct uiclient *client)
{
	struct timeval tv;
	extern struct timeval honeyd_uptime;

	gettimeofday(&tv, NULL);
	timersub(&tv, &honeyd_uptime, &tv);
	evbuffer_add_printf(client->outbuf,
	    "Honeyd %s Management Console\n"
	    "Copyright (c) 2004 Niels Provos.  All rights reserved.\n"
	    "See LICENSE for licensing information.\n"
	    "Up for %ld seconds.\n",
	    VERSION, tv.tv_sec);
}

void
ui_new(int fd, short what, void *arg)
{
	int newfd;
	struct uiclient *client;

	if ((newfd = accept(fd, NULL, NULL)) == -1) {
		warn("%s: accept");
		return;
	}

	if ((client = calloc(1, sizeof(struct uiclient))) == NULL) {
		warn("%s: calloc", __func__);
		close(newfd);
		return;
	}

	client->fd = newfd;
	client->inbuf = evbuffer_new();
	client->outbuf = evbuffer_new();

	if (client->inbuf == NULL || client->outbuf == NULL)
	{
		syslog(LOG_ERR, "%s: evbuffer_new",__func__);
		exit(EXIT_FAILURE);
	}

	syslog(LOG_NOTICE, "%s: New ui connection on fd %d", __func__, newfd);

	client->ev_read = event_new(libevent_base, newfd, EV_READ, ui_handler, client);
	event_priority_set(client->ev_read, 0);
	event_add(client->ev_read, NULL);

	client->ev_write = event_new(libevent_base, newfd, EV_WRITE, ui_writer, client);
	event_priority_set(client->ev_write, 0);

	//ui_greeting(client);
	ui_write_prompt(client);
}

void
ui_init(void)
{
        struct stat st;
        struct sockaddr_un ifsun;
	int ui_socket;

        /* Don't overwrite a file */
        if (lstat(ui_file, &st) == 0) {
                if ((st.st_mode & S_IFMT) == S_IFREG) {
                        errno = EEXIST;
                        syslog(LOG_ERR, "%s: could not create FIFO: %s", __func__, ui_file);
                        		exit(EXIT_FAILURE);
                }
	}

        /* No need to know about errors.  */
        unlink(ui_file);

        ui_socket = socket(AF_UNIX, SOCK_STREAM, 0);
        if (ui_socket == -1)
        {
        	syslog(LOG_ERR, "%s: socket", __func__);
        	exit(EXIT_FAILURE);
        }
        if (setsockopt(ui_socket, SOL_SOCKET, SO_REUSEADDR,
                       &ui_socket, sizeof (ui_socket)) == -1)
        {
        	syslog(LOG_ERR, "%s: setsockopt", __func__);
        	exit(EXIT_FAILURE);
        }

        memset(&ifsun, 0, sizeof (ifsun));
        ifsun.sun_family = AF_UNIX;
        strlcpy(ifsun.sun_path, ui_file, sizeof(ifsun.sun_path));
#ifdef HAVE_SUN_LEN
        ifsun.sun_len = strlen(ifsun.sun_path);
#endif /* HAVE_SUN_LEN */
        if (bind(ui_socket, (struct sockaddr *)&ifsun, sizeof (ifsun)) == -1)
        {
        	syslog(LOG_ERR, "%s: bind error: %s", __func__, strerror(errno));
        	exit(EXIT_FAILURE);
        }

        if (listen(ui_socket, 5) == -1)
        {
        	syslog(LOG_ERR, "%s: listen error: %s", __func__, strerror(errno));
        	exit(EXIT_FAILURE);
        }

	struct event *ev_accept = event_new(libevent_base, ui_socket, EV_READ | EV_PERSIST, ui_new, NULL);
	event_priority_set(ev_accept, 0);
	event_add(ev_accept, NULL);
}
