import sublime
import sublime_plugin
import subprocess
import os
import threading
import fnmatch
import platform


from datetime import datetime

SETTINGS_FILE = "WorkspaceMirroring.sublime-settings"


def settings():
    return sublime.load_settings(SETTINGS_FILE)


def show_error_popup(window, message):
    def _show():
        if window and window.active_view():
            window.active_view().show_popup(
                "<b style='color:red'>File not synced</b><br><br>" + message,
                max_width=1000
            )
    sublime.set_timeout(_show, 0)


def run_command(cmd, timeout=None):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timer = None

    if timeout:
        # Kill process if it exceeds timeout
        timer = threading.Timer(timeout, proc.kill)
        timer.start()

    stdout, stderr = proc.communicate()

    if timer:
        timer.cancel()

    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout + stderr)

    return stdout, stderr

def upload_file(file_path, window):
    # get the configuration
    REMOTE_USER = settings().get("remote_user")
    REMOTE_HOST = settings().get("remote_host")
    REMOTE_BASE_DIR = settings().get("remote_base_dir")
    LOCAL_BASE_DIR = settings().get("local_base_dir")
    TIMEOUT = settings().get("timeout")

    #optional configuration
    PASSWORD_FILE = settings().get("password_file","")
    KEY_FILE = settings().get("key_file","")

    # Validate required settings
    if not all([REMOTE_USER, REMOTE_HOST, REMOTE_BASE_DIR, LOCAL_BASE_DIR, TIMEOUT]):
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = "Missing required settings"
        print("🔴[" + timestamp + "] " + msg)
        show_error_popup(window, msg)
        return

    # set the relative paths against the remote and local base
    relative_path = os.path.relpath(file_path, LOCAL_BASE_DIR)
    # change \ to / for syncing from windows (local) to linux (remote)
    remote_path = REMOTE_BASE_DIR + "/" + relative_path.replace("\\", "/")

    # build scp command
    scp_command = ["scp"]
    if KEY_FILE:
       scp_command += ["-i", KEY_FILE]
    elif PASSWORD_FILE:
        if platform.system() == "Windows":
            timestamp = datetime.now().strftime("%H:%M:%S")
            msg = "sshpass not supported in Windows"
            print("🔴[" + timestamp + "]" + msg)
            show_error_popup(window,msg)
            return
        else:
            # Use scp/sshpass as current
            scp_command = ["sshpass", "-f", PASSWORD_FILE] + scp_command

    # add the file to sync and remote target
    scp_command += [file_path, REMOTE_USER + "@" + REMOTE_HOST + ":" + remote_path]


    try:
        run_command(scp_command, TIMEOUT)
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = "🟢[" + timestamp + "] Successfully uploaded " + file_path
        print(msg)


    except subprocess.CalledProcessError as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = "ERROR  to upload: " + relative_path + " error: " + e.output.decode() if e.output else "no debug error" 
        print("🔴[" + timestamp + "]" + msg)
        show_error_popup(window,msg)


def is_in_sync_folders(file_path, folders):

    file_path = os.path.abspath(file_path)

    for folder in folders:
        folder = os.path.abspath(folder)
        try:
            if file_path.startswith(folder + os.sep):
                return True
        except ValueError:
            # Happens on Windows if drives differ
            continue

    return False


def is_excluded(file_path, patterns):
    """
    Check if file_path matches any of the exclude patterns.
    Supports glob patterns like: *.log, *.tmp, __pycache__/*, .git/*
    """
    if not patterns:
        return False

    file_path = os.path.normpath(file_path)
    filename = os.path.basename(file_path)

    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
        # Match against full path (for patterns like __pycache__/*)
        if fnmatch.fnmatch(file_path, pattern):
            return True
        # Check if pattern appears anywhere in path
        if '*' not in pattern and pattern in file_path:
            return True

    return False


class WorkspaceMirroringSaveListener(sublime_plugin.EventListener):


    def on_post_save(self, view):

        file_path = view.file_name()
        if not file_path:
            return

        if not settings().get("enabled", True):
            msg = "WorkspaceMirroring is disabled"
            print(msg)
            return

        if not is_in_sync_folders(file_path, settings().get("folders_to_sync", [])):
            msg = "skip " + file_path + " - File Not in sync folders"
            print(msg)
            return

        if is_excluded(file_path,  settings().get("exclude_patterns", [])):
            msg = "skip " + file_path + " - File pattern is excluded"
            print(msg)
            return

        # Run upload in background thread
        threading.Thread(
            target=upload_file,
            args=(file_path, view.window()),
            daemon=True
        ).start()

# ----------------------------
# Plugin lifecycle
# ----------------------------
def plugin_loaded():
    settings().add_on_change(
        "WorkspaceMirroring_reload",
        lambda: print("WorkspaceMirroring settings reloaded")
    )

def plugin_unloaded():
    sublime.load_settings(SETTINGS_FILE).clear_on_change("WorkspaceMirroring_reload")
