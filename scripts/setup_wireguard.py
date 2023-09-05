import os
from pyinfra import host, inventory
from pyinfra.operations import server, files
from pyinfra.facts.server import LinuxName

#####
# Check that we don't accidentally assign two nodes to the same address
addrs: set[str] = set()
for _, _hostdata in inventory.hosts.items():
    if (wg_ip := _hostdata.data.get("wireguard_addr", None)) is not None:
        cur_len = len(addrs)
        addrs.add(wg_ip.split("/")[0])  # add just the address
        assert len(addrs) - 2 == cur_len, "Two hosts share an IP assignment"


#####

# These are common 'primary' interfaces names
interface_names = ["enp1s0", "ens18", "eno0", "eth0", "eth1"]

persistent_keepalive = 25
listenport = host.data.get("wireguard_listenport", 51820)
wireguard_addr = host.data.get("wireguard_addr", None)
if wireguard_addr:
    server.packages(
        _sudo=True,
        name="Ensure wireguard is installed",
        packages=["wireguard"],
    )

    if host.get_fact(LinuxName) == "Ubuntu":
        server.shell(
            _sudo=True,
            name="Set UFW rules",
            commands=[f"ufw allow {listenport}/udp"],
        )

    files.directory(
        ".wg",
        present=True,
        mode="0700",
    )

    server.shell(
        name="Generate wireguard private/public keypair",
        commands=[
            "umask 077",
            "test -f .wg/private.key || wg genkey > .wg/private.key",
            "wg pubkey < .wg/private.key > .wg/public.key",
            *[
                (
                    f"ip addr show {eth}"
                    " | grep -P 'inet\s' | awk '{print $2}' | cut -d/ -f1 > "
                    f".wg/address.{eth}"
                )
                for eth in interface_names
            ],
        ],
    )

    server.shell(
        _sudo=True,
        name="Setup wireguard network interface",
        commands=[
            "ip l | grep 'wg0' || ip link add wg0 type wireguard",
            f"ip addr add dev wg0 {wireguard_addr}",
            f"ip link set up dev wg0",
        ],
    )

    server.shell(
        _sudo=True,
        name="Configure wireguard",
        commands=[
            "wg set wg0 private-key .wg/private.key",
            f"wg set wg0 listen-port {listenport}",
        ],
    )

    for iface in interface_names:
        files.get(
            name="Retrieve address from remote server",
            src=f".wg/address.{iface}",
            dest=os.path.join(
                os.path.dirname(__file__), "wg_pubkeys", f"{host}.address.{iface}"
            ),
        )

    files.get(
        name="Retrieve public key from remote server",
        src=".wg/public.key",
        dest=os.path.join(os.path.dirname(__file__), "wg_pubkeys", f"{host}.pubkey"),
    )
