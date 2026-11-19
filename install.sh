#!/usr/bin/env bash
set -euo pipefail

LABEL="com.laserbirdx.windows-icon-fixer"
LEGACY_LABEL="com.omerfaruk.windows-icon-fixer"
APP_SUPPORT_DIR="$HOME/Library/Application Support/windows-icon-fixer"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Installing Windows Finder Icon Fixer..."

mkdir -p "$APP_SUPPORT_DIR" "$LAUNCH_AGENTS_DIR"
cp "$SCRIPT_DIR/windows_icon_fixer.py" "$APP_SUPPORT_DIR/windows_icon_fixer.py"
chmod +x "$APP_SUPPORT_DIR/windows_icon_fixer.py"

# Unload legacy or existing agent if loaded
launchctl bootout "gui/$(id -u)/$LEGACY_LABEL" 2>/dev/null || true
rm -f "$LAUNCH_AGENTS_DIR/$LEGACY_LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$APP_SUPPORT_DIR/windows_icon_fixer.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$APP_SUPPORT_DIR/fixer.log</string>
    <key>StandardErrorPath</key>
    <string>$APP_SUPPORT_DIR/fixer.log</string>
</dict>
</plist>
EOF

launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
echo "[+] Installed and started $LABEL"
echo "[+] Log file: $APP_SUPPORT_DIR/fixer.log"
