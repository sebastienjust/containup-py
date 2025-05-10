# containup-py

Define and run Docker Compose-like stacks entirely in Python. Include your environment logic. No YAML.

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
stack.service(
    "db",
    image="postgres:15",
    volumes=["dbdata:/var/lib/postgresql/data"],
    networks=["backend"]
)
```

You write your stack in Python — a language you're already using, already good at, already documented. 
You express logic directly. No interpolation, no templating, no escaping, no hacks. 

But behind that simplicity, it’s real code. You can loop, branch, query, fetch secrets, 
load configs — everything you already know how to do in Python. 
The API stays close to the mental model of Compose, but frees you from its constraints.

```python
stack.service(
    "db",
    image="myservice:latest",
    volumes=["myservice-data:/opt/application_data"],
    environment={
       "PG_PASSWORD": gopass("postgres/admin"),
       "PG_URL": myvault("where_is_postgres")
    }
    networks=["backend"]
)
stack.volume("myservice-data", external = True if dev else False)
```

This isn’t about replacing Compose. It’s about not having to build a custom orchestration layer around Compose just to support dynamic use cases.

## Usage

Where you want to add your script, create your script, for example `containup.py`: 

```python
#!/usr/bin/env python3
from containup import Stack
from mypasswordservice import passwords
import sys

password = passwords.find("mybddpassword")

stack = Stack("mystack")
stack.volume("dbdata", driver="local")
stack.network("backend")
stack.service(
    "db",
    image="postgres:15",
    volumes=["dbdata:/var/lib/postgresql/data"],
    networks=["backend"]
)
stack.service(
    "app",
    image="myorg/myapp:latest",
    depends_on=["db"],
    networks=["backend"],
    environment={"DATABASE_URL": f"postgres://user:{password}@db:5432/db"}
)

def __main__(args):
    # here, delegate command line handling to containup
    stack.run(args)
```

Don't forget to add `containup-py` where your script shall live. 

```bash
python -m venv .venv
source .venv/bin/activate  # Unix/macOS
# .venv\Scripts\activate    # Windows

pip install --upgrade pip
pip install git+https://github.com/sebastienjust/containup-py.git
```

Run it with 

```
python3 stack.py up
```

stop with 

```
python3 stack.py up
```

or make it shorter (if you added shebang and chmod u+x the script)

```
./stack.py up
./stack.py down
./stack.py down myservice
./stack.py up myservice
./stack.py logs myservice
```
You can add any logic you want: fetch secrets, inspect the system, change parameters on the fly — it's just Python.

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

## License
This project is licensed under the GNU General Public License v3.0.
See the LICENSE file for details.
