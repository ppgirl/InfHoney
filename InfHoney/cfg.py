__author__ = "ppgirl"

import logging
import sys

# log
LOG = logging.getLogger('inf_honey')
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler(sys.stderr))

# cfg
HONEYD_SOCK = r"/var/run/honeyd.sock"
HONEYD_CFG_PATH = r"/home/honeyd/honeyd/honeyd-config/honeyd.conf"
# HONEYD_CFG_PATH = r"honeyd.conf"
