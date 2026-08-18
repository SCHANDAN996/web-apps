from flask import Flask, render_template, request, jsonify
import pywhatkit
import os
import threading
from werkzeug.utils import secure_filename
import time
import pyautogui
import platform
import subprocess
import json
from datetime import datetime
import uuid
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)

HISTORY_FILE = "history.json"
PENDING_TASKS = {} # task_id -> {"timer_obj", "target", "time", "type", "desc"}

def log_history(target_id, message_type, content, status="Sent"):
    try:
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'w') as f:
                json.dump([], f)
        
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
            
        history.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target": target_id,
            "type": message_type,
            "content": content,
            "status": status
        })
        
        if len(history) > 100:
            history = history[:100]
            
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Failed to record history: {e}")

def execute_with_cleanup(task_id, func, *args):
    try:
        func(*args)
    finally:
        if task_id in PENDING_TASKS:
            del PENDING_TASKS[task_id]

def schedule_or_run(time_str, func, metadata, *args):
    task_id = str(uuid.uuid4())
    if time_str:
        try:
            target_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M")
            delta = (target_time - datetime.now()).total_seconds()
            
            if delta > 0:
                print(f"Scheduling task {task_id} in {delta} seconds for {time_str}")
                
                t = threading.Timer(delta, execute_with_cleanup, args=(task_id, func) + args)
                t.start()
                
                PENDING_TASKS[task_id] = {
                    "timer_obj": t,
                    "target": metadata.get("target", "Unknown"),
                    "time": time_str,
                    "type": metadata.get("type", "?"),
                    "desc": metadata.get("desc", "?")
                }
                return True, task_id
            else:
                print("Scheduled time is in the past! Running immediately.")
        except Exception as e:
            print(f"Time parse error: {e}")

    # Instant Run
    t = threading.Thread(target=execute_with_cleanup, args=(task_id, func) + args)
    t.start()
    return False, task_id

def send_msg_thread(target_id, message, is_group):
    try:
        print(f"Sending text to {'Group ' if is_group else ''}{target_id}...")
        if is_group:
            pywhatkit.sendwhatmsg_to_group_instantly(target_id, message, wait_time=15, tab_close=True, close_time=3)
        else:
            pywhatkit.sendwhatmsg_instantly(target_id, message, wait_time=15, tab_close=True, close_time=3)
        
        log_history(target_id, "Group Text" if is_group else "Direct Text", message)
        print("Message sent successfully!")
    except Exception as e:
        log_history(target_id, "Group Text" if is_group else "Direct Text", message, f"Failed: {e}")
        print(f"Failed to send message: {e}")

def send_attachment_thread(target_id, filepaths, caption, is_group):
    try:
        print(f"Opening chat to send attachments to {target_id}...")
        if is_group:
            pywhatkit.sendwhatmsg_to_group_instantly(target_id, " ", wait_time=16, tab_close=False)
        else:
            pywhatkit.sendwhatmsg_instantly(target_id, " ", wait_time=16, tab_close=False)
            
        time.sleep(2)
        
        if platform.system() == 'Windows':
            print("Executing powershell clipboard copy for multiple files...")
            files_arg = ", ".join([f"'{p}'" for p in filepaths])
            res = subprocess.run(["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Path {files_arg}"], capture_output=True, text=True)
            if res.returncode != 0:
                print(f"Clipboard Error: {res.stderr}")
        
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(4) 
        
        if caption:
            pyautogui.write(caption, interval=0.01)
            time.sleep(1)
            
        pyautogui.press('enter')
        
        msg_type = "Group Media/Doc" if is_group else "Direct Media/Doc"
        content_desc = f"Sent {len(filepaths)} files. Caption: {caption}"
        log_history(target_id, msg_type, content_desc)
        print("Attachment(s) sent successfully!")
        
    except Exception as e:
        msg_type = "Group Media/Doc" if is_group else "Direct Media/Doc"
        log_history(target_id, msg_type, f"Failed: {e}", "Failed")
        print(f"Failed to send attachment: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/history', methods=['GET'])
def get_history():
    if not os.path.exists(HISTORY_FILE):
        return jsonify([])
    try:
        with open(HISTORY_FILE, 'r') as f:
            return jsonify(json.load(f))
    except:
        return jsonify([])

@app.route('/api/pending', methods=['GET'])
def get_pending():
    results = []
    for tid, info in PENDING_TASKS.items():
        results.append({
            "id": tid,
            "target": info["target"],
            "time": info["time"].replace("T", " "),
            "type": info["type"],
            "desc": info["desc"]
        })
    results.sort(key=lambda x: x['time'])
    return jsonify(results)

@app.route('/api/pending/<task_id>', methods=['DELETE'])
def cancel_pending(task_id):
    if task_id in PENDING_TASKS:
        t = PENDING_TASKS[task_id]['timer_obj']
        t.cancel()
        target = PENDING_TASKS[task_id]['target']
        msg_type = PENDING_TASKS[task_id]['type']
        desc = PENDING_TASKS[task_id]['desc']
        
        del PENDING_TASKS[task_id]
        log_history(target, msg_type, f"Cancelled: {desc}", "Cancelled")
        return jsonify({"success": True, "message": "Task Cancelled."})
    return jsonify({"success": False, "error": "Task not found"}), 404

@app.route('/api/send', methods=['POST'])
def send_unified():
    target = request.form.get('target', '').strip()
    message = request.form.get('message', '')
    send_time = request.form.get('time', '')
    files = request.files.getlist('files')
    
    if not target:
        return jsonify({"success": False, "error": "Target (Phone/Group) is required"}), 400
        
    clean_target = target.replace(' ', '').replace('-', '')
    is_group = not bool(re.match(r'^\+?[0-9]+$', clean_target))
    
    if not is_group:
        if not clean_target.startswith('+'):
            if len(clean_target) == 10:
                clean_target = "+91" + clean_target
            elif clean_target.startswith("91") and len(clean_target) > 10:
                clean_target = "+" + clean_target
            else:
                clean_target = "+" + clean_target
        target = clean_target
    
    has_files = files and files[0].filename != ''
    
    metadata = {
        "target": target,
        "type": f"{'Group' if is_group else 'Direct'} {'Media' if has_files else 'Text'}",
    }
    
    if has_files:
        filepaths = []
        for f in files:
            filename = secure_filename(f.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(filepath)
            filepaths.append(os.path.abspath(filepath))
            
        metadata["desc"] = f"Attached {len(filepaths)} files. Caption: {message}"
        is_sched, _ = schedule_or_run(send_time, send_attachment_thread, metadata, target, filepaths, message, is_group)
    else:
        if not message:
             return jsonify({"success": False, "error": "Message content is required if no files attached"}), 400
        metadata["desc"] = f"Text: {message[:20]}..."
        is_sched, _ = schedule_or_run(send_time, send_msg_thread, metadata, target, message, is_group)
        
    if is_sched:
        log_history(target, metadata["type"], metadata["desc"], f"Scheduled ({send_time.replace('T', ' ')})")
    
    return jsonify({"success": True, "message": f"Execution {'scheduled' if is_sched else 'started'} successfully."})


if __name__ == '__main__':
    print("\n" + "="*50)
    print(" WhatsApp Unified Dashboard Running!")
    print(" Open http://127.0.0.1:9243 in your browser.")
    print("="*50 + "\n")
    app.run(debug=True, port=9243, host='0.0.0.0', use_reloader=False)
