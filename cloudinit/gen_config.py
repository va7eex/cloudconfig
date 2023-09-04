import base64
import os
from typing import Literal

import yaml
from pydantic import BaseModel


class DataSource(BaseModel):
    """
    https://cloudinit.readthedocs.io/en/latest/reference/datasources.html
    """

    url: str = "http://169.254.169.254"
    retries: int = 3
    timeout: int = 2
    wait: int = 2


class DigitalOcean(BaseModel):
    """Sets the key for the correct cloud provider."""

    DigitalOcean: DataSource = DataSource()


class Vultr(BaseModel):
    """Sets the key for the correct cloud provider."""

    Vultr: DataSource = DataSource()


class PowerState(BaseModel):
    """
    https://cloudinit.readthedocs.io/en/latest/reference/modules.html#power-state-change
    """

    delay: Literal["now"] | int = "now"
    mode: Literal["reboot", "shutdown"] = "reboot"
    message: str = "Rebooting machine"
    condition: bool | str = True


# apt:
#   sources:
#     docker.list:
#       source: "deb [arch=amd64] https://download.docker.com/linux/ubuntu $RELEASE stable"
#       keyid: FFFF0000 # Example GPG key ID


class Source(BaseModel):
    source: str
    keyid: str
    keyserver: str | None = None


class Apt(BaseModel):
    sources: dict[str, Source]


class User(BaseModel):
    """
    https://cloudinit.readthedocs.io/en/latest/reference/modules.html#users-and-groups
    """

    name: str
    shell: str = "/bin/bash"
    groups: list[str] | None = None
    sudo: list[str] | str | bool = False
    ssh_import_id: list[str] | str | None = None
    ssh_authorized_keys: list[str] | str | None = None


class NTP(BaseModel):
    """
    https://cloudinit.readthedocs.io/en/latest/reference/modules.html#ntp
    """

    enabled: bool = True
    pools: list[str] | None = None
    servers: list[str] | None = None
    peers: list[str] | None = None
    allow: list[str] | None = None


class FileObj(BaseModel):
    """
    https://cloudinit.readthedocs.io/en/latest/reference/modules.html#write-files
    """

    path: str
    content: str
    permissions: str
    owner: str = "root:root"
    encoding: str = "b64"

    @staticmethod
    def get_encoded_text(path: str) -> str:
        return base64.b64encode(open(path, mode="rb").read()).decode()

    @staticmethod
    def get_permissions(path: str) -> str:
        return str(oct(os.stat(path).st_mode))[-4:]


class Server(BaseModel):
    """
    Root model that we convert to yaml
    """

    users: list[User]
    write_files: list[FileObj]
    datasource: Vultr | DigitalOcean

    apt: Apt | None = None
    runcmd: list[list[str]] | None = None
    timezone: str = "America/Vancouver"
    package_update: bool = True
    package_upgrade: bool = True
    packages: list[str] | None = None
    ntp: NTP = NTP()
    resize_rootfs: bool = True
    power_state: PowerState = PowerState()
    final_message: str | None = "cloud-init has finished\nversion: $version\ntimestamp: $timestamp\ndatasource: $datasource\nuptime: $uptime"


#####
# Walk the rootdir/ directory for files, convert them to b64 and get permissions


def walk_dir(rootdir: str) -> list[str]:
    """
    Gets all files in a folder recursively
    """
    _files: list[str] = []
    for file in os.listdir(rootdir):
        file = os.path.join(rootdir, file)
        if os.path.isdir(file):
            _files.extend(walk_dir(file))
        else:
            _files.append(file)

    return _files


rootdir = os.path.join(os.path.dirname(__file__), "rootdir")
fileObjs = []
for f in walk_dir(rootdir):
    fileObjs.append(
        FileObj(
            path=f.replace(rootdir, ""),
            content=FileObj.get_encoded_text(f),
            permissions=FileObj.get_permissions(f),
        )
    )

######
# build our final model

server = Server(
    users=[
        User(
            name=os.getenv("CLOUDCONFIG_USER", "va7eex"),
            sudo=["ALL=(ALL) NOPASSWD:ALL"],
            ssh_import_id=["gh:va7eex"],
        )
    ],
    write_files=fileObjs,
    runcmd=[
        ["sudo", "rm", "/etc/ssh/sshd/50-cloud-init.conf"],
        ["sudo", "systemctl", "enable", "fail2ban.service"],
        ["sudo", "systemctl", "start", "fail2ban.service"],
        ["mkdir", "--mode=700", "~/.wg"],
        ["wg", "genkey", ">", "~/.wg/wg_private.key"],
        ["wg", "pubkey", "<", "~/.wg/wg_private.key", ">", "~/.wg/wg_public.key"],
    ],
    final_message=None,
    datasource=Vultr(),
    packages=[
        "fail2ban",
        "neofetch",
        "zsh",
        "wireguard",
        "python3",
        "python3-pip",
        "python-is-python3",
        "ca-certificates",
        "curl",
        "gnupg",
        "docker-ce",
        "docker-ce-cli",
        "containerd.io",
        "docker-buildx-plugin",
        "docker-compose-plugin",
    ],
    apt=Apt(
        sources={
            "docker.list": Source(
                source="deb [arch=amd64] https://download.docker.com/linux/ubuntu $RELEASE stable",
                keyid="9DC858229FC7DD38854AE2D88D81803C0EBFCD88",
            ),
        }
    ),
)

with open(
    os.path.join(
        os.path.dirname(__file__),
        "../output",
        "export_config.yml",
    ),
    mode="w",
) as wf:
    wf.write("#cloud-config\n")
    yaml.safe_dump(
        server.model_dump(mode="", exclude_none=True),
        wf,
        sort_keys=True,
        canonical=False,
    )
