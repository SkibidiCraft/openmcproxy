import asyncio
import argparse

async def handle_client(reader: asyncio.StreamReader,
                        writer: asyncio.StreamWriter,
                        target_host: str,
                        target_port: int):
    try:
        target_reader, target_writer = await asyncio.open_connection(
            target_host, target_port
        )
    except Exception as e:
        print(f"[!] Ziel nicht erreichbar: {e}")
        writer.close()
        await writer.wait_closed()
        return

    async def forward(src, dst):
        try:
            while data := await src.read(4096):
                dst.write(data)
                await dst.drain()
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        finally:
            dst.close()

    await asyncio.gather(
        forward(reader, target_writer),
        forward(target_reader, writer),
    )

async def start_proxy(listen_host: str, listen_port: int,
                      target_host: str, target_port: int):
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, target_host, target_port),
        listen_host,
        listen_port,
    )
    addr = server.sockets[0].getsockname()
    print(f"[+] Proxy läuft auf {addr[0]}:{addr[1]} → {target_host}:{target_port}")

    async with server:
        await server.serve_forever()

def main():
    parser = argparse.ArgumentParser(
        description="TCP‑Proxy für Minecraft (25595 → alphaattack.de:25565)"
    )
    parser.add_argument("--listen-host", default="0.0.0.0",
                        help="IP, auf der der Proxy lauscht (default: 0.0.0.0)")
    parser.add_argument("--listen-port", type=int, default=25595,
                        help="Port, auf dem der Proxy lauscht (default: 25595)")
    parser.add_argument("--target-host",
                        help="Ziel‑Hostname")
    parser.add_argument("--target-port", type=int, default=25565,
                        help="Ziel‑Port (WICHTIG: VORHER AUF mcstatus.io DEN SRV EINTRAG NACHSCHAUEN) (default: 25565)")

    args = parser.parse_args()

    try:
        asyncio.run(
            start_proxy(args.listen_host, args.listen_port,
                        args.target_host, args.target_port)
        )
    except KeyboardInterrupt:
        print("\n[+] Proxy beendet")

if __name__ == "__main__":
    main()
