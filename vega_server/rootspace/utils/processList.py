import psutil

ignore_list = ['cryptd', 'btrfs', 'kworker', 'kthreadd',
               'systemd', 'mount', 'napi', 'sleep', 'rcu',
               'nvidia', 'slub', 'netns', 'migration',
               'idle', 'sudo', 'cpu', 'irq', 'vfio', 'acpi',
               'zswap', 'ipv6', 'nvme', 'charger', 'watchdog',
               'postgres', 'docker', 'kernel', 'container',
               'libvirt', 'preload', 'session', 'gdm', 'python',
               'daemon', 'queue', 'bluetooth', 'scsi', 'raid',
               'mongo', 'node', 'registry', 'gvfsd', 'gnome',
               'shell', 'identity', 'redis', 'pipewire', 'dnsmasq',
               'iprt', 'cron', 'snapd', 'php', 'xorg', 'pihole',
               'master', 'notify', 'nacl', 'ksmd', 'tracker',
               'modem', 'network', 'agent', 'bash', 'integrity',
               'pulse', 'java', 'crash', 'ibus', 'dbus', 'snyk',
               'dconf', 'gsd', 'qmgr', 'clam', 'volume', 'monitor',
               'tray', 'power', 'compact', 'sys', 'color', 'notifier',
               'xdg', 'store', 'disk', 'crypt', 'control', 'uvm',
               'server', 'factory', 'audit', 'kdev', 'swap', 'ata',
               'launcher', 'glib', 'package', 'cfg', 'dhcp', 'http',
               'inet', 'wpa', 'block', 'poller']

strict_ignore_list = ['md', 'mld', 'sh', 'gjs', 'cat', 'tor']


def get_process_list():
    process_set = set()
    # Iterate over all running process
    for process in psutil.process_iter():
        try:
            # Get process name
            process_name = process.name().lower()
            process_set.add(process_name)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    filtered_process_set = set()

    for process_name in process_set:
        if not similar_string_list(process_name, ignore_list, strict_ignore_list):
            filtered_process_set.add(process_name)

    return filtered_process_set


def similar_string_list(string, list, strict_list):
    for ref_str in list:
        if ref_str in string:
            return True
    for ref_str in strict_list:
        if ref_str == string:
            return True
    return False
