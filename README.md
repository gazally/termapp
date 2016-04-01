## termapp-interaction 

A client-server pair to let a process communicate with the user
through a Terminal.app window. Works on Python 2.6.

### Usage
To try it out, create a Terminal.app window and type:

```sh
python termapp_server.py
```

This will bring up a new window in Terminal.app which appears to be
running the Python interpreter. What it is actually running is a
client process that is communicating with a Python interpreter object
(code.InteractiveConsole) inside termapp_server.py.

### Usage within an Indigo plugin

Here's how to hook it up to a menu command. You will need to have
termapp_server and termapp_client in the current working directory
(which Indigo sets to your Server Plugin directory when it launches
the plugin). The resulting Python shell will have access to the
namespace in the module you call it from plus the self varable.
    
```py
from termapp_server import start_shell_thread

# somewhere inside your plugin:

    def startInteractiveInterpreter(self):
        """ Called by the Indigo UI for the Start Interactive Interpreter
        menu item.
        """
        namespace = globals().copy()
        namespace.update(locals())
        start_shell_thread(namespace, "Indigo Plugin")
```

Once you do this you will have a Python shell with access to your
plugin's internal data structures and plugin module globals. This is
not thread-safe, or any kind of safe.

Or if you want to do some other kind of user interaction, make a function that
takes a line of input and returns a boolean, True to use a "..." prompt next
and False for a " >>" prompt. When your function is called sys.stdout and 
sys.stderr will be hooked up to the Terminal.app client, so you can just use
print if you want:

```py
from termapp_server import start_interaction_thread

# somewhere inside your plugin:

    def chat(self, line):
        if line:
            print("Hey thanks for telling me " + line)
            return False
        else:
            return True
    
    def startLameChatbot(self):
        """ Called by the Indigo UI for the Start Really Lame Chatbot menu item.
        """
        start_interaction_thread(self.chat, "chatbot")
```

The threads created are daemon threads so they will not block a plugin
from exiting. The start methods return the thread objects created if
you want to keep track of them. If the user uses ^D or closes the
Terminal window the plugin-side thread will terminate.
