from containup import (
    Stack,
    Service,
    Volume,
    Network,
    VolumeMount,
    port,
    BindMount,
    secret,
    CmdShellHealthcheck,
    HealthcheckOptions,
)


def test_networks():
    stack = create_n8n_stack()
    assert any(n.name == "n8n" for n in stack.networks)


def test_mounts():
    stack = create_n8n_stack()
    assert any(n.name == "pg_data" for n in stack.volumes)
    assert any(n.name == "n8n_data" for n in stack.volumes)
    assert any(n.name == "pgadmin_data" for n in stack.volumes)


def test_services():
    stack = create_n8n_stack()
    service = next(obj for obj in stack.services if obj.name == "n8n")
    assert service


def test_services_ordered():
    sorted = create_n8n_stack().get_services_sorted()
    names = [s.name for s in sorted]
    assert names == ["postgres", "n8n", "pgadmin", "traefik", "traefik-whoami"]


def test_services_ordered_filtered():
    sorted = create_n8n_stack().get_services_sorted(["traefik-whoami", "n8n"])
    names = [s.name for s in sorted]
    assert names == ["n8n", "traefik-whoami"]


def create_n8n_stack():
    stack = Stack("n8n-stack")
    stack.add(Network("n8n"))
    stack.add(Volume("pg_data"))
    stack.add(Volume("n8n_data"))
    stack.add(Volume("pgadmin_data"))
    stack.add(
        Service(
            name="postgres",
            image="postgres:17.5",
            environment={
                "POSTGRES_USER": "db_user",
                "POSTGRES_PASSWORD": secret("postgres password", "db_password"),
                "POSTGRES_DB": "dn_name",
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
    stack.add(
        Service(
            name="n8n",
            image="docker.n8n.io/n8nio/n8n:1.93.0",
            depends_on=["postgres"],
            environment={
                "DB_TYPE": "postgresdb",
                "DB_POSTGRESDB_HOST": "postgres",
                "DB_POSTGRESDB_PORT": "5432",
                "DB_POSTGRESDB_DATABASE": "dn_name",
                "DB_POSTGRESDB_USER": "db_user",
                "DB_POSTGRESDB_PASSWORD": secret("db_password", "db_password"),
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
            labels={"label1": "value1", "label2": "value2"},
        )
    )

    # pgAdmin (Admin interface for PostgreSQL)
    # This won't be launched in production or staging
    stack.add(
        Service(
            name="pgadmin",
            image="dpage/pgadmin4",
            environment={
                "PGADMIN_DEFAULT_EMAIL": "admin@example.com",
                "PGADMIN_DEFAULT_PASSWORD": secret(
                    "PGADMIN_DEFAULT_PASSWORD", "pgadmin_password"
                ),
            },
            volumes=[
                VolumeMount("pgadmin_data", "/var/lib/pgadmin"),
            ],
            network="n8n",
            ports=[port(container_port=80, host_port=5050)],
            labels={"label1": "value1", "label2": "value2"},
        )
    )
    # declare traefik-whoami before traefik to see if dependencies
    # are managed when getting service list ordered
    stack.add(
        Service(
            name="traefik-whoami",
            image="traefik/whoami",
            depends_on=["traefik"],
            network="n8n",
            labels={"label1": "value1", "label2": "value2"},
        )
    )
    stack.add(
        Service(
            name="traefik",
            image="traefik:v3.4",
            command=[
                "--api.insecure=true",
                "--providers.docker=true",
                "--entrypoints.web.address=:80",
                "--providers.docker.exposedbydefault=false",
            ],
            ports=[
                port(80, 80),
                port(8080, 8080),
            ],
            volumes=[BindMount("/var/run/docker.sock", "/var/run/docker.sock")],
            network="n8n",
        )
    )

    return stack
