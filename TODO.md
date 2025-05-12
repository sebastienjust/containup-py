# 🚧 TODO Development

## Current

- 🟥 Unblock healthcheck logic

- 🟩 Rewamp how mounts and volumes are declared in Service

- 🟨 Redesign port mapping to remove confusion

  Port mapping is confusing in Docker, you never know which one is the host
  and other the container.

## Backlog

- 🟦 ⚠️ Improve container port syntax

- 🟦 ⚠️ Improve environment variable syntax

- 🟦 ⚠️ Improve network syntax

- 🟦 ⚠️ Improve healthcheck syntax

- 🟦 ⚠️ Improve restart syntax

- 🟦 🔥 Manage container build/rebuild process

- 🟦 🔥 Healthcheck should have an option to wait that service is healthy
  before continuing on other elements of the stack.

  This should allow managing dependencies between services.

- 🟦 ⚠️ Podman support

- 🟦 💤 Add more options for containers

- 🟦 💤 Add more options for networks

- 🟦 💤 Add more options for volumes

- 🟦 ❔ Export final configuration as static file

- 🟦 ❔ Implement docker-compose-like log streaming feature

- 🟦 ❔ Ability to launch more containers of the same type (`--scale web=3` for example)

  May be it's not useful since you can create loops in your script. You can just
  do a loop and create yourself the names of the containers, adjust exposed
  ports as you wish. Adding scaling options would bring us back to a static
  model.

  Maybe we should better explain that in documentation for example.

## Notation

Status

- 🟥 Selected for TODO
- 🟨 In progress
- 🟩 Done
- 🟦 Backlog
- ⬜ Undecided / Not yet defined

Priorities

- 🔥 Must (critical, blocking)
- ⚠️ Should (important but not blocking)
- 💤 Could (nice to have / ideas)
- 🚫 Won’t (won’t do, dropped)
- ❔ Undecided
