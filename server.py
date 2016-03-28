from __future__ import unicode_literals

from code import InteractiveConsole
from contextlib import contextmanager
import os
import shutil
from StringIO import StringIO
from subprocess import Popen
import sys
import tempfile
from threading import Thread
from time import sleep

user_input_name = '.up.fifo'
results_name = '.down.fifo'

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
    def __init__(self, *args, **kwargs):
        self.output = StringIO()
        InteractiveConsole.__init__(self, *args, **kwargs)

    def process(self, line):
        """Feed one line of user input to the interactive console,
        and return a flag indicating which prompt to use next and
        a list of the lines of output returned by the console """
        with redirect_stds(stdout=self.output, stderr=self.output):
            more = InteractiveConsole.push(self, line)

        results = self.output.getvalue().split("\n")
        if results and results[-1] == "":
            results.pop()
            
        self.output.seek(0)
        self.output.truncate()
        return more, results


def run_server(prompt, namespace, temp_path):
    """Warning in 20 point bold type: this will delete temp_path!!! 

    besides that, do a read-eval-print loop in the context of
    namespace, doing I/O through two named pipes set up in the
    temp_path directory, which will be unlinked along with the pipes
    just as soon as they are opened.
    """
    
    def send_prompt(prompt):
        pipeout.write("PROMPT {0}\n".format(prompt))

    def send_lines(lines):
        pipeout.write("PRINT {0}\n".format(len(lines)))
        pipeout.writelines((line + "\n" for line in lines))

    user_input_name = os.path.join(temp_path, ".up.fifo")
    results_name = os.path.join(temp_path, ".down.fifo")
    
    if not os.path.exists(user_input_name):
        os.mkfifo(user_input_name)
    if not os.path.exists(results_name):
        os.mkfifo(results_name)
        
    shell = Shell(namespace)

    with open(results_name, "w", 0) as pipeout:
        with open(user_input_name, "r", 0) as pipein:
            shutil.rmtree(temp_path)

            more_input = False
            while True:
                send_prompt(prompt + "... " if more_input else prompt + " >> ")
                line = pipein.readline()
                if not line:
                    break

                more_input, lines = shell.process(line[:-1])
                send_lines(lines)


def start_shell_thread(namespace):
    """ Run the python script client.py (which must be in the current 
    directory) in a Terminal window. Set its current directory to the 
    current directory, and pass as an argument to it the name of a temporary
    directory where it should look for named pipes to communcate with. """
    path = tempfile.mkdtemp()
    cwd = os.getcwd()
    
    Popen(
        ["/usr/bin/osascript",
         "-e", 'tell app "Terminal"',
         "-e", 'do script "cd {0};python client.py {1};exit"'.format(cwd,
                                                                     path),
         "-e", 'end tell'
        ])

    t = Thread(target=run_server,
               name="Interpreter",
               args=("OmniLink", namespace, path))
    t.setDaemon(True)
    t.start()
    return t


if __name__ == "__main__":
    namespace = globals().copy()
    namespace.update(locals())
    t = start_shell_thread(namespace)
    while True:
        if not t.is_alive():
            break
        sleep(1)
        
