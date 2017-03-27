__author__ = "ppgirl"
"""
class INFINITY HONEYD MANAGER
"""
import os
import sys
import time
import socket
import cfg
import prettytable
from cfg import LOG
from template import Template


class InfHoneydMan(object):
    def __init__(self):
        super(InfHoneydMan, self).__init__()

        self.template_list = {}
        self.honeypot_list = {}
        self.config_file = cfg.HONEYD_CFG_PATH
        self.honeyd_sock = cfg.HONEYD_SOCK
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        while True:
            try:
                self.sock.connect(self.honeyd_sock)
                LOG.info("* * * * * * welcome to honeyd * * * * * *\n")
                break
            except:
                LOG.error("MAN ERROR when connecting to honeyd: maybe not running")
                sys.exit(0)
        self.sock.recv(1024)
        self._create_default_template()

    def add_template(self, template):
        self.template_list[template.name] = template

    def del_template(self, template_name):
        self.template_list.pop(template_name, None)

    def find_template(self, template_name):
        tmpl = self.template_list.get(template_name, None)
        if tmpl:
            return tmpl.serialize()
        else:
            return "ERROR: no template named " + template_name

    def list_templates_detail(self):
        tmpl_list_tbl = prettytable.PrettyTable()
        tmpl_list_tbl.field_names = ["Name", "Personality", "TCP port", "UDP port", "Detail"]
        tmpl_list_tbl.align["TCP port"] = 'l'
        tmpl_list_tbl.align["UDP port"] = 'l'
        tmpl_list_tbl.align["Detail"] = 'l'
        for (name, tmpl) in self.template_list.items():
            personality = tmpl.personality
            detail = tmpl.serialize()
            tcp_port = ""
            for (port, action) in tmpl.tcp_action_list.items():
                tcp_port += str(port) + " : " + action + "\n"
            udp_port = ""
            for (port, action) in tmpl.udp_action_list.items():
                udp_port += str(port) + " : " + action + "\n"
            tmpl_list_tbl.add_row([name, personality, tcp_port, udp_port, detail])

        print tmpl_list_tbl

    def list_templates(self):
        tmpl_list_tbl = prettytable.PrettyTable()
        tmpl_list_tbl.field_names = ["Name", "Personality", "TCP port", "UDP port"]
        tmpl_list_tbl.align["TCP port"] = 'l'
        tmpl_list_tbl.align["UDP port"] = 'l'
        for (name, tmpl) in self.template_list.items():
            personality = tmpl.personality
            tcp_port = ""
            for (port, action) in tmpl.tcp_action_list.items():
                tcp_port += str(port) + " : " + action + "\n"
            udp_port = ""
            for (port, action) in tmpl.udp_action_list.items():
                udp_port += str(port) + " : " + action + "\n"
            tmpl_list_tbl.add_row([name, personality, tcp_port, udp_port])

        print tmpl_list_tbl

    def add_honeypot(self, ip, template):
        if template in self.template_list.values():
            self.honeypot_list[ip] = template
        else:
            LOG.error("MAN ERROR when adding honeypot: no template %s", template.name)

    def del_honeypot(self, ip):
        honeypot = self.honeypot_list.pop(ip, None)

    def find_honeypot_template(self, ip):
        tmpl = self.honeypot_list.get(ip, None)
        if tmpl:
            return tmpl.serialize()
        else:
            return "ERROR: no template bind at " + ip + ", maybe default or invalid ip"

    def list_honeypots(self):
        hp_list_tbl = prettytable.PrettyTable()
        hp_list_tbl.field_names = ["IP", "Template"]
        for (ip, tmpl) in self.honeypot_list.items():
            tmpl_name = tmpl.name
            hp_list_tbl.add_row([ip, tmpl_name])
        print hp_list_tbl

    def update_config(self):
        self._mk_config_file()
        self._update_config(self.config_file)

    def update_config_with_file(self, file_path):
        if os.path.exists(file_path):
            self._update_config(file_path)
        else:
            LOG.error("MAN ERROR when updating configuration with file: no file %s", file_path)

    def _create_default_template(self):
        default_template = Template("default")
        self.template_list["default"] = default_template

    def _bind_ip_to_template(self, ip, template):
        return "bind " + ip + " " + template.name + "\n"

    def _mk_config_file(self):
        """
        check if there exist a default template in the template list, if no, create one
        generate 'create template' sentence
        generate bind string
        write to file
        """
        config_content = ""
        if "default" not in self.template_list:
            self._create_default_template()
        for template in self.template_list.values():
            template_str = template.serialize()
            if template_str != "":
                config_content += template_str + "\n"
        for (ip, tmpl) in self.honeypot_list.items():
            template_str = tmpl.serialize()
            if template_str != "":
                config_content += self._bind_ip_to_template(ip, tmpl)

        with open(self.config_file, 'w') as f:
            f.write(config_content)

    def _update_config(self, filepath):
        data = "update " + filepath + "\n"
        try:
            self.sock.send(data)
            recv_str = self.sock.recv(1024)
        except:
            LOG.error("MAN ERROR: honeyd has stopped!")
            sys.exit(0)
        return recv_str.split("\n")[0]



