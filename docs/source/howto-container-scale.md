# How-to: Launch Multiple Instances of a Service

In some cases, you might want to run multiple containers of the same service —
for example, running 3 web workers, or scaling out a backend temporarily.

In Docker Compose, this is typically done using the `--scale` flag:

```bash
docker-compose up --scale web=3
```

This automatically creates three containers (`web_1`, `web_2`, `web_3`) based on the same service definition.

## How to do the same in `containup`

`containup` does not include a `scale` option — and that’s intentional.

Instead of relying on a dedicated option to repeat a container definition,
you can use native Python logic to express this pattern directly.
This gives you more control and flexibility over each instance.

### Basic example

```python
from containup import Stack, Service, port, containup_run

stack = Stack("mystack")

# Create 3 instances of the same service
for i in range(3):
    stack.add(Service(
        name=f"web_{i}",
        image="nginx:latest",
        ports=[port(inside=80, outside=8080 + i)]
    ))

containup_run(stack)
```

This launches:

- `web_0` on port `8080`
- `web_1` on port `8081`
- `web_2` on port `8082`

You can scale any number of instances this way, and adjust each instance
as needed.

## Why this approach?

Using a `for` loop in Python lets you:

- Choose custom names, ports, volumes for each container
- Add instance-specific environment variables or volumes
- Apply conditional logic (e.g. different configs in dev vs prod)
- Avoid hidden behavior
- Create helper functions to build stacks or fetch stack characteristics
  or scaling parameters from elsewhere in target environment.

There’s no extra abstraction to learn — it’s just regular Python code.
