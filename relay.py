import trio
from python_socks.async_.trio import Proxy
from dataclasses import dataclass



PROXY_URL = 'socks5://127.0.0.1:1080'
DEST = 'steamcommunity.com'

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
        await trio.serve_tcp(self._relay, self.port, host='127.0.0.1')


async def main():
    async with trio.open_nursery() as nur:
        nur.start_soon(Relay(80).relay)
        nur.start_soon(Relay(443).relay)


if __name__ == '__main__':
    trio.run(main)