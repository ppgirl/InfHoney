# InfHonney
A dynamic honeypot generator - based on honeyd

## ui.c
ui.c is based on the ui.c in honeyd (https://github.com/DataSoft/Honeyd).

Online dynamic configuration of honeyd is conducted through the AX_UNIX socket created by honeyd.

To use it, copy ui.c to the honeyd folder, replace the original ui.c, then make & make install.

## InfHoney
The honeyd configuration engine in Python.
