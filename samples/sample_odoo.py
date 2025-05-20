#!/usr/bin/env python3
# fmt: off

import os

from containup import ( Stack, Service, Volume, Network, containup_run, VolumeMount, port, BindMount, secret, CmdShellHealthcheck, HealthcheckOptions )

# Sample script to demonstrate a how to build a stack with Odoo
#
# The requirements:
# -----------------
#
# The stack is composed of: postgresql + pgadmin + traefik + traefik whoami + odoo.
#
# This example will manage a development, staging and production environment.
# - in development environments we want all the containers
# - in staging and production, no pgadmin, no whoami, more secure traefik
#
# Moreover the routes to access the services are not the same in dev, staging
# and production.
#
# - in development, devs can't configure hosts or DNS, so they will get
#   http://localhost/{service}
# - in staging, each domain has its DNS https://{service}.staging.mycompany.com
# - in production : https://{service}.mycompany.com
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
# Linux users: add this in /etc/hosts in Linux :
#
# 127.0.0.1 traefik.mycompany.com
# 127.0.0.1 traefik.staging.mycompany.com
# 127.0.0.1 whoami.mycompany.com
# 127.0.0.1 whoami.staging.mycompany.com
# 127.0.0.1 odoo.mycompany.com
# 127.0.0.1 odoo.staging.mycompany.com
# 127.0.0.1 pgadmin.mycompany.com
# 127.0.0.1 pgadmin.staging.mycompany.com
#
# If needed - for example, if you launch that in a VM -  replace 127.0.0.1
# with the real VM's IP adress.
#
# Testing the dev mode (no environment variable or APP_ENV=dev):
# - open http://localhost:8080 -> you have traefik admin console
# - open http://localhost/whoami -> you have traefik whoami
# - open http://localhost/pgadmin -> you have pgadmin
# - open http://localhost/odoo -> you have odoo
#
# Testing the staging mode (APP_ENV=staging)
# - http://traefik.staging.mycompany.com:8080 -> you have nothing (as expected)
# - http://whoami.staging.mycompany.com -> you have nothing (as expected)
# - http://pgadmin.staging.mycompany.com -> you have nothing (as expected)
# - http://odoo.staging.mycompany.com -> you have odoo
#
# Testing the prod mode (APP_ENV=staging)
# - http://traefik.mycompany.com:8080 -> you have nothing (as expected)
# - http://whoami.mycompany.com -> you have nothing (as expected)
# - http://pgadmin.mycompany.com -> you have nothing (as expected)
# - http://odoo.mycompany.com -> you have odoo


# Fetch configuration
# ---------------------

# select environment from environment variable
app_env = os.environ.get("APP_ENV", "dev")

# users and passwords
db_user = os.environ.get("DB_USER", "odoo")
db_password = os.environ.get("DB_PASSWORD", "odoo")
pgadmin_password = os.environ.get("PGADMIN_PASSWORD", "defaultpass")

# Define the routing logic
# ------------------------
# Select routing method depending on environment.
# Because it's code, can create functions to avoid complex configuration

def routing(service: str, strip: bool = True) -> dict[str, str] :

    if app_env == "dev":
        config = {
            f"traefik.http.routers.{service}.rule" : f"PathPrefix(`/{service}`)",
        }
        # if strip:
        #     config.update(
        #         {
        #             f"traefik.http.routers.{service}.middlewares" : f"{service}-stripprefix",
        #             f"traefik.http.middlewares.{service}-stripprefix.stripprefix.prefixes" : f"/{service}",
        #         }
        #     )
        return config

    subdomain = "mycompany.com" if app_env == "prod" else "staging.mycompany.com"
    return {
        "traefik.http.routers.{service}.rule" : f"Host(`{service}.{subdomain}`)"
    }

# Create the stack
# ----------------

stack = Stack("odoo-stack")

# Networks
stack.add([
    Network("odoo")
])

# Persistent volumes
stack.add([
    Volume("pg_data"),
    Volume("odoo_data"),
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
        labels=routing("odoo", strip = False),
    )
)


if app_env == "dev":
    # pgAdmin (Admin interface for PostgreSQL)
    #
    # only installed in development environment.
    # No access in staging or production
    stack.add(
        Service(
            name="pgadmin",
            image="dpage/pgadmin4",
            environment={
                "PGADMIN_DEFAULT_EMAIL": "admin@example.com",
                "PGADMIN_DEFAULT_PASSWORD": secret(
                    "PGADMIN_DEFAULT_PASSWORD", pgadmin_password
                ),
                # Necessary for pgadmin when used in a subdirectory
                # That happens in dev environments only
                "SCRIPT_NAME": "/pgadmin" if app_env == "dev" else "/"
            },
            volumes=[
                VolumeMount("pgadmin_data", "/var/lib/pgadmin"),
            ],
            network="odoo",
            ports=[port(container_port=80, host_port=5050)],
            labels=routing("pgadmin"),
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
            # Activates only in dev
            "--api.insecure=true" if app_env == "dev" else "",
            "--providers.docker=true",
            "--entrypoints.web.address=:80",
            "--providers.docker.exposedbydefault=true",
        ],
        ports=[
            # The HTTP port
            port(80, 80),
            # The Web UI (if enabled by --api.insecure=true)
            port(8080, 8080),
        ],
        volumes=[BindMount("/var/run/docker.sock", "/var/run/docker.sock")],
        network="odoo",
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
            network="odoo",
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
