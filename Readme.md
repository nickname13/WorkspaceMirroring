# WorkspaceMirroring

Automatically uploads files on save to a remote host via SCP/SSH.
The idea is that you can have a repo locally and remotely (dev machine).
It is your responsibility to keep the repos in sync (git pull/push etc).

## Installation

1. Clone or copy this repository into your `Packages/` folder.
2. Edit settings in Sublime: **Preferences → Package Settings → Workspace Mirroring → Settings**

## Settings

| Setting | Description |
|---------|-------------|
| `enabled` | Enable/disable the plugin (default: `true`) |
| `remote_user` | Remote SSH username |
| `remote_host` | Remote host address |
| `local_base_dir` | Local base directory path |
| `remote_base_dir` | Base path on remote host |
| `folders_to_sync` | List of local folders to watch for changes |
| `exclude_patterns` | List of glob patterns to exclude (e.g. `["*.log", "__pycache__"]`) |
| `key_file` | Path to SSH private key (optional) |
| `password_file` | Path to file containing SSH password (optional) |
| `timeout` | SCP command timeout in seconds (default: `10`) |

## Authentication

Supports three authentication modes:

1. **Key file** (`key_file` set) → `scp -i /path/to/key ...`
2. **Password file** (`password_file` set) → `sshpass -f /path/to/pass scp ...`
3. **Default** (neither set) → uses SSH agent or `~/.ssh/id_rsa`

## Requirements

- `sshpass` (only if using password authentication)

## Platform Support
| Platform | Status |
|----------|--------|
| Linux | ✅ Tested |
| macOS | ⚠️ Should work (untested) |
| Windows | ⚠️ Requires OpenSSH (Win10+), password auth not supported |