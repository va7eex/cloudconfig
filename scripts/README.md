# Pyinfra scripts

## Wireguard

Configure inventory with the follwoing keys:

```python
vps = [
    (
        "vps", # name of endpoint reachable by SSH (.ssh/config, /etc/hosts, DNS, IP address, etc)
        {
            "wireguard_addr": "wg.int.ad.dr/24", # internal IP of the wireguard tunnel
            "wireguard_listenport": 51820, # Port that the wireguard service will listen on
            "external": True, # can be true or false, won't the script won't specify an endpoint if an External host is peering to a non-External host..
        },
    ),
]
```

Run `pyinfra inventory_example.py setup_wireguard.py` this will configure all hosts specified in the inventory file to have a wireguard interface with their specific IP address. Hosts must have `wireguard_addr` configured for them to be in the deployment.

Run `pyinfra infentory_example.py setup_wireguard_peers.py` to distribute information of peers to each wireguard node.
