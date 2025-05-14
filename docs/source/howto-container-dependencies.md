# How-to: Handle container dependencies

In standard Docker Compose, you cannot explicitly wait for a service to finish
installation or initialization (or heathcheck) before starting others:
`depends_on` only controls **start order**, not **readiness**.

This often leads to race conditions if one service relies on another being fully ready.

However, with `containup`, which you're using, you can implement actual
logic in Python. That means you can:

1. Launch a service (e.g., a database).
2. Wait for it to be fully ready (e.g., by polling a port or making a health check request).
3. Then launch dependent services.

## Stategy 1: two stacks

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

stack_db = Stack("db-stack")

# Add the database first
stack_db.add(Service(name="db", image="postgres:15", ports=[5432]))

# Run stack so db starts
containup_run(stack_db)

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
