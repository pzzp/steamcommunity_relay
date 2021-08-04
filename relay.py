import winreg
import trio
from python_socks.async_.trio import Proxy
from dataclasses import dataclass



DEST = 'steamcommunity.com'
PROXY_URL = 'socks5://127.0.0.1:1080'

@dataclass
class Relay:
    port: int

    async def _relay(self, local_stream: trio.SocketStream):
        proxy = Proxy.from_url(PROXY_URL)
        remote_sock = await proxy.connect(DEST, self.port)
        remote_stream = trio.SocketStream(remote_sock)

        async def upload():
            async for up_data in local_stream:
                await remote_stream.send_all(up_data)
        
        async def dowload():
            async for down_data in remote_stream:
                await local_stream.send_all(down_data)
        
        async with trio.open_nursery() as nur:
            nur.start_soon(upload)
            nur.start_soon(dowload)
    
    async def relay(self): 
        await trio.serve_tcp(self._relay, self.port, host='127.0.0.251')


async def main():
    async with trio.open_nursery() as nur:
        nur.start_soon(Relay(80).relay)
        nur.start_soon(Relay(443).relay)


def delete_reg_value(key_class, key_path, name):
    with winreg.OpenKey(key_class, key_path, 0, winreg.KEY_WRITE) as key:
        winreg.DeleteValue(key, name)

def insert_reg_value(key_class, key_path, name, value, value_type):
    with winreg.OpenKey(key_class, key_path, 0, winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key, name, 0, value_type, value)


def enable_autostart():
    import winreg
    import sys
    import os
    python = sys.executable.replace('python.exe', 'pythonw.exe')
    script = os.path.abspath(__file__)

    key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
    name = 'steamcommnunity_relay'
    value = f'"{python}" "{script}"'
    insert_reg_value(winreg.HKEY_CURRENT_USER, key_path, name, value, winreg.REG_SZ)

def disable_autostart():
    import winreg
    key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
    name = 'steamcommnunity_relay'
    delete_reg_value(winreg.HKEY_CURRENT_USER, key_path, name)

def print_help():
    doc = '''
python relay.py [option] [host port]
options:
--autostart                   
--disable-autostart            
'''
    print(doc)

if __name__ == '__main__':
    import sys
    argv = [x for x in sys.argv[1:]]
    if '--autostart' in argv:
        enable_autostart()
        exit(0)
    if '--disable-autostart' in sys.argv:
        disable_autostart()
        exit(0)
    if len(argv) == 2:
        PROXY_URL = f'socks5://{sys.argv[0]}:{sys.argv[1]}'
    elif len(argv) != 0:
        print_help()
        exit(1)
    trio.run(main)
