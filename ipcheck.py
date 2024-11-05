import winreg

def get_priority_manual_ipv4():
    """
    Get the highest priority manually configured IPv4 address from the Windows Registry.
    Priority order:
    1. IP addresses starting with "192.168..."
    2. IP addresses starting with "10.1..."
    3. Return "0.0.0.0" if neither are found.
    """
    ip_addresses = []
    
    try:
        # Open the registry key where network adapter information is stored
        reg_key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path)

        # Iterate through all subkeys (network adapters)
        i = 0
        while True:
            try:
                adapter_key_name = winreg.EnumKey(reg_key, i)
                adapter_key_path = reg_key_path + "\\" + adapter_key_name
                adapter_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, adapter_key_path)

                # Check for a manually configured IP address
                try:
                    ip_address, _ = winreg.QueryValueEx(adapter_key, "IPAddress")
                    if ip_address and ip_address[0] != "0.0.0.0":
                        ip_addresses.append(ip_address[0])  # Collect all valid IPs
                except FileNotFoundError:
                    pass  # IPAddress not found for this adapter, continue to the next

                i += 1
            except OSError:
                # No more subkeys
                break

        # Sort based on priority: "192.168..." > "10.1..."
        for ip in ip_addresses:
            if ip.startswith("192.168"):
                return ip
        for ip in ip_addresses:
            if ip.startswith("10.1"):
                return ip

        return "0.0.0.0"  # Return default if no priority IP is found

    except Exception:
        return "0.0.0.0"



    
if __name__ == '__main__':
    
  print(get_priority_manual_ipv4()
  )