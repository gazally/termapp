#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals

import io
import os
import readline
import sys


def run_client(path):
    encoding = sys.stdin.encoding
    with open(os.path.join(path, ".up.fifo"), "w") as pipeout:
        pipeout.write(encoding + "\n")

    pipein = io.open(os.path.join(path, ".down.fifo"), "r",
                     encoding=encoding, buffering=1)
    pipeout = io.open(os.path.join(path, ".up.fifo"), "w",
                      encoding=encoding, buffering=1)

    def readline():
        while True:
            try:
                return pipein.readline()
            except KeyboardInterrupt:
                print("Sorry, interrupting the interpreter now could "
                      "destabilize the Indigo plugin. If you think it's "
                      "really hung, reloading the plugin from the Indigo "
                      "Plugins menu is probably the best idea.")
    try:
        while True:
            cmd = readline()
            if not cmd:
                break
            elif cmd.startswith("ENCODING"):
                pipeout.write(encoding + "\n")
            elif cmd.startswith("PROMPT "):
                prompt = cmd[7:-1]
                try:
                    line = unicode(raw_input(prompt), encoding)
                except (EOFError, KeyboardInterrupt):
                    break
                pipeout.write(line + "\n")
            elif cmd.startswith("PRINT "):
                print(cmd[6:-1], end="")
            elif cmd.startswith("PRINTLINE "):
                print(cmd[10:-1])
            else:
                print("Client: got unexpected command " + cmd)
                break
    except IOError:
        pass


if __name__ == "__main__":
    run_client(sys.argv[1])
