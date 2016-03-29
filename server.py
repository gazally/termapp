from __future__ import unicode_literals

import appscript
from code import InteractiveConsole
from contextlib import contextmanager
import os
from pipes import quote
import shutil
from StringIO import StringIO
import sys
import tempfile
from threading import Thread
from time import sleep


@contextmanager
def redirect_stds(stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    redirected = stdin, stdout, stderr
    original = sys.stdin, sys.stdout, sys.stderr
    sys.stdin, sys.stdout, sys.stderr = redirected
    yield
    sys.stdin, sys.stdout, sys.stderr = original


class Shell(InteractiveConsole):
    """ Wrapper for the InteractiveConsole that captures its output
    instead of letting it use stdout/stderr. """
    def push(self, line, output):
        """Feed one line of user input to the interactive console,
        and return a flag indicating which prompt to use next """
        with redirect_stds(stdin=os.devnull, stdout=output, stderr=output):
            return InteractiveConsole.push(self, line)


class ClientIO(object):
    """ File Object wrapper that translates output into our simple little
    client-server language """
    def __init__(self, pipe):
        self.pipe = pipe

    @staticmethod
    def guarantee(string):
        return "".join(string.split("\n"))

    def send_prompt(self, prompt):
        self.pipe.write("PROMPT " + self.guarantee(prompt) + "\n")

    def send_lines(self, lines):
        self.pipe.write("PRINTLINE {0}\n".format(len(lines)))
        self.pipe.writelines((self.guarantee(line) + "\n" for line in lines))

    def send_partial_line(self, line):
        self.pipe.write("PRINT " + self.guarantee(line) + "\n")

    def write(self, text):
        lines = []
        while "\n" in text:
            line, text = text.split("\n")
            lines.append(line)
        self.send_lines(lines)
        if text:
            self.send_partial_line(text)
        text = ""


def run_server(prompt, namespace, temp_path):
    """Warning in 20 point bold type: this will delete temp_path!!!

    besides that, do a read-eval-print loop in the context of
    namespace, doing I/O through two named pipes set up in the
    temp_path directory, which will be unlinked along with the pipes
    just as soon as they are opened.
    """
    user_input_name = os.path.join(temp_path, ".up.fifo")
    results_name = os.path.join(temp_path, ".down.fifo")

    if not os.path.exists(user_input_name):
        os.mkfifo(user_input_name)
    if not os.path.exists(results_name):
        os.mkfifo(results_name)

    shell = Shell(namespace)

    p1 = prompt + " >> "
    p2 = prompt + "... "

    try:
        with open(results_name, "w", 0) as pipeout:
            with open(user_input_name, "r", 0) as pipein:
                client = ClientIO(pipeout)
                more_input = False
                while True:
                    client.send_prompt(p2 if more_input else p1)
                    line = pipein.readline()
                    if not line:
                        break
                    more_input = shell.push(line[:-1], client)
    finally:
        shutil.rmtree(temp_path)


def start_shell_thread(prompt, namespace):
    """ Run the python script client.py (which must be in the current
    directory) in a Terminal window. Set its current directory to the
    current directory, and pass as an argument to it the name of a temporary
    directory where it should look for named pipes to communcate with. """
    path = tempfile.mkdtemp()
    cwd = os.getcwd()

    app = appscript.app("Terminal")
    app.do_script("cd {0};python client.py {1};exit".format(quote(cwd),
                                                            quote(path)))

    t = Thread(target=run_server,
               name="console",
               args=(prompt, namespace, path))
    t.setDaemon(True)
    t.start()
    return t


if __name__ == "__main__":
    namespace = locals().copy()
    namespace.update(globals())
    t = start_shell_thread("[" + __file__ + "]", namespace)
    while True:
        if not t.is_alive():
            break
        sleep(1)
