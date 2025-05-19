#!/usr/bin/env python3

import os

from containup import (
    Stack,
    Service,
    Volume,
    Network,
    containup_run,
    VolumeMount,
    port,
    BindMount,
    secret,
    CmdShellHealthcheck,
    HealthcheckOptions,
)

# Sample script to demonstrate a stack with Odoo
#
# To be able to test this stack, you need to add in your /etc/hosts
#
# 192.168.122.179 traefik.docker.local
# 192.168.122.179 whoami.docker.local
# 192.168.122.179 odoo.docker.local
# 192.168.122.179 pgadmin.docker.local
#
# (and replace 192.168.122.179 with 127.0.0.1 or your own server IP)
#
# Then you can go to :
# - http://traefik.docker.local:8080
# - http://whoami.docker.local
# - http://odoo.docker.local
# - http://pgadmin.docker.local


# Environment variables

db_user = "odoo"
db_password = os.environ.get("DB_PASSWORD", "odoo")
pgadmin_password = os.environ.get("PGADMIN_PASSWORD", "defaultpass")
app_env = os.environ.get("APP_ENV", "dev")


stack = Stack("odoo-stack")

# Networks
stack.add(
    [
        Network("odoo"),
    ]
)

# Persistent volumes
stack.add(
    [
        Volume("pg_data"),
        Volume("odoo_data"),
        Volume("pgadmin_data"),
    ]
)

# Database PostgreSQL
stack.add(
    Service(
        name="postgres",
        image="postgres:17.5",
        environment={
            "POSTGRES_USER": db_user,
            "POSTGRES_PASSWORD": secret("postgres password", db_password),
            "POSTGRES_DB": "postgres",
        },
        volumes=[VolumeMount("pg_data", "/var/lib/postgresql/data")],
        network="odoo",
        ports=[port(container_port=5432)],
        healthcheck=CmdShellHealthcheck(
            "pg_isready -U odoo",
            HealthcheckOptions(interval="5s", timeout="3s", retries=5),
        ),
    )
)

# Odoo (ERP)
stack.add(
    Service(
        name="odoo",
        image="odoo:18",
        depends_on=["postgres"],
        environment={
            "HOST": "postgres",
            "PORT": "5432",
            "USER": db_user,
            "PASSWORD": secret("db_password", db_password),
        },
        volumes=[
            VolumeMount("odoo_data", "/var/lib/odoo"),
        ],
        network="odoo",
        ports=[port(container_port=8069, host_port=8069)],
        labels={"traefik.http.routers.odoo.rule": "Host(`odoo.docker.local`)"},
    )
)

# pgAdmin (Admin interface for PostgreSQL)
stack.add(
    Service(
        name="pgadmin",
        image="dpage/pgadmin4",
        environment={
            "PGADMIN_DEFAULT_EMAIL": "admin@example.com",
            "PGADMIN_DEFAULT_PASSWORD": secret(
                "PGADMIN_DEFAULT_PASSWORD", pgadmin_password
            ),
        },
        volumes=[
            VolumeMount("pgadmin_data", "/var/lib/pgadmin"),
        ],
        network="odoo",
        ports=[port(container_port=80, host_port=5050)],
        labels={"traefik.http.routers.pgadmin.rule": "Host(`pgadmin.docker.local`)"},
    )
)

# Traefik (proxy)
stack.add(
    Service(
        name="traefik",
        # The official v3 Traefik docker image
        image="traefik:v3.4",
        # Enables the web UI and tells Traefik to listen to docker
        command=[
            "--api.insecure=true",
            "--providers.docker=true",
            "--entrypoints.web.address=:80",
            "--providers.docker.exposedbydefault=true",
        ],
        ports=[
            # The HTTP port
            port(80, 80),
            # The Web UI (enabled by --api.insecure=true)
            port(8080, 8080),
        ],
        volumes=[BindMount("/var/run/docker.sock", "/var/run/docker.sock")],
        network="odoo",
    )
)

# Traefik whoami
# A container that exposes an API to show its IP address

stack.add(
    Service(
        name="traefik-whoami",
        image="traefik/whoami",
        depends_on=["traefik"],
        network="odoo",
        labels={
            "traefik.http.routers.traefik-whoami.rule": "Host(`whoami.docker.local`)"
        },
    )
)

containup_run(stack)
