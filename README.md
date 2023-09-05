# cloudconfig

Generates [cloud-init](https://cloudinit.readthedocs.io/en/latest/index.html) for provisioning new servers.

Also houses pyinfra projects to manage running servers.

To run:

```bash
pipenv install
pipenv run python cloudinit/gen_config.py # Generate a new config
cat output/export_config.yml  # Read the newly generated config from here
```
