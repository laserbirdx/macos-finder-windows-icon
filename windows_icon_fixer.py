#!/usr/bin/env python3
"""
Automatically replaces the ugly Windows CRT BSOD icon (public.generic-pc) in macOS Finder
with the sleek Cinema Display icon (same as NAS/Bonjour SMB servers) by registering a
LocalOnly (_smb._tcp.local.) mDNS proxy for NetBIOS-discovered Windows hosts.
"""

import re
import signal
import subprocess
import sys
import time
from typing import Dict, Optional, Set, Tuple


def run_dns_sd_capture(args: list, timeout_sec: float = 2.0) -> str:
    proc = subprocess.Popen(
        ["/usr/bin/dns-sd"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout_sec)
        return out
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            out, _ = proc.communicate(timeout=1.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
        return out


def get_workgroup_domains() -> Set[str]:
    domains = {"WORKGROUP"}
    out = run_dns_sd_capture(["-E"], timeout_sec=1.5)
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1] in ("Added", "Add"):
            dom = parts[-1].strip(".")
            if dom and dom.lower() != "local":
                domains.add(dom)
    return domains


def get_native_smb_hosts() -> Set[str]:
    """Return lowercase instance names of _smb._tcp.local. advertised on physical interfaces (if > 0)."""
    native = set()
    out = run_dns_sd_capture(["-B", "_smb._tcp", "local."], timeout_sec=1.8)
    for line in out.splitlines():
        # Format: Timestamp A/R Flags if Domain ServiceType InstanceName
        m = re.match(
            r"^\s*\d+:\d+:\d+\.\d+\s+(Add|Rmv)\s+\d+\s+(-?\d+)\s+\S+\s+_smb\._tcp\.\s+(.+)$",
            line,
        )
        if m:
            action, iface_str, instance = m.group(1), m.group(2), m.group(3).strip()
            iface = int(iface_str)
            if iface > 0 and action == "Add":
                native.add(instance.lower())
    return native


def get_netbios_hosts(domains: Set[str]) -> Set[str]:
    """Return lowercase hostnames discovered by netbiosd in _netbios._udp.<WORKGROUP>."""
    hosts = set()
    for dom in domains:
        out = run_dns_sd_capture(["-B", "_netbios._udp", dom], timeout_sec=1.8)
        for line in out.splitlines():
            m = re.match(
                r"^\s*\d+:\d+:\d+\.\d+\s+(Add|Rmv)\s+\d+\s+(-?\d+)\s+\S+\s+_netbios\._udp\.\s+(.+)$",
                line,
            )
            if m:
                action, _, instance = m.group(1), m.group(2), m.group(3).strip()
                if action == "Add":
                    hosts.add(instance.lower())
    return hosts


def resolve_netbios_ip(hostname: str) -> Optional[str]:
    try:
        res = subprocess.run(
            ["/usr/bin/smbutil", "lookup", hostname],
            capture_output=True,
            text=True,
            timeout=3.0,
        )
        for line in res.stdout.splitlines():
            m = re.search(r"IP address of [^:]+:\s*(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


class ProxyManager:
    def __init__(self) -> None:
        # hostname -> (ip, Popen)
        self.proxies: Dict[str, Tuple[str, subprocess.Popen]] = {}
        self.running = True

    def start_proxy(self, hostname: str, ip: str) -> None:
        self.stop_proxy(hostname)
        fqdn = f"{hostname}.local"
        proc = subprocess.Popen(
            [
                "/usr/bin/dns-sd",
                "-lo",
                "-P",
                hostname,
                "_smb._tcp",
                "local",
                "445",
                fqdn,
                ip,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.proxies[hostname] = (ip, proc)
        print(f"[+] Registered sleek icon proxy for {hostname} ({ip})", flush=True)

    def stop_proxy(self, hostname: str) -> None:
        entry = self.proxies.pop(hostname, None)
        if entry:
            _, proc = entry
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
            print(f"[-] Stopped proxy for {hostname}", flush=True)

    def stop_all(self) -> None:
        for hostname in list(self.proxies.keys()):
            self.stop_proxy(hostname)

    def sync(self) -> None:
        domains = get_workgroup_domains()
        native_smb = get_native_smb_hosts()
        netbios_hosts = get_netbios_hosts(domains)

        target_hosts = netbios_hosts - native_smb

        # Check existing proxies as well so temporary NetBIOS browse blips don't drop active hosts
        candidates = target_hosts | (set(self.proxies.keys()) - native_smb)

        for host in candidates:
            ip = resolve_netbios_ip(host)
            if not ip:
                if host in self.proxies:
                    self.stop_proxy(host)
                continue

            current = self.proxies.get(host)
            if current is None or current[0] != ip or current[1].poll() is not None:
                self.start_proxy(host, ip)

        # Remove proxies for hosts that now advertise native SMB
        for host in list(self.proxies.keys()):
            if host in native_smb:
                self.stop_proxy(host)


def main() -> int:
    manager = ProxyManager()

    def handle_signal(signum, frame):
        manager.running = False
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    print("[*] Starting Windows Finder Icon Fixer...", flush=True)
    while manager.running:
        try:
            manager.sync()
        except Exception as exc:
            print(f"[!] Error during sync: {exc}", flush=True)
        for _ in range(15):
            if not manager.running:
                break
            time.sleep(1.0)

    manager.stop_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
