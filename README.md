# containup

Define and run Docker Compose-like stacks entirely in Python. Include your environment logic. No YAML.

> [!IMPORTANT]  
> ⚠️ This project is under active development — the API may change frequently.

[![PyPI version](https://img.shields.io/pypi/v/containup)](https://pypi.org/project/containup/)
[![Downloads/month](https://static.pepy.tech/badge/containup/month)](https://pepy.tech/project/containup)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![CI](https://github.com/sebastienjust/containup-py/actions/workflows/python-publish.yml/badge.svg)](https://github.com/sebastienjust/containup-py/actions/workflows/python-publish.yml)

## Interested in containup?

- ⭐️ [Star the project](https://github.com/sebastienjust/containup-py) to follow updates.
- 👍 [React to this issue](https://github.com/sebastienjust/containup-py/issues/14) to signal interest.
- 💬 Feedback is very welcome! Feel free to open issues or
  react [here](https://github.com/sebastienjust/containup-py/issues/14) if you're interested.

This helps gauge whether the project is worth pushing further.

## Summary

😵‍💫 **Before**

* `docker-compose.yml` + `.env` + `bash` + `make` + `envsubst` + YAML templating
* Can't branch, can't loop, can't read a secret, can't debug
* One file per env, or one giant template nobody wants to touch
* Fragile chains of tools just to "start containers"
* You pray it works, you don't know what will run 
* "dev", "staging", "prod" — and 5 hacks per environment 🥵

> [!NOTE]
> Describing dynamic systems in static files that can’t even branch.
> What could go wrong? 🙃

😌 **After**

```python
dbpass = vault.get_password("db") if env == "prod" else gopass.get_password("dev_db")
stack.add(Service(name="db", image="postgres", environment={"PASS": secret(dbpass)}))
```

```bash
./stack.py up --dry-run   # ✅ dry-run to inspect → flaky images, secret access, env logic
./stack.py up             # 🚀 launch your stack
```

- 🧠 One Python script
- 🔁 Conditionals, loops, logic
- 🔐 Secrets, context-aware behavior
- 🧪 Testable, readable, controlled

**→ From YAML + hacks to real code you can trust.**
**No glue, no guessing, no mess.**

---

## Motivations

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
from containup import Service, Stack
Stack("mystack").add(Service(
    name="db",
    image="postgres:15",
    volumes=["dbdata:/var/lib/postgresql/data"],
    networks=["backend"]
))
```

You write your stack in Python — a language you're maybe already using,
already good at, already documented. And if you don't know Python, it doesn't
matter because the syntax you need for basic things is, in fact, no more
complicated than YAML.

You express logic directly. No interpolation, no templating, no escaping, no hacks.

But behind that simplicity, it’s real code. You can loop, branch, query, fetch secrets,
load configs — everything you already know, or can learn, in Python.
The API stays close to the mental model of Compose, but frees you from its constraints.

```python
from containup import Stack, Service, Volume
stack = Stack("mystack")
stack.add(Service(
    name="db",
    image="myservice:latest",
    volumes=["myservice-data:/opt/application_data"],
    environment={
        "PG_PASSWORD": gopass("postgres/admin"),
        "PG_URL": myvault("where_is_postgres")
    },
    networks = ["backend"]
))
stack.add(Volume("myservice-data", external=True if dev else False))
```
> [!NOTE]
> Containup isn’t a replacement for Compose — it’s what you reach for when Compose stops being enough.
> If your `docker-compose.yml` still works fine, keep using it.
> But when you start juggling `.env` files, `envsubst`, wrapper scripts, or conditionals across environments — that’s where Containup makes things simpler, not harder.

### Know what you do before launching

One key pain point with Compose — and container tooling in general — is that you
often don’t know exactly what’s going to be created until you run it.

In DevOps workflows, this lack of visibility is risky. You want a plan, not just a launch.

That’s why Containup includes a human-readable `--dry-run` mode: it shows exactly what would be 
created — volumes, networks, containers, ports — **and emits warnings** when something looks off: 
an image without a tag, a container without a healthcheck, a writable bind mount on a critical path…

## Usage

### Create your script and use containup

In any directory, create your file (we like to call them `containup-stack.py`
but it can be whatever you want).

Make the file executable if needed (`chmod u+x ./containup-stack.py`)

Make sure you install `containup`either globally on the machine :

```bash
pip install containup
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
from containup import Stack, Service, Volume, Network, containup_run, VolumeMount
import logging

# Configure logging so you can have log output as you wish
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s [%(levelname)s] %(message)s"
)

# This is your moment, your business logic. You grab what you need from your
# machine, remote services, command-line arguments, environment variables,
# whatever you need.
password = passwords.find("mybddpassword")

# Define your service, volumes, networks, like you do with docker-compose

# Create the stack (think of a docker-compose file)
stack = Stack("mystack")

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
    volumes=[VolumeMount("dbdata", "/var/lib/postgresql/data")],
    network="backend"
))
stack.add(Service(
    name="app",
    image="myorg/myapp:latest",
    depends_on=["db"],
    network="backend",
    environment={"DATABASE_URL": f"postgres://user:{password}@db:5432/db"}
))

# Now that we have the stack declared, we can run the commands on the stack
containup_run(stack)
```
### ☕ `--dry-run`

```bash
# Check everything
./containup-stack.py up --dry-run 
```

One recurring pain point in container workflows is this:  
You don’t know what will be created — until it’s already running.

Docker Compose doesn’t show you a plan. It just runs.  
You launch, then you find out what happened.

But DevOps needs visibility. Whether you're scripting a deployment, reviewing a config, 
debugging CI, or syncing with a teammate — you want to **see first, run second**.

Containup provides a `--dry-run` mode to do exactly that.
It prints a clean, readable preview of what the stack will create:
**volumes, networks, containers, ports, mounts, environment variables**, and more — without touching your system.

> [!TIP]
> The following example can be run immediately if you "git clone" this project (see instructions for checkout below): 

```text
$ python3 samples/sample_web_stack.py up --dry-run

🧱 Stack: odoo-stack (dry-run) up 

📦 Volumes
  - pgdata       : 🟢 created   
  - odoo_data    : 🟢 created   
  - pgadmin_data : 🟢 created   

🔗 Networks
  - frontend     : 🟢 created  
  - backend      : 🟢 created  

🚀 Containers

1. postgres (image: postgres:15)
   Network    : backend
   Ports      : 5432/tcp
   Volumes    : /var/lib/postgresql/data → (volume) pgdata (read-write) 
   Environment: POSTGRES_DB=postgres 
                POSTGRES_USER=odoo 
                POSTGRES_PASSWORD=<Secret: postgres password> 
   Healthcheck: {'pg_isready -U odoo'}

2. redis (image: redis:7)
   Network    : backend
   Ports      : 6379/tcp
   Healthcheck: 🛈 no healthcheck

3. odoo (image: odoo:16)
   Network    : backend
   Ports      : 8069:8069/tcp
   Volumes    : /var/lib/odoo → (volume) odoo_data (read-write) 
                /var/logs/odo → (bind) /opt/tmp/logs read-only 
   Environment: HOST=0.0.0.0 
                PORT=8069 
                USER=odoo 
                PASSWORD=defaultpass ❌ PASSWORD looks like a secret but is passed as plaintext — use containup.secret() to redact it safely
                PGHOST=postgres 
                PGUSER=odoo 
                PGPASSWORD=defaultpass ❌ PGPASSWORD looks like a secret but is passed as plaintext — use containup.secret() to redact it safely
   Healthcheck: 🛈 no healthcheck

4. pgadmin (image: dpage/pgadmin4 ❌  image has no explicit tag (defaults to :latest))
   Network    : frontend
   Ports      : 5050:80/tcp
   Volumes    : /var/lib/pgadmin → (volume) pgadmin_data (read-write) 
                /etc/postgresql → (bind) /etc/postgresql (read-write) ❌  sensitive host path, ⚠️  default to read-write, make it explicit
   Environment: PGADMIN_DEFAULT_EMAIL=admin@example.com 
                PGADMIN_DEFAULT_PASSWORD=defaultpass ❌ PGADMIN_DEFAULT_PASSWORD looks like a secret but is passed as plaintext — use containup.secret() to redact it safely
   Healthcheck: 🛈 no healthcheck

5. traefik (image: traefik:v2.10)
   Network    : frontend
   Ports      : 80:80/tcp, 8081:8080/tcp
   Healthcheck: 🛈 no healthcheck
   Commands   : --api.insecure=true
                --providers.docker=true
                --entrypoints.web.address=:80


```

> [!TIP]
> Un further releases, secrets will be redacted in reports 

#### What is this useful for?

`--dry-run` is more than a preview. It’s your **plan + linter** in one.

`--dry-run` is for humans.  It gives you a clear, shareable, verifiable view of what
Containup will do — before it does it.

You can use it to:

* debug and understand your stack logic,
* explain what will happen in a merge request or ops meeting,
* share a deployment plan with colleagues,
* validate changes in CI before they reach production,
* as DevOps, validate changes made by developers,
* as Developer, communicate with DevOps,
* catch mistakes like bad tags, dangerous mounts, or missing readiness checks,
* document in seconds.

In practice, this removes a common DevOps fear:

> *"If I run this, what exactly is it going to do?"*

Dry-run gives you the confidence to say: "Here’s what it will do, line by line."

#### What does it check?

Containup dry-run emits warnings when it sees patterns known to cause trouble:

* ❌ image has no tag (defaults to `:latest`)
* ⚠️ image uses unstable or vague tag (`dev`, `nightly`, etc.)
* ❌ bind mount over sensitive host path (`/etc`, `/var`, `/root`)
* ⚠️ bind mount is read-write by default — make it explicit
* 🛈 no healthcheck — Docker will consider the service healthy as soon as it starts

Upcoming (not in this release)
* ⚠️ port exposed without fixed host binding
* ❌ Environment variables with plaintext secrets

These checks don’t block anything. They just make the implicit explicit — so you can catch it early, 
and fix it while it’s still safe.


## ▶️ Use your script

```bash
# Starts everything
./containup-stack.py up
# Stops everything
./containup-stack.py down
# Starts only myservice
./containup-stack.py up --service myservice
# Stops only myservice
./containup-stack.py down --service myservice
# Starts everything and give yourself parameters
# you should not need a lot of parameters since your script can get what it
# needs programmatically.
./containup-stack.py up -- --myprofile=staging
```

## API usage

You can add elements to your stack in multiple ways:

```python
from containup import Stack, Service, Volume, Network, containup_run

stack = Stack("mystack")
stack.add(Volume("myvolume1"))
stack.add(Volume("myvolume2"))
stack.add(Network("network1"))
stack.add(Network("network2"))
stack.add(Service(name="myservice", image="nginx:latest"))
containup_run(stack)
```

or you can chain calls as `add` is a builder method:

```python
from containup import Stack, Service, Volume, Network, containup_run

stack = Stack("mystack").add(
    Volume("myvolume2")).add(
    Volume("myvolume1")).add(
    Network("network1")).add(
    Network("network2")).add(
    Service(name="myservice", image="nginx:latest"))
containup_run(stack)

```

or add elements as lists:

```python
from containup import Stack, Service, Volume, Network, containup_run

stack = Stack("mystack").add([
    Volume("myvolume1"),
    Volume("myvolume2"),
    Network("network1"),
    Network("network2"),
    Service(name="myservice", image="nginx:latest")
])
containup_run(stack)
```

or a combination of everything:

```python
from containup import Stack, Service, Volume, Network, containup_run

stack = Stack("mystack").add([
    Volume("myvolume1"),
    Volume("myvolume2"),
    Network("network1"),
]).add(
    Service(name="myservice", image="nginx:latest")
)

if something:
    stack.add(Network("network2"))

if other_thing:
    stack.add([
        Volume("monitoring_data"),
        Network("monitoring_network"),
        Service(name="monitoring")
    ])
containup_run(stack)
```

## Creating services tips and tricks

Mostly you will get help of IDE and you'll find everything you need in class Stack.

Some differences on things you may be used to:

### Service volume mapping

Docker manages 3 types of "volumes" :

- bind: maps one of the container's directory to your host in another directory
- volume: maps one of the container's directory to a Docker volume (a virtual hard disk)
- tmpfs: creates a temporary, in-memory, filesystem.

It's often unclear to know which parameters to use in which case. That's why
we declare those like this:

If the directory to map is a Docker volume, use VolumeMount

```python
from containup import Stack, Service, VolumeMount, Volume, containup_run

stack = Stack("yourstack")
stack.add(Volume("postgres-data"))
stack.add(Service(
    "postgres",
    image="postgres:17",
    volumes=[VolumeMount("postgres-data", "/var/lib/postgresql/data")]
))
containup_run(stack)
```

If the directory to map is your host's hard drive, it's bind:

```python
from containup import Stack, Service, BindMount, containup_run

Stack("yourstack").add(Service(
    "postgres",
    image="postgres:17",
    volumes=[BindMount("/home/mycomputer/postgres", "/var/lib/postgresql/data")]
))
containup_run(stack)
```

And for TmpFS

```python
from containup import Stack, Service, TmpfsMount, containup_run

stack = Stack("yourstack", config).add(Service(
    "postgres",
    image="postgres:17",
    volumes=[TmpfsMount("/var/lib/postgresql/data")]
))
containup_run(stack)
```

In each scenario, you can pass additional parameters, but only the parameters
that matches the type of mount.

### Port Mapping

To avoid confusion between the port "inside" the container (which needs to be
exposed) and the port "outside" the container (from which you can access the
container services), use explicit notation like this:

```python
from containup import Stack, Service, port, containup_cli, containup_run

stack = Stack("yourstack", config).add(Service(
    name="caddy",
    image="caddy:latest",
    ports=[
        port(container_port=80, host_port=8080),
        port(container_port=443, host_port=8443),
        port(container_port=9000),
    ],
))
containup_run(stack)
```

You have some small factory methods in containup you can use to create the port mappings,
use them to make your stack structure more readable.

You can also use the full `ServicePortMapping` class that allow precise configuration.

## How-to

- [Parse your own command line arguments](docs/source/howto-additional-comment-line-args.md)
- [Handle container inter-dependencies](docs/source/howto-container-dependencies.md)
- [Launch Multiple Instances of a Service (scale containers)](docs/source/howto-container-scale.md)

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

| Tool       | Usage                                 |
|------------|---------------------------------------|
| ruff       | linter                                |
| black      | formatter                             |
| pyright    | static typing verification            |
| pytest     | unit tests                            |
| pre-commit | pre-commit hooks                      |
| bumpver    | Bump version numbers in project files |

## Development external documentation

_Some bookmarks._

Docker documentation and specs:

- [Docker Engine API reference](https://docs.docker.com/reference/api/engine/)
- [Docker Engine API spec 1.49](https://docs.docker.com/reference/api/engine/version/v1.49/)
- [Docker Python SDK](https://docker-py.readthedocs.io/en/stable/index.html)
- [Docker Compose file Reference](https://docs.docker.com/reference/compose-file/)

## License

This project is licensed under the GNU General Public License v3.0.
See the LICENSE file for details.
