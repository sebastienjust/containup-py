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
)
from containup.stack.service_healthcheck import CmdShellHealthcheck, HealthcheckOptions

# logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# Environment variables (for example from l'environnement)
app_env = os.environ.get("APP_ENV", "dev")
db_password = os.environ.get("DB_PASSWORD", "defaultpass")
odoo_password = os.environ.get("ODOO_PASSWORD", "defaultpass")
pgadmin_password = os.environ.get("PGADMIN_PASSWORD", "defaultpass")

stack = Stack("odoo-stack")

# Networks
stack.add(
    [
        Network("frontend"),
        Network("backend"),
    ]
)

# Persistent volumes
stack.add(
    [
        Volume("pgdata"),
        Volume("odoo_data"),
        Volume("pgadmin_data"),
    ]
)

# Database PostgreSQL
stack.add(
    Service(
        name="postgres",
        image="postgres:15",
        environment={
            "POSTGRES_DB": "postgres",
            "POSTGRES_USER": "odoo",
            "POSTGRES_PASSWORD": secret("postgres password", db_password),
        },
        volumes=[VolumeMount("pgdata", "/var/lib/postgresql/data")],
        network="backend",
        ports=[port(container_port=5432)],
        healthcheck=CmdShellHealthcheck(
            "pg_isready -U odoo",
            HealthcheckOptions(interval="5s", timeout="3s", retries=5),
        ),
    )
)

# Cache Redis (for Odoo)
stack.add(
    Service(
        name="redis",
        image="redis:7",
        network="backend",
        ports=[port(container_port=6379)],
    )
)

# Odoo (ERP)
stack.add(
    Service(
        name="odoo",
        image="odoo:16",
        # depends_on=["postgres", "redis"],
        environment={
            "HOST": "0.0.0.0",
            "PORT": "8069",
            "USER": "odoo",
            "PASSWORD": odoo_password,
            "PGHOST": "postgres",
            "PGUSER": "odoo",
            "PGPASSWORD": db_password,
        },
        volumes=[
            VolumeMount("odoo_data", "/var/lib/odoo"),
            BindMount("/opt/tmp/logs", "/var/logs/odo", read_only=True),
        ],
        network="backend",
        ports=[port(container_port=8069, host_port=8069)],
    )
)

# pgAdmin (Admin interface for PostgreSQL)
stack.add(
    Service(
        name="pgadmin",
        image="dpage/pgadmin4",
        environment={
            "PGADMIN_DEFAULT_EMAIL": "admin@example.com",
            "PGADMIN_DEFAULT_PASSWORD": pgadmin_password,
        },
        volumes=[
            VolumeMount("pgadmin_data", "/var/lib/pgadmin"),
            BindMount("/etc/postgresql", "/etc/postgresql"),
        ],
        network="frontend",
        ports=[port(container_port=80, host_port=5050)],
    )
)

# Traefik (proxy)
stack.add(
    Service(
        name="traefik",
        image="traefik:v2.10",
        command=[
            "--api.insecure=true",
            "--providers.docker=true",
            "--entrypoints.web.address=:80",
        ],
        ports=[
            port(container_port=80, host_port=80),
            port(container_port=8080, host_port=8081),  # UI traefik
        ],
        network="frontend",
    )
)

containup_run(stack)
