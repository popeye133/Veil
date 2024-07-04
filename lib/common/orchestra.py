"""
This class controls the Veil framework and its operations.
"""

import os
import sys
import readline
import glob
import subprocess
import platform

from lib.common import completer
from lib.common import helpers
from lib.common import messages

# Attempt to import settings.py from /etc/veil/
try:
    sys.path.append("/etc/veil/")
    import settings
except ImportError:
    print("\n [!] ERROR: Unable to import /etc/veil/settings.py. Please run: {}\n".format(os.path.abspath("./config/update-config.py")))
    sys.exit(1)


class Conductor:
    def __init__(self, cli_stuff):
        self.imported_tools = {}
        self.load_tools(cli_stuff)
        self.mainmenu_commands = {
            "list": "List available tools",
            "use": "Use a specific tool",
            "info": "Information on a specific tool",
            "options": "Show Veil configuration",
            "update": "Update Veil",
            "exit": "Completely exit Veil"
        }
        self.command_line_options = cli_stuff

    def command_line_use(self):
        tool_found = False
        for tool_object in self.imported_tools.values():
            if self.command_line_options.tool.lower() == tool_object.cli_name.lower():
                tool_object.cli_menu()
                tool_found = True
                break
        if not tool_found:
            print(helpers.color(' [!] ERROR: Invalid tool name provided!', warning=True))
            sys.exit(1)

    def list_tools(self, show_header=True):
        if show_header:
            messages.title_screen()
            print(helpers.color(' [*] Available Tools:\n'))
        else:
            print("Available Tools:\n")

        for index, tool in enumerate(sorted(self.imported_tools.values(), key=lambda x: x.cli_name), start=1):
            print('\t{})\t{}'.format(index, tool.cli_name))
        print()

    def load_tools(self, command_line_object):
        for tool_file in glob.glob('tools/*/tool.py'):
            if tool_file.endswith(".py") and "__init__" not in tool_file:
                module = helpers.load_module(tool_file)
                if module:
                    self.imported_tools[tool_file] = module.Tools(command_line_object)

    def main_menu(self):
        show_header = True

        try:
            while True:
                comp = completer.VeilMainMenuCompleter(self.mainmenu_commands, self.imported_tools)
                readline.set_completer_delims(' \t\n;')
                readline.parse_and_bind("tab: complete")
                readline.set_completer(comp.complete)

                if show_header:
                    messages.title_screen()
                    print("Main Menu")
                    print("\n\t{} tools loaded\n".format(len(self.imported_tools)))
                    self.list_tools(False)
                    print("Available Commands:\n")
                    for command, description in sorted(self.mainmenu_commands.items()):
                        print("\t{}\t\t{}".format(helpers.color(command), description))
                    print()
                    show_header = False

                main_menu_command = input('Veil>: ').strip()

                if main_menu_command.startswith('use'):
                    if len(main_menu_command.split()) == 1:
                        self.list_tools()
                    elif len(main_menu_command.split()) == 2:
                        tool_choice = main_menu_command.split()[1]
                        if tool_choice.isdigit() and 0 < int(tool_choice) <= len(self.imported_tools):
                            tool_number = 1
                            for tool_object in sorted(self.imported_tools.values(), key=lambda x: x.cli_name):
                                if int(tool_choice) == tool_number:
                                    tool_object.tool_main_menu()
                                tool_number += 1
                            show_header = True
                        else:
                            for tool_object in sorted(self.imported_tools.values(), key=lambda x: x.cli_name):
                                if tool_choice.lower() == tool_object.cli_name.lower():
                                    tool_object.tool_main_menu()
                                    show_header = True
                elif main_menu_command.startswith('list'):
                    self.list_tools()
                elif main_menu_command.startswith('info'):
                    if len(main_menu_command.split()) == 1:
                        show_header = True
                    elif len(main_menu_command.split()) == 2:
                        info_choice = main_menu_command.split()[1]
                        if info_choice.isdigit() and 0 < int(info_choice) <= len(self.imported_tools):
                            for index, tool_object in enumerate(sorted(self.imported_tools.values(), key=lambda x: x.cli_name), start=1):
                                if int(info_choice) == index:
                                    print()
                                    print(helpers.color(tool_object.cli_name) + " => " + tool_object.description)
                                    print()
                                    break
                        else:
                            for tool_object in sorted(self.imported_tools.values(), key=lambda x: x.cli_name):
                                if main_menu_command.split()[1].lower() == tool_object.cli_name.lower():
                                    print()
                                    print(helpers.color(tool_object.cli_name) + " => " + tool_object.description)
                                    print()
                                    break
                    else:
                        show_header = True
                elif main_menu_command.startswith('option'):
                    self.options_veil()
                elif main_menu_command.startswith('config'):
                    self.config_veil()
                elif main_menu_command.startswith('setup'):
                    self.setup_veil()
                elif main_menu_command.startswith('update'):
                    self.update_veil()
                elif main_menu_command.startswith('exit') or main_menu_command.startswith('quit'):
                    sys.exit()

        except KeyboardInterrupt:
            print("\n\n" + helpers.color("^C.   Quitting...", warning=True))
            sys.exit()

    def options_veil(self):
        print(" [i] Veil configuration file: /etc/veil/settings.py")
        for attr_name in dir(settings):
            if not attr_name.startswith('_'):
                print(" [i] {}: {}".format(attr_name, getattr(settings, attr_name)))
        input('\n\nOptions shown. Press enter to continue')

    def update_veil(self):
        if settings.OPERATING_SYSTEM == "Kali":
            self.run_command(['apt-get', 'update'])
            self.run_command(['apt-get', '-y', 'install', 'veil'])
        else:
            self.run_command(['git', 'pull'])
        input('\n\nVeil has checked for updates, press enter to continue')

    def setup_veil(self):
        setup_script_path = "/usr/share/veil/config/setup.sh" if settings.OPERATING_SYSTEM == "Kali" else "./config/setup.sh"
        self.run_script(setup_script_path, ['-f', '-s'], "Veil setup.sh")

    def config_veil(self):
        config_script_path = "/usr/share/veil/config/update-config.py" if settings.OPERATING_SYSTEM == "Kali" else "./config/update-config.py"
        self.run_script(config_script_path, [], "Veil update-config.py")

    def run_command(self, command):
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print("\n [!] ERROR: Command '{}' failed with error code {}. Exiting...\n".format(' '.join(command), e.returncode))
            sys.exit(1)

    def run_script(self, script_path, args, script_name):
        if os.path.exists(script_path):
            try:
                subprocess.run([script_path] + args, check=True)
            except subprocess.CalledProcessError as e:
                print("\n [!] ERROR: {} script failed with error code {}. Exiting...\n".format(script_name, e.returncode))
                sys.exit(1)
        else:
            print("\n [!] ERROR: {} not found.\n".format(script_path))
            sys.exit(1)

