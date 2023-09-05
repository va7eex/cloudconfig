vps = [
    (
        "vps",
        {
            "wireguard_addr": "1.2.3.4/24",
            "wireguard_listenport": 51820,
            "external": True,
        },
    ),
]

dev = [
    (
        "dev-server",
        {
            "wireguard_addr": "1.2.3.5/24",
            "wireguard_listenport": 51820,
            "external": False,
        },
    )
]
