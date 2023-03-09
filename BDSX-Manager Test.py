import subprocess
import threading
import PySimpleGUI as sg
import re
import time
import os
import configparser

# get the directory path of the current script
dir_path = os.path.dirname(__file__)

# construct the path to the bat file in the same directory
bat_file = os.path.join(dir_path, 'bdsx', 'bdsx.bat')

bat_file = (r'C:\MCBDSX\bdsx\bdsx.bat')

process = None

config_file = 'config.ini'

# check if config file exists
if not os.path.exists(config_file):
    # create new config file with default values
    config = configparser.ConfigParser()
    config['SERVER'] = {'RestartInterval': '6 hr'}
    config['SERVER'] = {'Restartenabled': '0'}
    with open(config_file, 'w') as f:
        config.write(f)

# read config file
config = configparser.ConfigParser()
config.read(config_file)

lock = threading.Lock()

# regex pattern to match player join event
#JOIN_PATTERN = re.compile(r"Connection: ([^\s]+)> Ip=(\d+\.\d+\.\d+\.\d+)\|\d+, Xuid=(\d+),")

# regex pattern to match player join event
JOIN_PATTERN = re.compile(r"Player connected: ([^\s]+), xuid: (\d+)")

# regex pattern to match player leave event
LEAVE_PATTERN = re.compile(r"Player disconnected: ([^\s]+), xuid: (\d+)")

player_list = []
player_count = 0

restart_interval = config['SERVER'].get('RestartInterval', '6 hr')

def run_bat_file_restart():
    remaining_time = int(restart_interval) * 3600
    print(remaining_time)    
    global process
    global player_list
    global player_count
    time.sleep(7)
    while remaining_time > 0:
        time.sleep(1)
        remaining_time -= 1
        hours, rem = divmod(remaining_time, 3600)
        minutes, seconds = divmod(rem, 60)
        countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        window['-COUNTDOWN-'].update(countdown_str)
    
    window['-COUNTDOWN-'].update("Restarting")
    print(remaining_time)
    print("Restarting")
    stop_server_restart()
    time.sleep(8)
    with lock:
        if process is None:
            process = subprocess.Popen([bat_file], stdout=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True, shell=True)
    output = ""
    while True:
        line = process.stdout.readline()
        
        if line == '' and process.poll() is not None:
            with lock:
                process = None
            break
        if line:
            line = re.sub(r'\033\[\d{1,2}m', '', line)
            output += line
            window['output'].update(output.strip())

            # search for player join event
            match = JOIN_PATTERN.search(line)
            if match:
                player_name = match.group(1)
                player_list.append(player_name)  # append player name only
                window['player_list'].update(values=player_list)
                player_count += 1  # increment player count
                window['-ONLINE_PLAYERS-'].update(f"Players: {player_count}")  # update player count display

            # search for player leave event
            match = LEAVE_PATTERN.search(line)
            if match:
                player_name = match.group(1)
                player_list = [p for p in player_list if p != player_name]  # remove player by name only
                window['player_list'].update(values=player_list)
                player_count -= 1  # decrement player count
                window['-ONLINE_PLAYERS-'].update(f"Players: {player_count}")  # update player count display

            # update server status
            if '[BDSX] bedrockServer is launching...' in line:
                window['-SERVER_STATE-'].update('Starting')
            elif 'Server started.' in line:
                window['-SERVER_STATE-'].update('Running')
                remaining_time = restart_interval * 60
            elif 'Server stop requested.' in line:
                window['-SERVER_STATE-'].update('Stopping')
            elif '[BDSX] bedrockServer closed' in line:
                window['-SERVER_STATE-'].update('Stopped')
            elif "Fail" in line or "Error" in line or "error" in line or "fail" in line or "exit" in line or "Exit" in line or "ERROR" in line:
                window['-SERVER_STATE-'].update('Error')



def run_bat_file():
    global process
    global player_list
    global player_count
    with lock:
        if process is None:
            process = subprocess.Popen([bat_file], stdout=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True, shell=True)
    output = ""
    while True:
        line = process.stdout.readline()
        
        if line == '' and process.poll() is not None:
            with lock:
                process = None
            break
        if line:
            line = re.sub(r'\033\[\d{1,2}m', '', line)
            output += line
            window['output'].update(output.strip())

            # search for player join event
            match = JOIN_PATTERN.search(line)
            if match:
                player_name = match.group(1)
                player_list.append(player_name)  # append player name only
                window['player_list'].update(values=player_list)
                player_count += 1  # increment player count
                window['-ONLINE_PLAYERS-'].update(f"Players: {player_count}")  # update player count display

            # search for player leave event
            match = LEAVE_PATTERN.search(line)
            if match:
                player_name = match.group(1)
                player_list = [p for p in player_list if p != player_name]  # remove player by name only
                window['player_list'].update(values=player_list)
                player_count -= 1  # decrement player count
                window['-ONLINE_PLAYERS-'].update(f"Players: {player_count}")  # update player count display

            # update server status
            if '[BDSX] bedrockServer is launching...' in line:
                window['-SERVER_STATE-'].update('Starting')
            elif 'Server started.' in line:
                window['-SERVER_STATE-'].update('Running')
                remaining_time = restart_interval * 60
            elif 'Server stop requested.' in line:
                window['-SERVER_STATE-'].update('Stopping')
            elif '[BDSX] bedrockServer closed' in line:
                window['-SERVER_STATE-'].update('Stopped')
            elif "Fail" in line or "Error" in line or "error" in line or "fail" in line or "exit" in line or "Exit" in line or "ERROR" in line:
                window['-SERVER_STATE-'].update('Error')


def run_bat_file_delayed():
    global process
    global player_list
    global player_count
    time.sleep(5)
    with lock:
        if process is None:
            process = subprocess.Popen([bat_file], stdout=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True, shell=True)
    output = ""
    while True:
        line = process.stdout.readline()
        
        if line == '' and process.poll() is not None:
            with lock:
                process = None
            break
        if line:
            line = re.sub(r'\033\[\d{1,2}m', '', line)
            output += line
            window['output'].update(output.strip())

            # search for player join event
            match = JOIN_PATTERN.search(line)
            if match:
                player_name = match.group(1)
                player_list.append(player_name)  # append player name only
                window['player_list'].update(values=player_list)
                player_count += 1  # increment player count
                window['-ONLINE_PLAYERS-'].update(f"Players: {player_count}")  # update player count display

            # search for player leave event
            match = LEAVE_PATTERN.search(line)
            if match:
                player_name = match.group(1)
                player_list = [p for p in player_list if p != player_name]  # remove player by name only
                window['player_list'].update(values=player_list)
                player_count -= 1  # decrement player count
                window['-ONLINE_PLAYERS-'].update(f"Players: {player_count}")  # update player count display

            # update server status
            if '[BDSX] bedrockServer is launching...' in line:
                window['-SERVER_STATE-'].update('Starting')
            elif 'Server started.' in line:
                window['-SERVER_STATE-'].update('Running')
                remaining_time = restart_interval * 60
            elif 'Server stop requested.' in line:
                window['-SERVER_STATE-'].update('Stopping')
            elif '[BDSX] bedrockServer closed' in line:
                window['-SERVER_STATE-'].update('Stopped')
            elif "Fail" in line or "Error" in line or "error" in line or "fail" in line or "exit" in line or "Exit" in line or "ERROR" in line:
                window['-SERVER_STATE-'].update('Error')


def start_server_delayed():
    window.Element('output').Update('')
    thread = threading.Thread(target=run_bat_file_delayed, daemon=True)
    thread.start()

def start_server():
    window.Element('output').Update('')
    thread = threading.Thread(target=run_bat_file, daemon=True)
    thread.start()

def stop_server():
    command = ("stop")
    process.stdin.write(command + "\n")
    process.stdin.flush()

def stop_server_restart():
    command = ("stop")
    process.stdin.write(command + "\n")
    process.stdin.flush()
    start_server_restart()

def restart_server():
    global process
    if process is not None:
        stop_server()
        start_server_delayed()
    else:
        sg.popup('Server is not running')

def start_server_restart():
    window.Element('output').Update('')
    thread = threading.Thread(target=run_bat_file_restart, daemon=True)
    thread.start()




def run_command(values):
    command = values['input']
    process.stdin.write(command + "\n")
    process.stdin.flush()

def op_player():
    selected = values['player_list']
    if selected:
        player_name = selected[0]
        command = f"op {player_name}"
        print(command)
        process.stdin.write(command + "\n")
        process.stdin.flush()

def deop_player():
    selected = values['player_list']
    if selected:
        player_name = selected[0]
        command = f"deop {player_name}"
        print(command)
        process.stdin.write(command + "\n")
        process.stdin.flush()

def kick_player():
    selected = values['player_list']
    if selected:
        player_name = selected[0]
        command = f"kick {player_name}"
        print(command)
        process.stdin.write(command + "\n")
        process.stdin.flush()
# create the GUI layout



operations_column = [
    [sg.Text("Server Status:", pad=(0,0)), sg.Text("Stopped", key="-SERVER_STATE-")],
    [sg.Button('Start', button_color="green", size = (10,0)), 
     sg.Button('Restart', button_color="#DBA800", size = (10,0)), 
     sg.Button('Stop', button_color="red", size = (10,0))],
    [sg.Button('Index.ts', size = (16,0)), sg.Button('Server.properties', size = (16,0))], 
    [sg.Button('BDSX Folder', size = (16,0)), sg.Button(' ', size = (16,0))], 
    [sg.Text('—'*22, pad = (0,0), justification = "center")],
    
    [sg.Text("Auto Restart System:"), sg.Checkbox("Enabled", enable_events=True, key="-RESTART_ENABLED-")],
    [sg.Text("Next Restart:"), sg.Text("- -", key="-COUNTDOWN-")],
    [sg.Text("Restart Interval:")],
    [sg.Radio("1 hr", "RADIO1", key="-1", enable_events=True), 
     sg.Radio("2 hrs", "RADIO1", key="-2", enable_events=True), 
     sg.Radio("6 hrs", "RADIO1", default=True, key="-6", enable_events=True), 
     sg.Radio("12 hrs", "RADIO1", key="-12", enable_events=True)],
    
    [sg.Text('—'*22, pad = (0,0), justification = "center")],
    [sg.Text("Online Players:"), sg.Text("0", key=("-ONLINE_PLAYERS-"))],
    [sg.Listbox(values=player_list, size=(50, 8), key='player_list')],
    [sg.Button('OP', size = (10,0)), 
     sg.Button('DEOP', size = (10,0)), 
     sg.Button('Kick', size = (10,0))],
    [sg.Button("Test", key=("-TEST-"), visible=False)],
    ]
    
output_column = [
    [sg.Text(' Console Output:')],
    [sg.Multiline(size=(120, 25), key='output', autoscroll=True, disabled=True)],
    [sg.InputText(size=(114,1), key='input'), sg.Button('Run', size=(5,1))],
    ]
    

layout = [
    [sg.Column(output_column, justification = "left", vertical_alignment = ("top")), 
     sg.Column(operations_column, justification = "left", vertical_alignment = ("top"))],
    ]


#sg.theme('DefaultNoMoreNagging')

window = sg.Window('BDSX Manager', layout, size = (1200,600), finalize=True)

restart_interval = config['SERVER'].get('RestartInterval', '6 hr')
if restart_interval == '1':
    window['-1'].update(value=True)
elif restart_interval == '2':
    window['-2'].update(value=True)
elif restart_interval == '6':
    window['-6'].update(value=True)
elif restart_interval == '12':
    window['-12'].update(value=True)

restart_enabled = config['SERVER'].getboolean('Restartenabled')
window['-RESTART_ENABLED-'].update(value=restart_enabled)


while True:
    # read the window's events
    event, values = window.read()
    print(event)
    
    restart_enabled = config['SERVER'].getboolean('Restartenabled')
    if restart_enabled is True and process is not None:
        time.sleep(restart_interval)
        print('Restart')

    if event == 'Run':
        print("run", values['input'])
        run_command(values)
        
    # if the 'Run .bat file' button is clicked
    if event == 'Start':
    # Check if the process is already running
        if process is not None:
            sg.popup('Server is already running')
        else:
            # run the .bat file with the command as an argument
            start_server()
            if restart_enabled == 1:
                start_server_restart()



    if event == 'OP':
        op_player()

    if event == 'DEOP':
        deop_player()

    if event == 'Restart':
        restart_server()
        player_list = []  # remove all players
        window['player_list'].update(values=player_list)
        player_count = 0
        window['-ONLINE_PLAYERS-'].update(f"Players: {player_count}")

    if event == 'Kick':
        kick_player()

    elif event == "Index.ts":
        file_path = os.path.join(os.getcwd(), "Index.ts")
        subprocess.run(["start", "", file_path], shell=True)

    elif event == "Server.properties":
        file_path = os.path.join(os.getcwd(), "Server.properties")
        subprocess.run(["start", "", file_path], shell=True)

    if event == 'BDSX Folder':
        current_folder = os.getcwd()  # Get the current working directory
        subprocess.Popen(f'explorer "{current_folder}"')  # Open the folder using the default file explorer

    if event == "-TEST-":
        if restart_enabled == 1 and process is not None:
            print(restart_enabled)
            print(f"Restart enabled: {restart_enabled}")
            print(f"Process: {process}")

    if event == 'Stop':
        if process is None:
            sg.popup('Server is not running')
        else:
            stop_server()
            player_list = []  # remove all players
            window['player_list'].update(values=player_list)
            player_count = 0
            window['-ONLINE_PLAYERS-'].update(player_count)
            
    if event == '-1' or event == '-2' or event == '-6' or event == '-12':
        print("Test")
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


    # if the 'Exit' button is clicked or the window is closed
    if event in (None,):
        if process is not None:
            stop_server()
            break
        else:
            break

# close the window
window.close()

