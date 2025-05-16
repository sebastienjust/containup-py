#!/usr/bin/env python3

import argparse

import boto3  # type: ignore

from containup import (
    Stack,
    Service,
    Volume,
    Network,
    containup_run,
    port,
    secret,
    VolumeMount,
    containup_cli,
    CmdHealthcheck,
    HealthcheckOptions,
)

# Parse command-line arguments
cli = containup_cli()
args = cli.extra_args
parser = argparse.ArgumentParser()
parser.add_argument("--env", default="dev", choices=["dev", "preprod", "prod"])
args, _ = parser.parse_known_args(args)

ENV = args.env


def get_aws_secret(secret_name: str) -> str:
    if cli.dry_run:
        return "dryrun-mode"
    client = boto3.client("secretsmanager", region_name="eu-west-1")  # type: ignore
    response = client.get_secret_value(SecretId=secret_name)  # type: ignore
    return response["SecretString"]  # type: ignore


def get_secret(key: str, fallback: str) -> str:
    if ENV == "prod":
        return get_aws_secret(f"sentry/{key}")
    return fallback


POSTGRES_PASSWORD = get_secret("db_password", "devpass")
RELAY_SECRET = get_secret("relay_secret", "devrelaysecret")

stack = Stack("sentry")

stack.add(Volume("sentry-data"))
stack.add(Volume("sentry-postgres"))
stack.add(Network("sentry-net"))

# PostgreSQL
stack.add(
    Service(
        name="postgres",
        image="postgres:15",
        volumes=[VolumeMount("sentry-postgres", "/var/lib/postgresql/data")],
        environment={
            "POSTGRES_USER": "sentry",
            "POSTGRES_PASSWORD": secret("POSTGRES_PASSWORD", POSTGRES_PASSWORD),
            "POSTGRES_DB": "sentry",
        },
        network="sentry-net",
        healthcheck=CmdHealthcheck(
            ["pg_isready", "-U", "sentry"],
            options=HealthcheckOptions(interval="10s", timeout="5s", retries=5),
        ),
    )
)

# Redis
stack.add(
    Service(
        name="redis",
        image="redis:7",
        network="sentry-net",
        healthcheck=CmdHealthcheck(
            ["redis-cli", "ping"],
            options=HealthcheckOptions(interval="10s", timeout="5s", retries=5),
        ),
    )
)

# Sentry Web
stack.add(
    Service(
        name="web",
        image="getsentry/sentry:23.4.0",
        environment={
            "SENTRY_SECRET_KEY": secret("SENTRY_SECRET_KEY", "dummysecret"),
            "SENTRY_REDIS_HOST": "redis",
            "SENTRY_POSTGRES_HOST": "postgres",
            "SENTRY_DB_USER": "sentry",
            "SENTRY_DB_PASSWORD": secret("SENTRY_DB_PASSWORD", POSTGRES_PASSWORD),
            "SENTRY_DB_NAME": "sentry",
        },
        depends_on=["postgres", "redis"],
        ports=[port(container_port=9000, host_port=9000)],
        network="sentry-net",
    )
)

# Cron
stack.add(
    Service(
        name="cron",
        image="getsentry/sentry:23.4.0",
        command=["sentry", "run", "cron"],
        depends_on=["postgres", "redis"],
        network="sentry-net",
    )
)

# Worker
stack.add(
    Service(
        name="worker",
        image="getsentry/sentry:23.4.0",
        command=["sentry", "run", "worker"],
        depends_on=["postgres", "redis"],
        network="sentry-net",
    )
)

# Relay
stack.add(
    Service(
        name="relay",
        image="getsentry/relay:latest",
        environment={
            "RELAY_RELAY_PORT": "3000",
            "RELAY_UPSTREAM": "http://web:9000/",
            "RELAY_SECRET_KEY": secret("RELAY_SECRET_KEY", RELAY_SECRET),
        },
        ports=[port(container_port=3000, host_port=3000)],
        network="sentry-net",
    )
)

# Symbolicator only in dev/preprod
if ENV != "prod":
    stack.add(
        Service(
            name="symbolicator",
            image="getsentry/symbolicator:latest",
            environment={"SYMBOLICATOR_LOG_LEVEL": "debug"},
            ports=[port(container_port=3021, host_port=3021)],
            network="sentry-net",
        )
    )

containup_run(stack)
