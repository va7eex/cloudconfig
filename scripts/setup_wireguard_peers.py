from dataclasses import dataclass
import os
from pyinfra import host, inventory
from pyinfra.operations import server

from setup_wireguard import interface_names


@dataclass
class WgPeerData:
    host: str
    wg_ip: str
    wg_port: int
    external: bool
    ext_ip: str | None = None
    pubkey: str | None = None
    persistent_keepalive: int | None = 25

    def get_endpoint(self, host_is_external) -> str:
        if self.ext_ip and (host_is_external or self.external == host_is_external):
            return f"endpoint {self.ext_ip}:{self.wg_port}"
        return ""

    def get_persistent_keepalive(self) -> str:
        if self.persistent_keepalive:
            return f"persistent-keepalive {self.persistent_keepalive}"
        return ""


peers = []
for _host, _hostdata in inventory.hosts.items():
    if (wg_ip := _hostdata.data.get("wireguard_addr", None)) is not None:
        peers.append(
            WgPeerData(
                host=_host,
                wg_ip=wg_ip,
                wg_port=_hostdata.data.get("wireguard_listenport", 51820),
                external=_hostdata.data.get("external", False),
                persistent_keepalive=_hostdata.data.get("persistent_keepalive", 25),
            )
        )

for peer in peers:
    pubkey_path = os.path.join(
        os.path.dirname(__file__), "wg_pubkeys", f"{peer.host}.pubkey"
    )
    if os.path.exists(pubkey_path):
        peer.pubkey = open(pubkey_path, mode="r").read().strip()
    for iface in interface_names:
        address_path = os.path.join(
            os.path.dirname(__file__), "wg_pubkeys", f"{peer.host}.address.{iface}"
        )
        if os.path.exists(address_path):
            if not peer.ext_ip:
                peer.ext_ip = open(address_path, mode="r").read().strip()

# with open("output.txt", mode="w") as f:
#     f.writelines(
#         ["; ".join([f"{k}: {v}" for k, v in peer.__dict__.items()]) for peer in peers]
#     )

# with open(f"output-{host}.txt", mode="w") as f:
#     f.writelines(
#         [
#             f"wg set wg0 peer {peer.pubkey} allowed-ips {peer.wg_ip} {peer.get_endpoint()} persistent-keepalive {persistent_keepalive}"
#             for peer in filter(lambda _host: _host.host != host, peers)
#         ]
#     )

if host.data.get("wireguard_addr", None):
    # Add all peers to device
    server.shell(
        _sudo=True,
        name="Configure peers",
        commands=[
            f"wg set wg0 peer {peer.pubkey} allowed-ips {peer.wg_ip} {peer.get_endpoint(host.data.get('external', False))} {peer.get_persistent_keepalive()}"
            for peer in filter(lambda _host: _host.host != host, peers)
        ],
    )
