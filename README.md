# containup

**Write Compose-like stacks in Python — when static files fall short.**

Same Docker, same containers, same behaviour — just no more hacks around static YAML. Use real code instead.

> For developers and DevOps: when Compose YAML hits its limits, but Kubernetes is overkill.

Containup isn’t a replacement for Compose. It’s what you reach for when Compose isn’t enough anymore.  
- If your `docker-compose.yml` still does the job, stick with it. 
- But if you’ve added a `Makefile`, `envsubst`, or shell wrappers — maybe it’s no longer “simple”.
  That’s where Containup comes in: one file, your logic, no glue, no guessing.


[![PyPI version](https://img.shields.io/pypi/v/containup)](https://pypi.org/project/containup/)
[![Downloads/month](https://static.pepy.tech/badge/containup/month)](https://pepy.tech/project/containup)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![CI](https://github.com/sebastienjust/containup-py/actions/workflows/python-publish.yml/badge.svg)](https://github.com/sebastienjust/containup-py/actions/workflows/python-publish.yml)


> [!IMPORTANT]  
> ⚠️ This project is under active development — the API may change frequently.

## Summary

❌ With Compose YAML

- You need `.env`, `envsubst`, `shell`, `Makefiles`...
- Can’t branch, can’t loop, can’t fetch a secret
- Logic spread across files and scripts
- No preview of what will run

✅ With Containup

- One Python script — _your_ script, readable, testable, versionable
- Real logic — `if`, `for`, variables, secrets, external calls, reusability
- Safe preview — `--dry-run` with warnings and human reporting
- No glue, no guessing

🛠 Write it

```python
from containup import Stack, Service, containup_run
stack = Stack("demo").add(Service(name="web", image="nginx:alpine"))
containup_run(stack)
```

🚀 Run it

```bash 
./your-stack.py up --dry-run   # ✅ dry-run to inspect → flaky images, secret access, env logic
./your-stack.py up             # 🚀 launch your stack
```

> 🧠 Heads up  
> Containup is not a CLI. You don’t run containup.  
> You write and run your own Python script — `stack.py`. That’s your new Compose file.

## Try it now 

```
curl -sSL -o containup-try.sh https://raw.githubusercontent.com/sebastienjust/containup-py/main/installer/containup-try.sh && bash ./containup-try.sh 
```

🔥 Ready in 10s — launches an example of a full Odoo stack with PostgreSQL, Redis, Traefik, and pgAdmin.

Requires Python >= 3.9 + Docker installed and running on your machine.

Example source: [sample_web_stack.py](https://github.com/sebastienjust/containup-py/blob/main/samples/sample_web_stack.py)

This stack includes:
- Odoo 16, PostgreSQL, Redis, pgAdmin, Traefik
- Real environment variables and mounts
- Read-only paths and dry-run warnings

What you will see (condensed):

```
📦 Volumes: pgdata 🟢 created
🚀 Containers: postgres, redis, odoo, pgadmin, traefik
❌ Warning: bind mount on /etc/postgresql is read-write
```

--- 

## Interested in containup?

Want more?

- ⭐️ [Star the repo](https://github.com/sebastienjust/containup-py) to follow updates, 
- 💬 [Give feedback](https://github.com/sebastienjust/containup-py/issues/14) or suggest features.

---

## Motivations

Docker Compose is great for simple, static setups: define services, volumes, networks — and run.

But the moment you need logic — secrets, conditional mounts, environment-based configs — the model 
starts to break.

So you add `.env` files, then `sed`, `envsubst`, templating, wrapper scripts. A `Makefile`, maybe. 

At some point, you’re not describing a stack anymore — you’re managing the machinery around it.

What was supposed to be a simple declarative file becomes a small system of indirection and tooling.

> Describing dynamic systems in static files that can’t even branch. What could go wrong? 🙃

IMHO, the paradox is this: Docker Compose is a static format trying to describe dynamic behavior.
But real-world deployments are dynamic: logic, context, secrets, runtime conditions.
So we build layers on top of YAML to simulate what a real programming language would do natively.

> At some point, I was writing more shell than YAML.
> So I dropped the templates and wrote real code instead.
> It turned out simpler — and much easier to reason about.
> And since I wanted to reuse it, I turned it into a library: Containup.

That's what Containup solves (in my use-cases anyway), by taking the opposite approach.
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

You write your stack file in Python — a language you're maybe already using,
already good at, already documented. And **if you don't know Python, it doesn't
matter** because the syntax you need for basic things is, in fact, no more
complicated than YAML (and for sure `sed` or `awk` or anything like this).

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

### Know what you do before launching

> But I was still hesitant before running my stacks…
> What happens when someone else runs it in staging or production — when environments that “should be the same” aren’t, really?
> Can I simulate that locally? Can I see what will happen, before it actually does?
> That’s why I added a dry-run mode.

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
> Secrets, when declared with `secret()`, are reacted in reports, logs and exceptions. 

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
* ❌ conflicting mount paths
* ❌ relative mount paths
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
