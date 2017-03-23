import sys
from cfg import LOG
from manager import InfHoneydMan
from template import Template, FileTemplate


def main():
    try:
        manager = InfHoneydMan()
        windows = Template("windows")
        windows.set_personality("Microsoft Windows NT 4.0 SP3")
        windows.set_uptime(1728650)
        windows.set_ethernet("dell")
        windows.set_tcp_default("closed")
        windows.add_tcp_port(80, "/home/honeyd/honeyd/Honeyd-master/scripts/web.sh")
        windows.add_tcp_port(22, "/home/honeyd/honeyd/Honeyd-master/scripts/test.sh")
        windows.add_tcp_port(23, "/home/honeyd/honeyd/Honeyd-master/scripts/router-telnet.pl")
        windows.add_udp_port(53, "open")
        windows.add_udp_port(137, "open")
        windows.add_udp_port(161, "open")
        windows.add_udp_port(162, "filtered")

        ubuntu = Template("ubuntu")
        ubuntu.set_personality("Linux 2.6.15 (Ubuntu)")
        ubuntu.set_ethernet("dell")
        ubuntu.set_tcp_default("closed")
        ubuntu.add_tcp_port(80, "/home/honeyd/honeyd/Honeyd-master/scripts/web.sh")
        ubuntu.add_tcp_port(22, "/home/honeyd/honeyd/Honeyd-master/scripts/test.sh")
        ubuntu.add_tcp_port(23, "/home/honeyd/honeyd/Honeyd-master/scripts/router-telnet.pl")
        ubuntu.add_udp_port(54, "open")
        ubuntu.add_udp_port(138, "open")
        ubuntu.add_udp_port(163, "open")
        ubuntu.add_udp_port(164, "filtered")

        manager.add_template(windows)
        manager.add_template(ubuntu)
        manager.add_honeypot("192.168.193.97", windows)
        manager.add_honeypot("192.168.193.98", ubuntu)
        manager.list_templates()
        manager.list_honeypots()
        manager.update_config()
    except KeyboardInterrupt:
        LOG.info("MAIN ERROR: keyboard interrupt, now quit")
        sys.exit(0)

if __name__ == "__main__":
    main()
