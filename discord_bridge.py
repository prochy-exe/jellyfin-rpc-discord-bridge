#!/usr/bin/env python3

import copy, json, websocket, threading, requests, time, signal, sys, os, subprocess, platform

# ANSI escape codes for text colors
class Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RESET = "\033[0m"  # Reset color to default

current_platform = platform.system().lower()

def printinfo(text):
  print(Color.CYAN + text + Color.RESET)

def printerr(text):
  print(Color.RED + text + Color.RESET)  

def printsucc(text): # It stands for successful you sussy baka
  print(Color.GREEN + text + Color.RESET)

cached_small_image = None
cached_big_image = None
new_big_image = None
new_small_image = None
previous_payload = None
original_status = None
ws_connected = True

current_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_path, 'config.json')
if os.path.exists(config_path):
  with open(config_path, "r") as f:
    # Load the JSON data
    config = json.load(f)
else:
  printerr("Please generate config first!")
  exit(0)

params = {}
for i in range(1, 4):
    try:
        params[i] = sys.argv[i]
    except:
        params[i] = None
token = params[1] if params[1] else config['token']
type_ = params[2] if params[2] else config.get('rpc_type', 0)
rpc_style = params[3] if params[3] else config.get('rpc_style', 0)
node_server_path = config['node_path']
jellyfin_rpc_path = config['jellyfin_rpc_path']
type_ = 0 if type_ == 0 else 3 #Convert type ints to ones used by Discord (0: Gaming, 3: Watching)

init_payload = {
    'op': 2,
    'd': {
        'token': token,
        'intents': 0,
        'properties': {
            'os': current_platform,
            'browser': "python-rpc-bridge",
            'device': "python-rpc-bridge"
        },
    }
}

clear_payload = {
    'op': 3,
    'd': {
        'since': 91879201,
        'activities': None,
        'status': original_status,
        'afk': False
    }
}

def process_image(image_url, type_, app_id):
    global cached_big_image, cached_small_image, new_big_image, new_small_image
    if image_url == cached_big_image or image_url == cached_small_image:
        return new_big_image if type_ == "large" else new_small_image
    else:
        url = f"https://discord.com/api/v9/applications/{app_id}/external-assets"
        response = requests.post(url, headers={'Authorization': token, 'Content-Type': "application/json"}, json={'urls': [image_url]})
        data = response.json()[0]
        if type_ == "large":
            cached_big_image = image_url
            new_big_image = f"mp:{data['external_asset_path']}"
            return new_big_image
        elif type_ == "small":
            cached_small_image = image_url
            new_small_image = f"mp:{data['external_asset_path']}"
            return new_small_image

def process_data(data):
    global original_status
    processed_data = data['activity']
    processed_data['type'] = type_
    if rpc_style == 0:
        processed_data['name'] = "Jellyfin"
    elif rpc_style == 1:
        processed_data['name'] = processed_data['details']
        del processed_data['details']
        processed_data['assets']['large_text'] = "Streaming on Jellyfin™"
    if processed_data['assets'].get('large_image'):
        updated_large_image = process_image(processed_data['assets']['large_image'], 'large', processed_data['application_id'])
        while not updated_large_image:
            time.sleep(1)
            updated_large_image = process_image(processed_data['assets']['large_image'], 'large', processed_data['application_id'])
        processed_data['assets']['large_image'] = updated_large_image
    if processed_data['assets'].get('small_image'):
        updated_small_image = process_image(processed_data['assets']['small_image'], 'small', processed_data['application_id'])
        while not updated_small_image:
            time.sleep(1)
            updated_small_image = process_image(processed_data['assets']['small_image'], 'small', processed_data['application_id'])
        processed_data['assets']['small_image'] = updated_small_image
    return processed_data

def update_status(activity):
    payload = {
        'op': 3,
        'd': {
            'since': 91879201,
            'activities': [activity],
            'status': original_status,
            'afk': False
        }
    }
    printinfo(
              ("Updating RPC with:\n" +
              activity['name'] + 
              (f" {Color.RED}({activity['assets']['small_text']}){Color.RESET}" if activity.get('assets', {}).get('small_text') else ""))
              if activity else json.dumps(payload, indent=4)
            ) # COLORS!1!1!
    ws.send(json.dumps(payload))

def are_objects_equal(obj1, obj2):
    result = json.dumps(obj1) == json.dumps(obj2)
    return result

def clear_rpc():
    printsucc("Clearing RPC")
    ws.send(json.dumps(clear_payload))

def on_message(ws, message):
    global previous_payload, original_status, previous_s
    payload = json.loads(message)
    op = payload.get('op')
    t = payload.get('t')
    previous_s = payload.get('s')

    if op == 10:
        heartbeat_interval = payload['d']['heartbeat_interval']
        threading.Thread(target=heartbeat, args=(heartbeat_interval / 1000,)).start()

    if t == "READY":
        original_status = payload['d']['user_settings']['status']
        printsucc("WebSocket connected, listening for RPC calls")
        websocket_event()

def heartbeat(interval):
    global ws_connected, previous_s
    while ws_connected:
        payload = {
            'op': 1,
            'd': previous_s
        }
        ws.send(json.dumps(payload))
        printinfo("Sent heartbeat")
        time.sleep(interval)
    printinfo("WebSocket connection closed. Stopping heartbeat.")

def on_error(ws, error):
    if str(error) != "0":
        printerr(f"Error in Gateway WebSocket: {error}")

def on_close(ws, close_status, close_msg):
    global ws_connected
    ws_connected = False

def on_open(ws):
    ws.send(json.dumps(init_payload))
    printinfo("WebSocket to Gateway opened")

def on_open_discord(ws):
    printinfo("WebSocket to Discord opened")

def on_message_discord(ws, message):
    global previous_payload
    received_payload = json.loads(message)
    try:
        del received_payload['pid']
        del received_payload['socketId']
    except:
        pass
    if received_payload['activity']:
        cleaned_payload = copy.deepcopy(received_payload)
        try:
            del cleaned_payload['activity']['timestamps'] # While checking if payloads are same, drop timestamps because deviation is only a couple of ms
        except:
            pass
        if not are_objects_equal(cleaned_payload, previous_payload):
            previous_payload = copy.deepcopy(cleaned_payload)
            try:
                processed_data = process_data(cleaned_payload if type_ == 3 else received_payload)# If type is 0, we need timetamps to show time remaining
                update_status(processed_data)
            except Exception as e:
                printerr(f"Error: {e}")

def on_error_discord(ws, error):
    if str(error) != "0":
      printerr(f"Error in Discord WebSocket: {error}")

def on_close_discord(ws, close_status, close_msg):
    global ws_connected
    ws_connected = False
    
def websocket_event():
    ws_discord.run_forever()

def close_connections():
    global ws, ws_discord
    ws.close()
    printinfo("Gateway WebSocket closed")
    ws_discord.close()
    printinfo("Discord WebSocket closed")

def signal_handler(sig, frame):
    global ws, ws_discord
    clear_rpc()
    printinfo("Closing connections, please wait...")
    if ws_connected:
        # Send close frame to the server
        closingThread = threading.Thread(target=close_connections)
        closingThread.start()
        closingThread.join()
    os._exit(0)

def start_node_server():
    subprocess.run(["node", node_server_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_jellyfin_rpc():
    process = subprocess.Popen(jellyfin_rpc_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
      for line in iter(process.stdout.readline, b""):
        decoded_line = line.decode("utf-8")
        if "Cleared" in decoded_line: clear_rpc() # Clear RPC when jellyfin-rpc clears it

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    arrpc_thread = threading.Thread(target=start_node_server, daemon=True)
    jellyfin_rpc_thread = threading.Thread(target=start_jellyfin_rpc, daemon=True)
    arrpc_thread.start()
    time.sleep(5)
    jellyfin_rpc_thread.start()
  
    ws = websocket.WebSocketApp("wss://gateway.discord.gg/?v=10&encoding=json",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open

    ws_discord = websocket.WebSocketApp("ws://127.0.0.1:1337",
                                        on_message=on_message_discord,
                                        on_error=on_error_discord,
                                        on_close=on_close_discord)
    ws_discord.on_open = on_open_discord

    ws.run_forever()