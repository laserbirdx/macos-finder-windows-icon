#!/usr/bin/env bash
set -euo pipefail

LABEL="com.laserbirdx.windows-icon-fixer"
LEGACY_LABEL="com.omerfaruk.windows-icon-fixer"
APP_SUPPORT_DIR="$HOME/Library/Application Support/windows-icon-fixer"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "[*] Uninstalling Windows Finder Icon Fixer..."

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/$LEGACY_LABEL" 2>/dev/null || true

rm -f "$LAUNCH_AGENTS_DIR/$LABEL.plist" "$LAUNCH_AGENTS_DIR/$LEGACY_LABEL.plist"
rm -rf "$APP_SUPPORT_DIR"

echo "[+] Uninstalled Windows Finder Icon Fixer."
