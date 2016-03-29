#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals

import os
import readline
import sys


def run_client(path):
    pipein = open(os.path.join(path, ".down.fifo"), "r", 0)
    pipeout = open(os.path.join(path, ".up.fifo"), "w", 0)

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
            elif cmd.startswith("PROMPT "):
                prompt = cmd[7:-1]
                try:
                    line = raw_input(prompt)
                except (EOFError, KeyboardInterrupt):
                    break
                pipeout.write(line + "\n")
            elif cmd.startswith("PRINT "):
                text = cmd[6:-1]
                print(text, end="")
            elif cmd.startswith("PRINTLINE "):
                count = int(cmd[10:-1])
                for i in range(count):
                    print(readline()[:-1])
            else:
                print("Client: got unexpected command " + cmd)
                break
    except IOError:
        pass


if __name__ == "__main__":
    run_client(sys.argv[1])
