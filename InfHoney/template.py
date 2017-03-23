__author__ = "ppgirl"
"""
class TEMPLATE
"""
import os
from cfg import LOG


class Template(object):
    def __init__(self, template_name):
        super(Template, self).__init__()

        self.name = template_name
        self.personality = "random"
        self.uptime = 0
        self.droprate = 0
        self.ethernet = "dell"
        self.tcp_default = "closed"
        self.tcp_action_list = {}
        self.udp_action_list = {}

    def set_name(self, name):
        self.name = name

    def set_personality(self, personality):
        self.personality = personality

    def set_uptime(self, uptime):
        self.uptime = uptime

    def set_droprate(self, droprate):
        self.droprate = droprate

    def set_ethernet(self, mac):
        self.ethernet = mac

    def set_tcp_default(self, tcp_default):
        self.tcp_default = tcp_default

    def add_tcp_port(self, tcp_port, tcp_action):
        self.tcp_action_list[tcp_port] = tcp_action

    def add_udp_port(self, udp_port, udp_action):
        self.udp_action_list[udp_port] = udp_action

    def del_tcp_port(self, tcp_port):
        self.tcp_action_list.pop(tcp_port, "closed")

    def del_udp_port(self, udp_port):
        self.udp_action_list.pop(udp_port, "closed")

    def _format_port_action(self, action):
        t_action = action.split(' ')[0]
        if t_action == "open" or t_action == "closed" or t_action == "filtered" or t_action == "proxy":
            return action
        else:
            return "\"" + action + "\""

    def serialize(self):
        string = ""
        string += "create " + self.name + "\n"
        if self.personality == "random":
            string += "set " + self.name + " personality random\n"
        else:
            string += "set " + self.name + " personality \"" + self.personality + "\"\n"
        if self.uptime != 0:
            string += "set " + self.name + " uptime " + str(self.uptime) + "\n"
        if self.droprate != 0:
            string += "set " + self.name + " droprate in " + str(self.droprate) + "\n"
        string += "set " + self.name + " ethernet \"" + self.ethernet + "\"\n"
        string += "set " + self.name + " default tcp action " + self.tcp_default + "\n"
        for (port, action) in self.tcp_action_list.items():
            string += "add " + self.name + " tcp port " + str(port) + " " + self._format_port_action(action) + "\n"
        for (port, action) in self.udp_action_list.items():
            string += "add " + self.name + " udp port " + str(port) + " " + self._format_port_action(action) + "\n"

        return string


class FileTemplate(object):
    def __init__(self, template_name, template_f_path):
        super(FileTemplate, self).__init__()

        self.name = template_name
        self.path = template_f_path

    def serialize(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                string = f.read()

        else:
            LOG.error("FileTemplate Error when serialize template %s: no file %s", self.name, self.path)
            string = ""
        return string
