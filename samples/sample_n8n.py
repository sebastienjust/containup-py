#!/usr/bin/env python3
# fmt: off

import os

from containup import ( Stack, Service, Volume, Network, containup_run, VolumeMount, port, BindMount, secret, CmdShellHealthcheck, HealthcheckOptions )

# Sample script to demonstrate a how to build a stack with n8n
#
# The requirements:
# -----------------
#
# The stack is composed of : postgresql + pgadmin + traefik + traefik whoami + n8n.
#
# This example will manage a development, staging and production environment.
# - in development environments we want all the containers
# - in staging and production, no pgadmin, no whoami, more secure traefik
#
# Moreover the routes to access the services are not the same in dev, staging
# and production. As a special case, it's known that Linux users don't have
# access to *.docker.localhost. For them, they can use an environment variable
# to choose their base DNS.
#
# Passwords, in this example, are extracted from environment variables. We would
# have loved to show you a better alternative, but we don't know your tools :)
#
# Because it's python, You can easily fetch secrets them from AWS or
# any other secrets vault, even "gopass" in development.
#
# What you can see
# ================
#
# - run `python <this_script>.py up --dry-run`, you will be in "dev" mode.
# - then "export APP_ENV=staging" and run it again, you will see staging config
# - then "export APP_ENV=prod" and run it again to see production config.
#
# remove the --dry-run and it will launch for real.
#
# Note: for testing with a browser
# --------------------------------
#
# You can access the services using: http://<service>.<basedns>
#
# On "localhost" :
# - http://trafik.docker.localhost:8008
# - http://whoami.docker.localhost
# - http://n8n.docker.localhost
# - http://pgadmin.docker.localhost
#
# Linux users: you don't have access to "*.docker.localhost", please use
# do something like this : export DEPLOYMENT_DOMAIN_NAME=docker.local
# before launching the commands. Moreover, you'll have to change your
# /etc/hosts to add each DNS.
#
# Everybody: then you can add some DNS in your /etc/hosts to simulate
# staging and production environments.
#
# Examples:
#
# 127.0.0.1 n8n.mycompany.com
# 127.0.0.1 n8n.staging.mycompany.com
# 127.0.0.1 pgadmin.mycompany.com
# 127.0.0.1 pgadmin.staging.mycompany.com
#

# Fetch configuration
# ---------------------

# select environment from environment variable
app_env = os.environ.get("APP_ENV", "dev")

# users and passwords
dn_name = "n8n"
db_user = os.environ.get("DB_USER", "n8n")
db_password = os.environ.get("DB_PASSWORD", "n8n")
pgadmin_password = os.environ.get("PGADMIN_PASSWORD", "defaultpass")

# Define the routing logic
# ------------------------
# Select routing method depending on environment.
# Because it's code, you can create functions to avoid complex configuration

domain_name = (
    os.environ.get("DEPLOYMENT_DOMAIN_NAME") if os.environ.get("DEPLOYMENT_DOMAIN_NAME") else
    "docker.localhost" if app_env == "dev" else
    "staging.mycompany.com" if app_env == "staging" else
    "mycompany.com"
)
def routing(service: str) -> dict[str, str] :
    return {
        f"traefik.http.routers.{service}.rule" : f"Host(`{service}.{domain_name}`)",
        "traefik.enable": "true"
    }

# Create the stack
# ----------------

stack = Stack("n8n-stack")

# Networks
stack.add([
    Network("n8n")
])

# Persistent volumes
stack.add([
    Volume("pg_data"),
    Volume("n8n_data"),
    Volume("pgadmin_data"),
])

# Database PostgreSQL
stack.add(
    Service(
        name="postgres",
        image="postgres:17.5",
        environment={
            "POSTGRES_USER": db_user,
            "POSTGRES_PASSWORD": secret("postgres password", db_password),
            "POSTGRES_DB": dn_name,
        },
        volumes=[
            VolumeMount("pg_data", "/var/lib/postgresql/data"),
        ],
        network="n8n",
        ports=[port(container_port=5432)],
        healthcheck=CmdShellHealthcheck(
            "pg_isready -U n8n",
            HealthcheckOptions(interval="5s", timeout="3s", retries=5),
        ),
    )
)

# n8n
stack.add(
    Service(
        name="n8n",
        image="docker.n8n.io/n8nio/n8n:1.93.0",
        depends_on=["postgres"],
        environment={
            "DB_TYPE": "postgresdb",
            "DB_POSTGRESDB_HOST": "postgres",
            "DB_POSTGRESDB_PORT": "5432",
            "DB_POSTGRESDB_DATABASE": dn_name,
            "DB_POSTGRESDB_USER": db_user,
            "DB_POSTGRESDB_PASSWORD": secret("db_password", db_password),
            "GENERIC_TIMEZONE": "Europe/Paris",
            "TZ": "Europe/Paris",
            "N8N_LOG_LEVEL": "debug",
            "N8N_SECURE_COOKIE": "false",
            "N8N_PROXY_HOPS": "1",
        },
        volumes=[
            VolumeMount("n8n_data", "/home/node/.n8n"),
        ],
        network="n8n",
        ports=[port(container_port=5678, host_port=5678)],
        # Note: here you call the "routing" function defined earlier that
        # will generate all the labels depending on environment
        labels=routing("n8n"),
    )
)


if app_env == "dev":
    # pgAdmin (Admin interface for PostgreSQL)
    # This won't be launched in production or staging
    stack.add(
        Service(
            name="pgadmin",
            image="dpage/pgadmin4",
            environment={
                "PGADMIN_DEFAULT_EMAIL": "admin@example.com",
                "PGADMIN_DEFAULT_PASSWORD": secret(
                    "PGADMIN_DEFAULT_PASSWORD", pgadmin_password
                )
            },
            volumes=[
                VolumeMount("pgadmin_data", "/var/lib/pgadmin"),
            ],
            network="n8n",
            ports=[port(container_port=80, host_port=5050)],
            labels=routing("pgadmin"),
        )
    )

# Traefik (proxy)
stack.add(
    Service(
        name="traefik",
        image="traefik:v3.4",
        command=[
            # Activates only in dev
            "--api.insecure=true" if app_env == "dev" else "",
            # Tells Traefik to listen to docker
            "--providers.docker=true",
            "--entrypoints.web.address=:80",
            # Only containers with traefik.enable shall be exposed
            "--providers.docker.exposedbydefault=false",
        ],
        ports=[
            # The HTTP port
            port(80, 80),
            # The Web UI (if enabled by --api.insecure=true)
            port(8080, 8080),
        ],
        volumes=[BindMount("/var/run/docker.sock", "/var/run/docker.sock")],
        network="n8n",
    )
)

# Traefik whoami
# A container that exposes an API to show its IP address
# Only available in dev
if app_env == "dev":
    stack.add(
        Service(
            name="traefik-whoami",
            image="traefik/whoami",
            depends_on=["traefik"],
            network="n8n",
            labels=routing("whoami"),
        )
    )

# Run
# --------------------------
# Finally this will delegate command-line handling to containup
# and run everything you created.
# This is where command line is parsed and commands (like up, down) are
# evaluated and executed.
containup_run(stack)
