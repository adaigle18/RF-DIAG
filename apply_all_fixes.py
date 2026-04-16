with open('wifi_utils.py', 'r') as f:
    c = f.read()

# Fix 1 - Auto-detect IP address
c = c.replace(
    '    host: str = "169.254.42.1",',
    '    host: str = None,'
)

c = c.replace(
    '        self.host = host',
    '''        # Auto-detect WLANPi IP if not specified
        if host is None:
            import socket as _s
            for _ip in ["169.254.42.1", "198.18.42.1"]:
                try:
                    s = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                    s.settimeout(1)
                    s.connect((_ip, 22))
                    s.close()
                    host = _ip
                    break
                except Exception:
                    pass
            if host is None:
                host = "169.254.42.1"
        self.host = host'''
)

c = c.replace('host="169.254.42.1",', 'host=None,')

# Fix 2 - Increase timeouts
c = c.replace('connect_timeout: int = 5', 'connect_timeout: int = 15')
c = c.replace('exec_timeout: int = 10', 'exec_timeout: int = 30')

# Fix 3 - Probe timeout
c = c.replace(
    'with socket.create_connection((self.host, 22), timeout=2):',
    'with socket.create_connection((self.host, 22), timeout=10):'
)

# Fix 4 - Add banner_timeout and auth_timeout
c = c.replace(
    '            hostname=self.host,\n            username=self.user,\n            timeout=self.connect_timeout,\n        )',
    '            hostname=self.host,\n            username=self.user,\n            timeout=self.connect_timeout,\n            banner_timeout=30,\n            auth_timeout=30,\n        )'
)

# Fix 5 - Add look_for_keys and allow_agent
c = c.replace(
    '            kwargs["key_filename"] = self.key_path\n        if self.password:',
    '            kwargs["key_filename"] = self.key_path\n            kwargs["look_for_keys"] = False\n            kwargs["allow_agent"] = False\n        if self.password:'
)

# Fix 6 - Add IPv4 socket with interface binding and _local_ip helper
c = c.replace(
    '        client.connect(**kwargs)\n        return client\n\n    def _is_alive',
    '''        import socket as _socket
        _sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        _sock.settimeout(self.connect_timeout)
        _sock.bind((self._local_ip(), 0))
        _sock.connect((self.host, 22))
        kwargs["sock"] = _sock
        client.connect(**kwargs)
        return client

    def _local_ip(self) -> str:
        import socket as _s
        try:
            tmp = _s.socket(_s.AF_INET, _s.SOCK_DGRAM)
            tmp.connect((self.host, 22))
            ip = tmp.getsockname()[0]
            tmp.close()
            return ip
        except Exception:
            return "0.0.0.0"

    def _is_alive'''
)

# Fix 7 - Add ip link set before scan trigger
c = c.replace(
    '            self.run(f"sudo /usr/sbin/iw dev {interface} scan trigger 2>/dev/null || true")',
    '            self.run(f"sudo /sbin/ip link set {interface} up 2>/dev/null || true")\n            self.run(f"sudo /usr/sbin/iw dev {interface} scan trigger 2>/dev/null || true")'
)

with open('wifi_utils.py', 'w') as f:
    f.write(c)
print("wifi_utils.py fixed!")

# Now fix wifi_tool.py
with open('wifi_tool.py', 'r') as f:
    c = f.read()

# Fix 8 - Change wlan1 to wlan0
c = c.replace(
    'WLANPI_SCAN_IFACE = "wlan1"',
    'WLANPI_SCAN_IFACE = "wlan0"'
)

# Fix 9 - Increase sleep
c = c.replace('time.sleep(3)', 'time.sleep(10)')

with open('wifi_tool.py', 'w') as f:
    f.write(c)
print("wifi_tool.py fixed!")
