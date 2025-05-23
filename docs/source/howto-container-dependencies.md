# How-to: Handle container inter-dependencies

In standard Docker Compose, you cannot explicitly wait for a service to finish
installation or initialization (or heathcheck) before starting others:
`depends_on` only controls **start order**, not **readiness**.

This often leads to race conditions if one service relies on another being fully ready.

However, with `containup`, which you're using, you can implement actual
logic in Python. That means you can:

1. Launch a service (e.g., a database).
2. Wait for it to be fully ready (e.g., by polling a port or making a health check request).
3. Then launch dependent services.

## Use health checks

An _internal_ health check is a health check that docker runs inside the container itself. 

Some image (not much) provide commands that you can run inside the container.

```python
from containup import (Stack, Service, CmdHealthcheck, HealthcheckOptions, port, containup_run, secret)

stack = Stack("db-stack")
user = "myapp"
stack.add(Service(
    name="sample-db",
    image="postgres:17",
    ports=[port(5432, 5432)],
    environment={
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": secret("dummy", "dummy"),
    },
    healthcheck=CmdHealthcheck(
        ["pg_isready", "-U", user],
        options=HealthcheckOptions(
            interval="10s", timeout="5s", retries=3, start_period="5s"
        ),
    ),
))

containup_run(stack)
```


Containup

## Use depends on





## Stategy: use external health checks



## Stategy: two stacks

Ok it's tricky but it does the job.

:::{warning}
Having two stacks in the same script may produce issus in further developments,
as we plan to have some additional tooling over stacks.
For the moment, we use it like this.

```python
from containup import Stack, Service, containup_run, containup_cli
import time
import socket

# Gets the command line parameters so we know which command is used
# We don't want to wait that database is ready if we do "down" or "logs"
config = containup_cli()

# You can check directly the database or use Docker SDK to check health
def wait_for_postgres(host, port, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("Postgres is ready!")
                return
        except Exception:
            print("Waiting for Postgres...")
            time.sleep(1)
    raise TimeoutError("Postgres did not become ready in time.")

stack = Stack("db-stack")
stack.add(Service(name="db", image="postgres:15", ports=[5432], healthcheck=ExternalHealthCheck(lambda: wait_for_postgres("localhost", 5432))))


# Wait for readiness
# But only if we do "up"
if config.command == "up":
    wait_for_postgres("localhost", 5432)

# Add and start the dependent services
stack_app = Stack("app-stack")
stack_app.add(Service(name="app", image="myapp:latest", depends_on=["db"]))
# Run the other part of the stack
containup_run(stack_app)
```

### Summary

With Docker Compose YAML — **no**, you can't wait for a service to be “ready.”
With `containup` — **yes**, because it's Python, you can program the wait logic however you want.
