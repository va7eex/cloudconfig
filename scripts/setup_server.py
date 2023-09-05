from pyinfra import host
from pyinfra.operations import server, systemd, apt, pip
from pyinfra.facts.server import LinuxName

if host.get_fact(LinuxName) == "Ubuntu":
    apt.packages(
        _sudo=True,
        name="Ensure packages are installed",
        packages=[
            "fail2ban",
            "openssh-server",
            "python3",
            "python3-pip",
            "python-is-python3",
            "git",
        ],
        present=True,
        upgrade=True,
        update=True,
        latest=True,
    )

systemd.daemon_reload(
    _sudo=True,
    name="Reload the systemd daemon",
)

systemd.service(
    _sudo=True,
    name="Ensure fail2ban is operating",
    service="fail2ban.service",
    running=True,
    enabled=True,
)

systemd.service(
    _sudo=True,
    name="Ensure openssh-server has latest config",
    service="ssh.service",
    running=True,
    enabled=True,
    reloaded=True,
)

pip.packages(
    _sudo=True,
    packages=[
        "pipenv",
        "hatch",
        "black",
        "isort",
        "mypy",
        "mypy-extensions",
        "pytest",
        "pytest-cov",
        "pytest-html",
        "pyinfra",
    ],
    present=True,
    latest=True,
)
