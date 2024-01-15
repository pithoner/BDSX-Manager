import subprocess
import threading
import PySimpleGUI as sg
import re
import time
import os
import configparser
import json
import socket
import sys


def script_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(os.path.abspath(__file__))
    else:
        return os.getcwd()

script_dir = script_directory()
server_dir = os.path.join(script_dir, "bdsx.bat")
bedrock_server_dir = os.path.join(script_dir, 'bedrock_server')
permissions_dir = os.path.join(bedrock_server_dir, 'permissions.json')

version = '1.1.2'
process = None
config_file = 'config.ini'

if not os.path.exists(config_file):
    config = configparser.ConfigParser()
    config['SERVER'] = {'RestartInterval': '6',
                        'Restartenabled': '0',
                        'HideTelemetryMsg': '0',
                        'Theme': 'DefaultNoMoreNagging'
                        }
    with open(config_file, 'w') as f:
        config.write(f)

config = configparser.ConfigParser()
config.read(config_file)

default_config = {'RestartInterval': '6',
                  'Restartenabled': '0',
                  'HideTelemetryMsg': '0',
                  'Theme': 'DefaultNoMoreNagging'
                  }

for section in config.sections():
    for key, value in default_config.items():
        if key not in config[section]:
            config[section][key] = value

# Save the updated config
with open(config_file, 'w') as f:
    config.write(f)

hide_telemetry_msg = config['SERVER'].getboolean('HideTelemetryMsg')
restart_enabled = config['SERVER'].getboolean('Restartenabled')
app_theme = config['SERVER']['Theme']

if app_theme == 'DefaultNoMoreNagging':
    app_theme_format = 'Light'
elif app_theme == 'DarkGray13':
    app_theme_format = 'Dark'
elif app_theme == 'DarkBlue3':
    app_theme_format = 'Gray'
elif app_theme == 'PythonPlus':
    app_theme_format = 'Blue'

lock = threading.Lock()

JOIN_PATTERN = re.compile(r"Player connected: (.*?), xuid: ?(\d*)")
SPAWN_PATTERN = re.compile(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:\d{3} INFO\] Player Spawned: (.*?) xuid: ?(\d*)")
LEAVE_PATTERN = re.compile(r"Player disconnected: (.*?), xuid: ?(\d*)")

player_list = []
player_count = 0

restart_interval = config['SERVER']['RestartInterval']
restart_seconds = 3600

stop_flag = False

server_status = "None"

def run_server():
    global process
    global player_list
    global player_count
    global timer_thread
    global server_status

    restart_enabled = config['SERVER'].getboolean('Restartenabled')

    with lock:
        if process is None:
            process = subprocess.Popen([server_dir], stdout=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True, shell=True)
    output = ""

    while True:
        if process is not None:
            server_output = process.stdout.readline()

            if server_output.strip() == '' and process.poll() is not None:
                with lock:
                    process = None
                break

            if server_output.strip():
                server_output = re.sub(r'\033\[\d{1,2}m', '', server_output)
                server_output = server_output.strip()

                if 'TELEMETRY MESSAGE' in server_output:
                    hide_telemetry_msg = config['SERVER'].getboolean('HideTelemetryMsg')
                    if hide_telemetry_msg:
                        for _ in range(6):
                            process.stdout.readline().strip()
                        continue  # Skip the telemetry message

                output += server_output + '\n'
                window['output'].update(output)

                match = JOIN_PATTERN.search(server_output)
                if match:
                    player_name = match.group(1)
                    xuid = match.group(2)
                    level = "Member"  #TODO make this be the default permission level for server.properties
                    with open(permissions_dir) as f:
                        permissions = json.load(f)
                    for permission in permissions:
                        if permission['xuid'] == xuid:
                            level = permission['permission'].capitalize()
                            break
                    player_list.append([player_name, xuid, level])
                    window['player_list'].update(values=player_list)
                    player_count += 1
                    window['-ONLINE_PLAYERS-'].update(player_count)

                match = LEAVE_PATTERN.search(server_output)
                if match:
                    player_name = match.group(1)
                    player_list = [p for p in player_list if p[0] != player_name]
                    window['player_list'].update(values=player_list)
                    player_count -= 1
                    window['-ONLINE_PLAYERS-'].update(player_count)

            if 'Level Name' in server_output:
                match = re.search(r'Level Name: (.+)', server_output)
                if match:
                    level_name = match.group(1)
                    window['-INFO_LEVELNAME-'].update(level_name)
            if 'Game mode' in server_output:
                match = re.search(r'Game mode: \d+ (\w+)', server_output)
                if match:
                    game_mode = match.group(1)
                    window['-INFO_GAMEMODE-'].update(game_mode)
            if 'Difficulty' in server_output:
                match = re.search(r'Difficulty: \d+ (\w+)', server_output)
                if match:
                    difficulty = match.group(1).lower()
                    window['-INFO_DIFFICULTY-'].update(difficulty.title())
            if 'Version' in server_output:
                match = re.search(r'Version: (.+)', server_output)
                if match:
                    version = match.group(1)
                    window['-INFO_VERSION-'].update(version)
            if 'port' in server_output:
                match = re.search(r'IPv4 supported, port: (\d+): Used for gameplay', server_output)
                if match:
                    port_number = match.group(1)
                    window['-INFO_PORT-'].update(port_number)
                    ip_address = socket.gethostbyname(socket.gethostname())
                    window['-INFO_ADDRESS-'].update(ip_address)

            if 'Starting Server' in server_output:
                window['-SERVER_STATE-'].update('Starting')
                server_status = 'Starting'
            if 'Server started' in server_output:
                window['-SERVER_STATE-'].update('Running')
                server_status = 'Running'
                if restart_enabled:
                    stop_event = threading.Event()
                    auto_restart_thread = threading.Thread(target=auto_restart, args=(), daemon=True)
                    auto_restart_thread.start()

                timer_thread = threading.Thread(target=update_uptime, args=(), daemon=True)
                timer_thread.start()

            elif 'Server stop requested.' in server_output:
                server_status = 'Stopping'
                window['-SERVER_STATE-'].update('Stopping')
            elif 'Quit correctly' in server_output:
                window['-SERVER_STATE-'].update('Stopping')
                server_status = 'Stopping'

            elif '[BDSX] bedrockServer closed' in server_output:
                window['-SERVER_STATE-'].update('Stopped')
                server_status = 'Stopped'

            elif "Fail" in server_output or "Error" in server_output or "error" in server_output or "fail" in server_output or "exit" in server_output or "Exit" in server_output or "ERROR" in server_output:
                window['-SERVER_STATE-'].update('Error')
        else:
            break


def start_server():
    window.Element('output').Update('')
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

stop_restart_thread = threading.Event()

def restart_server():
    global stop_event
    stop_server()
    stop_event.set()
    while not server_status == 'Stopped':
        #print('Waiting for server to stop')
        time.sleep(5) #TODO pls fix this someone, the delay is 3 seconds to ensure it stops completely, else it throws an attribute error about process.
                      #This only happens when running bdsx.bat, when running just the regular bedrock_server.exe it does not happened, so idk what causes the issue but if you know pls fix

    #print('Restart request sent')
    window.write_event_value('-SERVER_RESTARTABLE-', None)


def stop_server():
    global stop_event
    stop_event.set()
    command = "stop"
    process.stdin.write(command + "\n")
    process.stdin.flush()
    #print('stopping server')

def stop_server_force(type):
    global stop_event
    stop_event.set()
    command = "stop"
    process.stdin.write(command + "\n")
    process.stdin.flush()
    while not server_status == 'Stopped':
        time.sleep(1)
    if type == 'Stop':
        window.write_event_value('-SERVER_STOPPED-', None)
    elif type == 'Restart':
        window.write_event_value('-SERVER_STOPPED_R-', None)

def run_command(server_command):
    #command = values['input']
    process.stdin.write(server_command + "\n")
    process.stdin.flush()

def update_permissions_thread():
    time.sleep(1)
    row_number = values['player_list'][0]
    xuid = player_list[row_number][1]
    # Update the player level
    level = "Member"  #TODO make this be the default permission level for server.properties
    with open(permissions_dir) as f:
        permissions = json.load(f)
    for permission in permissions:
        if permission['xuid'] == xuid:
            level = permission['permission'].capitalize()
            break
    player_list[row_number][2] = level
    window['player_list'].update(values=player_list)  # update player list with list of dictionaries

def update_permissions():
    t = threading.Thread(target=update_permissions_thread)
    t.start()

def op_player():
    if values['player_list']:
        row_number = values['player_list'][0]
        player_name = player_list[row_number][0]
        if player_name:
            command = f'op "{player_name}"'
            #print(command)
            process.stdin.write(command + "\n")
            process.stdin.flush()
            update_permissions()

def deop_player():
    if values['player_list']:
        row_number = values['player_list'][0]
        player_name = player_list[row_number][0]
        if player_name:
            command = f'deop "{player_name}"'
            #print(command)
            process.stdin.write(command + "\n")
            process.stdin.flush()
            update_permissions()

def kick_player():
    if values['player_list']:
        row_number = values['player_list'][0]
        player_name = player_list[row_number][0]
        if player_name:
            command = f'kick "{player_name}"'
            process.stdin.write(command + "\n")
            process.stdin.flush()

def auto_restart():
    global server_status
    global stop_event
    while not stop_event.is_set():
        restart_enabled = config['SERVER'].getboolean('Restartenabled')
        if restart_enabled:
            restart_interval = int(config['SERVER']['RestartInterval'])

            for remaining_time in range(restart_interval * 60 * 60, 0, -1):
                if stop_event.is_set():
                    break  # exit the loop if the stop event is set

                hours, remainder = divmod(remaining_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                window['-RESTART_COUNTDOWN-'].update(countdown_str)

                time.sleep(1)

            if server_status == 'Running':
                restart_server()
                player_list = []  # Remove all players
                window['player_list'].update(values=player_list)
                player_count = 0
                window['-ONLINE_PLAYERS-'].update(player_count)
                update_info()
                break
            else:
                break
        else:
            break

def update_uptime():
    global stop_event
    start_time = time.time()
    while not stop_event.is_set():
        elapsed_time = time.time() - start_time

        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
        window['-INFO_UPTIME-'].update(uptime)
        time.sleep(1)

def update_info():
    window['-INFO_LEVELNAME-'].update('- - -')
    window['-INFO_GAMEMODE-'].update('- - -')
    window['-INFO_DIFFICULTY-'].update('- - -')
    window['-INFO_VERSION-'].update('- - -')
    window['-INFO_ADDRESS-'].update('- - -')
    window['-INFO_PORT-'].update('- - -')
    window['-INFO_UPTIME-'].update('—:—:—')
    window['-RESTART_COUNTDOWN-'].update('—:—:—')

sg.theme(app_theme)

#DefaultNoMoreNagging
#DarkGray13
#DarkBlue3
#PythonPlus

themes = ['Light', 'Dark', 'Gray', 'Blue']

headings = ['Name', 'Xuid', 'Level']

operations_column = [
    [sg.Text("Server Status:", pad=(0,0)), sg.Text("Stopped", key="-SERVER_STATE-", size=(6,1)), sg.Text('Uptime:', size=(8,1), justification='right'), sg.Text('—:—:—', key='-INFO_UPTIME-', size=(15,1))],
    [sg.Button('Start', button_color="green", size = (10,0)),
     sg.Button('Restart', button_color="#DBA800", size = (10,0)),
     sg.Button('Stop', button_color="red", size = (10,0))],
    [sg.Button('Index.ts', size = (16,0)), sg.Button('Server.properties', size = (16,0))],
    [sg.Button('BDSX Folder', size = (16,0)), sg.Button(' ', size = (16,0))],
    [sg.Text('—'*22, pad = (0,0), justification = "center")],

    [sg.Text("Auto Restart System:"), sg.Checkbox("Enabled", default=restart_enabled, enable_events=True, key="-RESTART_ENABLED-")],
    [sg.Text("Next Restart:"), sg.Text("—:—:—", key="-RESTART_COUNTDOWN-")],
    [sg.Text("Restart Interval:")],
    [sg.Radio("1 hr", "RADIO1", key="-1", enable_events=True),
     sg.Radio("2 hrs", "RADIO1", key="-2", enable_events=True),
     sg.Radio("6 hrs", "RADIO1", default=True, key="-6", enable_events=True),
     sg.Radio("12 hrs", "RADIO1", key="-12", enable_events=True)],


    [sg.Text('—'*22, pad = (0,0), justification = "center")],
    [sg.Text("Online Players:"), sg.Text("0", key=("-ONLINE_PLAYERS-"))],
    [sg.Table(headings=headings, values=player_list, enable_events=True, justification='center', auto_size_columns=False, def_col_width=10, num_rows=7, key='player_list')],
    [sg.Button('OP', size = (10,0)),
     sg.Button('DEOP', size = (10,0)),
     sg.Button('Kick', size = (10,0))],
    [sg.Button("Test", key=("-TEST-"), visible=False)],

    [sg.Text('—'*22, pad = (0,0), justification = "center")],
    [sg.Combo(values=themes, readonly=True, size=(16,1), key='-CHANGE_THEME-', default_value = app_theme_format, tooltip='Change the theme of the app, requires restart', enable_events = True),
     sg.Text('App Theme', size=(13,1), tooltip='Change the theme of the app, requires restart'),
     sg.Button('⟳', size=(2,1), key='-RESTART_APP-', tooltip='Restart BDSX Manager')],
    [sg.Checkbox("Hide Telemetry Message", default=hide_telemetry_msg, enable_events=True, key="-HIDE_TELEMETRY_MSG-", tooltip='Hides the telemetry message without having to modify server.properties')],
    [sg.Text('Version: '+version, font=('Helvetica', 8), size=(50,1), pad=(5,14), justification='right')]
    ]

output_column = [
    [sg.Text('Console Output:')],
    [sg.Multiline(size=(120, 25), key='output', autoscroll=True, disabled=True)],
    [sg.InputText(size=(102,1), key='input', pad=(6,5)), sg.Button('Run', size=(8,1)), sg.Button('Clear', size=(5,1), key='-CLEAR-')],
    [sg.Text('Server Information', font=('Helvetica', 14), justification='Center', pad=(0,6), size=(25,0)), ],
    [sg.Text('Level Name:', size=(10,1), justification='left'), sg.Text('- - -', key='-INFO_LEVELNAME-', size=(15,1)), sg.Text('Server Version:', size=(12,1), justification='left'), sg.Text('- - -', key='-INFO_VERSION-', size=(15,1))],
    [sg.Text('Gamemode:', size=(10,1), justification='left'), sg.Text('- - -', key='-INFO_GAMEMODE-', size=(15,1)), sg.Text('Address:', size=(12,1), justification='left'), sg.Text('- - -', key='-INFO_ADDRESS-', size=(15,1))],
    [sg.Text('Difficulty:', size=(10,1), justification='left'), sg.Text('- - -', key='-INFO_DIFFICULTY-', size=(15,1)), sg.Text('Port:', size=(12,1), justification='left'), sg.Text('- - -', key='-INFO_PORT-', size=(15,1))],
    ]


layout = [
    [sg.Column(output_column, justification = "left", vertical_alignment = ("top")),
     sg.Column(operations_column, justification = "left", vertical_alignment = ("top"))],
    ]


window = sg.Window('BDSX Manager', layout, size = (1200,610), finalize=True, enable_close_attempted_event=True)

restart_interval = config['SERVER']['RestartInterval']
if restart_interval == '1':
    window['-1'].update(value=True)
elif restart_interval == '2':
    window['-2'].update(value=True)
elif restart_interval == '6':
    window['-6'].update(value=True)
elif restart_interval == '12':
    window['-12'].update(value=True)



while True:
    # read the window's events
    event, values = window.read()
    print(event)

    if event == 'Start':
    # Check if the process is already running
        if process is not None:
            sg.popup('Server is already running')
        else:
            stop_flag = False
            start_server()
            stop_event = threading.Event()


    if event == 'Restart':
        if process is None:
            sg.popup('Server is not running')
        else:
            restart_thread = threading.Thread(target=restart_server, daemon=True)
            restart_thread.start()

            #if restart_enabled == 1:
                #stop_flag = False

            player_list = []  # remove all players
            window['player_list'].update(values=player_list)
            player_count = 0
            window['-ONLINE_PLAYERS-'].update(player_count)
            stop_event.set()
            update_info()

    if event == '-SERVER_RESTARTABLE-':
        stop_flag = False
        start_server()
        stop_event = threading.Event()

    if event == 'Stop':
        if process is None:
            sg.popup('Server is not running')
        else:
            stop_server()
            player_list = []  # remove all players
            window['player_list'].update(values=player_list)
            player_count = 0
            window['-ONLINE_PLAYERS-'].update(player_count)
            stop_event.set()
            update_info()

    if event == 'Run':
        server_command = values['input'].strip()
        if server_command:
            if process is None:
                sg.popup('Server is not running')
            else:
                run_command(server_command)

    if event == '-CLEAR-':
        window['input'].update('')

    if event == 'OP':
        op_player()

    if event == 'DEOP':
        deop_player()

    if event == 'Kick':
        kick_player()

    elif event == "Index.ts":
        file_path = os.path.join(os.getcwd(), "Index.ts")
        subprocess.run(["start", "", file_path], shell=True)

    elif event == "Server.properties":
        file_path = os.path.join(os.getcwd(), "bedrock_server", "Server.properties")
        subprocess.run(["start", "", file_path], shell=True)

    if event == 'BDSX Folder':
        current_folder = os.getcwd()  # Get the current working directory
        subprocess.Popen(f'explorer "{current_folder}"')  # Open the folder using the default file explorer

    if event == "-TEST-":
        print(server_dir)
        
    if event == '-RESTART_APP-':
        if process is not None:
            if sg.popup_ok_cancel('Are you sure you want to stop the server', title='Confirmation') == 'OK':
                stop_server()
                force_close_thread = threading.Thread(target=stop_server_force, args=('Restart',), daemon=True)
                force_close_thread.start()
        else:
            window.close()
            python = sys.executable
            os.execl(python, python, *sys.argv)
    if event == '-SERVER_STOPPED_R-':
        window.close()
        python = sys.executable
        os.execl(python, python, *sys.argv)

    if event == '-1' or event == '-2' or event == '-6' or event == '-12':
        config['SERVER']['RestartInterval'] = event[1:]
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    if event == '-RESTART_ENABLED-':
        if values['-RESTART_ENABLED-']:
            # Checkbox is checked
            config['SERVER']['Restartenabled'] = '1'
        else:
            # Checkbox is unchecked
            config['SERVER']['Restartenabled'] = '0'
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    if event == '-HIDE_TELEMETRY_MSG-':
        if values['-HIDE_TELEMETRY_MSG-']:
            config['SERVER']['HideTelemetryMsg'] = '1'
        else:
            config['SERVER']['HideTelemetryMsg'] = '0'
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    if event == '-CHANGE_THEME-':
        theme = values['-CHANGE_THEME-']
        if theme == 'Light':
            theme = 'DefaultNoMoreNagging'
        elif theme == 'Dark':
            theme = 'DarkGray13'
        elif theme == 'Gray':
            theme = 'DarkBlue3'
        elif theme == 'Blue':
            theme = 'PythonPlus'

        if theme:
            config['SERVER']['Theme'] = theme
            with open('config.ini', 'w') as configfile:
                config.write(configfile)

    # old closing method, doesnt work with bdsx for some reason, bedrock_server starts using more and more ram till ur pc crashes
    #if event in (None,):
    #    if process is not None:
    #        stop_server()
    #        stop_event.set()
    #        stop_flag = True
    #
    #        break
    #    else:
    #        break

    if event == sg.WIN_X_EVENT:
        if process is not None:
            if sg.popup_ok_cancel('Are you sure you want to stop the server', title='Confirmation') == 'OK':
                stop_server()
                force_close_thread = threading.Thread(target=stop_server_force, args=('Stop',), daemon=True)
                force_close_thread.start()
        else:
            break
    if event == '-SERVER_STOPPED-':
        break

window.close()