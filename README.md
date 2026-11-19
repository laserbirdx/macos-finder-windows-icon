<p align="center">
  <img src="assets/generic-pc.png" width="240" alt="macOS Generic PC CRT BSOD Icon" />
</p>

<h1 align="center">macos-finder-windows-icon</h1>

<p align="center">
  Replace the infamous 1990s CRT Blue Screen of Death (<code>public.generic-pc</code>) icon in macOS Finder with the modern Apple display icon used for NAS and Bonjour SMB servers — without disabling SIP.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-macOS-black?logo=apple" alt="Platform: macOS" />
  <img src="https://img.shields.io/badge/python-3.9%2B-blue?logo=python" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/SIP-Enabled%20(Safe)-success" alt="SIP Enabled" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" />
</p>

---

## Why Does macOS Show the CRT BSOD Icon?

When macOS discovers network shares in Finder:
1. **Bonjour / mDNS (`_smb._tcp.local.`)** devices (such as modern NAS appliances or Macs) receive the sleek Apple Cinema Display icon (`com.apple.mac` / `com.apple.led-cinema-display-27.icns`).
2. **Windows PCs** typically do not advertise `_smb._tcp.local.` over mDNS and are instead discovered by macOS's `netbiosd` daemon via **NetBIOS (`_netbios._udp.<WORKGROUP>.`)**. Any host discovered exclusively via NetBIOS is tagged with the `public.generic-pc` UTI and assigned Apple's vintage beige CRT monitor with a Windows Blue Screen of Death (`public.generic-pc.icns`).

## How It Works

Because `CoreTypes.bundle` is protected by System Integrity Protection (SIP), modifying system `.icns` files directly is neither safe nor persistent across macOS updates.

Instead, `macos-finder-windows-icon` runs a lightweight, zero-dependency background agent (`LaunchAgent`) that:
1. Monitors NetBIOS-discovered hosts (`_netbios._udp`) registered by `netbiosd`.
2. Filters out hosts that already advertise native Bonjour SMB (`_smb._tcp.local.`) on physical network interfaces.
3. Resolves the IPv4 address of each Windows host via `smbutil lookup`.
4. Registers a **LocalOnly** (`interface -1`, `dns-sd -lo -P`) `_smb._tcp.local.` mDNS proxy record on your Mac.

Finder automatically merges the NetBIOS entry with the LocalOnly `_smb._tcp.local.` record and switches the device icon from the CRT BSOD icon to the modern display icon — without broadcasting extra mDNS traffic onto your LAN.

---

## Installation

Clone the repository and run the installer script:

```bash
git clone https://github.com/laserbirdx/macos-finder-windows-icon.git
cd macos-finder-windows-icon
chmod +x install.sh uninstall.sh
./install.sh
```

The installer copies `windows_icon_fixer.py` into `~/Library/Application Support/windows-icon-fixer/` and registers a user `LaunchAgent` (`~/Library/LaunchAgents/com.laserbirdx.windows-icon-fixer.plist`) that starts immediately and runs automatically at login.

---

## Uninstallation

To stop the background service and remove all installed files:

```bash
./uninstall.sh
```

---

## Manual Usage

You can also run the daemon directly in the terminal for testing or debugging:

```bash
/usr/bin/python3 windows_icon_fixer.py
```

---

## Project Structure

- `windows_icon_fixer.py` — Zero-dependency Python 3 daemon that bridges NetBIOS hosts to LocalOnly `_smb._tcp.local.` mDNS records.
- `install.sh` — Installs and loads the macOS `LaunchAgent`.
- `uninstall.sh` — Unloads and removes the `LaunchAgent`.
- `public.generic-pc.icns` & `assets/generic-pc.png` — Apple's original `public.generic-pc` CRT BSOD icon for reference.

---

## License

Released under the [MIT License](LICENSE).
