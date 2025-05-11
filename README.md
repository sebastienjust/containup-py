# containup-py

Define and run Docker Compose-like stacks entirely in Python. Include your environment logic. No YAML.

> [!IMPORTANT]  
> This is under heavy development: project just started, API is subject to a lot
> of changes. Issues have been blocked and contribution is limited until
> a first usable version runs in production.

## Motivation

Docker Compose makes things simple: define services, volumes, networks in a YAML file, then run them.
But the moment you try to do anything dynamic — use secrets, switch images based on environments,
mount things conditionally — the model breaks.

You start adding .env files. Then you add envsubst or templating. Then you write shell scripts
to export variables, inject values, conditionally generate docker-compose.yml.
Then maybe you start using Makefiles or wrapper scripts. At some point, you’re not really “just
composing containers” anymore — you’re maintaining a brittle orchestration layer around Compose,
just to inject the right values into a rigid format. What was supposed to be a simple declarative
file becomes a small system of indirection and tooling.

IMHO, the paradox is this: Docker Compose is a static format trying to describe dynamic behavior.
But real-world deployments are dynamic: logic, context, secrets, runtime conditions.
So we build layers on top of YAML to simulate what a real programming language would do natively.

That's what containup-py solves (in my use-cases anyway), by taking the opposite approach.
It exposes a Python API designed to be declarative — so declarative, in fact, that your Python code
can look almost like Compose YAML:

```python
stack.service(ServiceCfg(
    name="db",
    image="postgres:15",
    volumes=["dbdata:/var/lib/postgresql/data"],
    networks=["backend"]
))
```

You write your stack in Python — a language you're already using, already good at, already documented.
You express logic directly. No interpolation, no templating, no escaping, no hacks.

But behind that simplicity, it’s real code. You can loop, branch, query, fetch secrets,
load configs — everything you already know how to do in Python.
The API stays close to the mental model of Compose, but frees you from its constraints.

```python
stack.service(ServiceCfg(
    name="db",
    image="myservice:latest",
    volumes=["myservice-data:/opt/application_data"],
    environment={
       "PG_PASSWORD": gopass("postgres/admin"),
       "PG_URL": myvault("where_is_postgres")
    }
    networks=["backend"]
))
stack.volume("myservice-data", external = True if dev else False)
```

This isn’t about replacing Compose. It’s about not having to build a custom orchestration layer around Compose just to support dynamic use cases.

## Usage

### Create your script and use containup

In any directory, create your file (we like to call them `containup-stack.py`
but it can be whatever you want).

Make the file executable if needed (`chmod u+x ./containup-stack.py`)

Make sure you install `containup`either globally on the machine :

```bash
pip install git+https://github.com/sebastienjust/containup-py.git
```

or with a local `venv` to not pollute the host with extra stuff.

```bash
python -m venv .venv
source .venv/bin/activate  # Unix/macOS
## .venv\Scripts\activate    # Windows
pip install --upgrade pip
pip install git+https://github.com/sebastienjust/containup-py.git
```

### Script example

```python
#!/usr/bin/env python3

# Elements to import
from containup import Stack, Service, Volume, Network, containup_cli

# Configure logging so you can have log output as you wish
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s [%(levelname)s] %(message)s"
)

# Tell containup to handle the command line. It will parse what it needs
# then give you back your own "extra arguments" in config.extra_args.
# Then, you can parse them with, for example with Python's argparse
config = containup_cli()

# This is your moment, your business logic. You grab what you need from your
# machine, remote services, command-line arguments, environment variables,
# whatever you need.
password = passwords.find("mybddpassword")

# Define your service, volumes, networks, like you do with docker-compose

# Create the stack (think of a docker-compose file)
stack = Stack("mystack", config)

# Then, add elements. Order doesn't matter

# If you need add one or more volumes (you can use "if", "for loops")
# Default behaviour is to create them if they not exist, or else, reuse them.
stack.add(Volume("dbdata", driver="local"))

# If you need add one or more networks (you can use "if", "for loops")
# Default behaviour is to create them if they not exist, or else, reuse them.
stack.add(Network("backend"))

# Describe your own services. Containup API syntax tries to stick with
# docker-compose naming and syntax, so you can guess what you need to do.
# Containup library is strongly typed: if you use Pylance for example,
# don't worry, your IDE will help autocompleting your code.
stack.add(Service(
    name="db",
    image="postgres:15",
    volumes=["dbdata:/var/lib/postgresql/data"],
    networks=["backend"]
))
stack.add(Service(
    name="app",
    image="myorg/myapp:latest",
    depends_on=["db"],
    networks=["backend"],
    environment={"DATABASE_URL": f"postgres://user:{password}@db:5432/db"}
))

# Now that we have the stack declared, we can run the commands on the stack
containup_run(stack, config)
```

### Use your script

```bash
# Starts everything
./containup-stack.py up
# Stops everything
./containup-stack.py down
# Starts only myservice
./containup-stack.py up myservice
# Stops only myservice
./containup-stack.py down myservice
# Get logs of myservice
./containup-stack.py logs myservice
# Starts everything and give yourself parameters
# you should not need a lot of parameters since your script can get what it
# needs programmatically.
./containup-stack.py up -- --myprofile=staging
```

## API usage

You can add elements to your stack in multiple ways:

```python
stack = Stack("mystack", config)
stack.add(Volume("myvolume1"))
stack.add(Volume("myvolume2"))
stack.add(Network("network1"))
stack.add(Network("network2"))
stack.add(Service(name="myservice",image="nginx:latest"))
```

or you can chain calls as `add` is a builder method:

```python
stack = Stack("mystack", config)
    .add(Volume("myvolume2"))
    .add(Volume("myvolume1"))
    .add(Network("network1"))
    .add(Network("network2"))
    .add(Service(name="myservice",image="nginx:latest"))
```

or add elements as lists:

```python
stack = Stack("mystack", config).add([
    Volume("myvolume1"),
    Volume("myvolume2"),
    Network("network1"),
    Network("network2"),
    Service(name="myservice",image="nginx:latest")
])
```

or a combination of everything:

```python
stack = Stack("mystack", config).add([
    Volume("myvolume1"),
    Volume("myvolume2"),
    Network("network1"),
]).add(
    Service(name="myservice",image="nginx:latest")
)

if something:
    stack.add(Network("network2"))

if other_thing:
    stack.add([
        Volume("monitoring_data"),
        Network("monitoring_network"),
        Service(name="monitoring")
    ])
```

## Project layout

This repo follows standard Python packaging practices:

```
containup-py/
  containup/
    __init__.py
    stack.py
    docker_interface.py
  pyproject.toml
  README.md
  LICENSE
```

## Development toolchain

This library uses the following tools:

| Tool       | Usage                      |
| ---------- | -------------------------- |
| ruff       | linter                     |
| black      | formatter                  |
| pyright    | static typing verification |
| pytest     | unit tests                 |
| pre-commit | pre-commit hooks           |

## License

This project is licensed under the GNU General Public License v3.0.
See the LICENSE file for details.
