"""Private temporary desktop for manual server login; reachable only by SSH tunnel."""
import os
from pathlib import Path
import secrets
import subprocess
import time

state = Path('/var/lib/studystation-instagram')
auth = state / 'xauthority'
password = state / 'vnc-password'
if not password.is_file():
    raise SystemExit('Create private VNC password first: x11vnc -storepasswd /var/lib/studystation-instagram/vnc-password')
os.umask(0o077)
auth.touch(mode=0o600)
subprocess.run(['xauth', '-f', str(auth), 'add', ':91', '.', secrets.token_hex(16)], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.environ.update(DISPLAY=':91', XAUTHORITY=str(auth))
processes = []
try:
    processes.append(subprocess.Popen(['Xvfb', ':91', '-screen', '0', '1280x900x24', '-nolisten', 'tcp', '-auth', str(auth)]))
    time.sleep(2)
    processes.append(subprocess.Popen(['openbox']))
    processes.append(subprocess.Popen(['x11vnc', '-display', ':91', '-auth', str(auth), '-localhost',
                                       '-rfbport', '5901', '-rfbauth', str(password), '-forever', '-shared', '-quiet']))
    processes.append(subprocess.Popen(['websockify', '--web=/usr/share/novnc', '127.0.0.1:6081', '127.0.0.1:5901']))
    while all(p.poll() is None for p in processes):
        time.sleep(2)
    raise SystemExit('Desktop process stopped')
finally:
    for process in reversed(processes):
        process.terminate()
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
