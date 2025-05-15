import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TextIO, Union

from docker.types import Healthcheck

from containup.utils.secret_value import SecretValue
from containup.containup_cli import Config
from containup.stack.network import Network
from containup.stack.service_mounts import BindMount, VolumeMount
from containup.stack.service_mounts import ServiceMount
from containup.stack.stack import Service, Stack
from containup.stack.volume import Volume


@dataclass
class ExecutionEvt(ABC):
    pass


@dataclass
class ExecutionEvtVolume(ExecutionEvt):
    volume_id: str


@dataclass
class ExecutionEvtVolumeExistsCheck(ExecutionEvtVolume):
    volume_id: str
    exists: bool


@dataclass
class ExecutionEvtVolumeRemoved(ExecutionEvtVolume):
    volume_id: str


@dataclass
class ExecutionEvtVolumeCreated(ExecutionEvtVolume):
    volume_id: str
    volume: Volume


@dataclass
class ExecutionEvtContainer(ExecutionEvt):
    container_id: str


@dataclass
class ExecutionEvtContainerExistsCheck(ExecutionEvtContainer):
    container_id: str
    exists: bool


@dataclass
class ExecutionEvtContainerRemoved(ExecutionEvtContainer):
    container_id: str


@dataclass
class ExecutionEvtContainerRun(ExecutionEvtContainer):
    container_id: str
    container: Service


@dataclass
class ExecutionEvtNetwork(ExecutionEvt):
    network_id: str


@dataclass
class ExecutionEvtNetworkExistsCheck(ExecutionEvtNetwork):
    network_id: str
    exists: bool


@dataclass
class ExecutionEvtNetworkRemoved(ExecutionEvtNetwork):
    network_id: str


@dataclass
class ExecutionEvtNetworkCreated(ExecutionEvtNetwork):
    network_id: str
    network: Network


class ExecutionAuditor:
    @abstractmethod
    def record(self, message: ExecutionEvt) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass


class StdoutAuditor(ExecutionAuditor):
    def __init__(self, stack: Stack, config: Config, stream: Optional[TextIO] = None):
        self._messages: list[ExecutionEvt] = []
        self._stream: TextIO = stream or sys.stdout
        self._stack = stack
        self._config = config

    def record(self, message: ExecutionEvt) -> None:
        self._messages.append(message)

    def flush(self) -> None:
        print(
            _render_readable_summary(self._messages, self._stack, self._config),
            file=self._stream,
        )
        # for msg in self._messages:
        #     print(msg, file=self._stream)


class VolumeEvts:
    def __init__(self, volume_id: str, evts: list[ExecutionEvtVolume]):
        self.volume_id = volume_id
        self.evts = evts


@dataclass
class NetworkEvts:
    network_id: str
    evts: list[ExecutionEvtNetwork]


@dataclass
class ContainerEvts:
    container_id: str
    evts: list[ExecutionEvtContainer]


class AuditorError(Exception):
    pass


@dataclass
class GroupEvts:
    volumes: list[VolumeEvts]
    networks: list[NetworkEvts]
    containers: list[ContainerEvts]


def _group_evts(evts: list[ExecutionEvt]) -> GroupEvts:
    evts_volume: dict[str, list[ExecutionEvtVolume]] = {}
    evts_network: dict[str, list[ExecutionEvtNetwork]] = {}
    evts_container: dict[str, list[ExecutionEvtContainer]] = {}
    for evt in evts:
        if isinstance(evt, ExecutionEvtVolume):
            key = evt.volume_id
            evts_volume.setdefault(key, []).append(evt)
        elif isinstance(evt, ExecutionEvtNetwork):
            key = evt.network_id
            evts_network.setdefault(key, []).append(evt)
        elif isinstance(evt, ExecutionEvtContainer):
            key = evt.container_id
            evts_container.setdefault(key, []).append(evt)
        else:
            raise AuditorError(f"Unhandled event type {evt}")
    volume_evts: list[VolumeEvts] = [
        VolumeEvts(volume_id=k, evts=v) for k, v in evts_volume.items()
    ]
    network_evts: list[NetworkEvts] = [
        NetworkEvts(network_id=k, evts=v) for k, v in evts_network.items()
    ]
    container_evts: list[ContainerEvts] = [
        ContainerEvts(container_id=k, evts=v) for k, v in evts_container.items()
    ]

    return GroupEvts(volume_evts, network_evts, container_evts)


def _render_readable_summary(
    evts: list[ExecutionEvt], stack: Stack, config: Config
) -> str:
    evt_groups = _group_evts(evts)

    lines: list[str] = []

    services_joined = ", ".join(config.services)
    services_annotated = f"[{services_joined}]" if services_joined else ""

    lines.append(
        f"🧱 Stack: {stack.name} (dry-run) {config.command} {services_annotated}\n"
    )

    max_key_len_volumes = max((len(n.volume_id) for n in evt_groups.volumes), default=0)
    max_key_len_networks = max(
        (len(n.network_id) for n in evt_groups.networks), default=0
    )
    max_key_len = max(max_key_len_volumes, max_key_len_networks)

    evt_volumes: list[VolumeEvts] = evt_groups.volumes
    if evt_volumes:
        lines.append("📦 Volumes")

        for v in evt_volumes:
            lines.append(
                f"  - {v.volume_id:<{max_key_len}} : "
                + " → ".join(volume_evt_summaries(v.evts))
            )
        lines.append("")

    if evt_groups.networks:
        lines.append("🔗 Networks")
        for n in evt_groups.networks:
            lines.append(
                f"  - {n.network_id:{max_key_len}} : "
                + " → ".join(network_evt_summaries(n.evts))
            )
        lines.append("")

    if evt_groups.containers:
        lines.append("🚀 Containers\n")
        container_number: int = 0
        for container_evt in [
            container_evt
            for container_evts in evt_groups.containers
            for container_evt in container_evts.evts
            if isinstance(container_evt, ExecutionEvtContainerRun)
        ]:
            c: Service = container_evt.container
            container_number += 1

            key_network = "Network"
            key_ports = "Ports"
            key_mounts = "Volumes"
            key_environment = "Environment"
            key_healthcheck = "Healthcheck"
            key_commands = "Commands"
            key_empty = ""
            key_len = max(
                len(key_network),
                len(key_mounts),
                len(key_environment),
                len(key_healthcheck),
                len(key_commands),
            )
            key_network_formatted = f"   {key_network:<{key_len}}:"
            key_ports_formatted = f"   {key_ports:<{key_len}}:"
            key_mounts_formatted = f"   {key_mounts:<{key_len}}:"
            key_environment_formatted = f"   {key_environment:<{key_len}}:"
            key_healthcheck_formatted = f"   {key_healthcheck:<{key_len}}:"
            key_commands_formatted = f"   {key_commands:<{key_len}}:"
            key_empty_formatted = f"   {key_empty:<{key_len}} "

            lines.append(f"{container_number}. {c.name} ({image_str(c.image)})")
            if c.network:
                lines.append(f"{key_network_formatted} {c.network}")
            if c.ports:
                port_lines: list[str] = []
                for p in c.ports:
                    if p.host_port:
                        port_lines.append(
                            f"{p.host_port}:{p.container_port}/{p.protocol}"
                        )
                    else:
                        port_lines.append(f"{p.container_port}/{p.protocol}")
                lines.append(f"{key_ports_formatted} {', '.join(port_lines)}")
            if c.volumes:
                for i, vol in enumerate(c.volumes):
                    key = key_mounts_formatted if i == 0 else key_empty_formatted
                    source = (
                        vol.source
                        if isinstance(vol, BindMount)
                        else vol.source if isinstance(vol, VolumeMount) else ""
                    )
                    alerts = ", ".join(mount_alert(vol))
                    rw = (
                        "(read-write)"
                        if vol.read_only is None
                        else "read-only" if vol.read_only else "read-write"
                    )
                    lines.append(
                        f"{key} {vol.target} → ({vol.type()}) {source} {rw} {alerts}"
                    )
            if c.environment:
                for i, (k, v) in enumerate(c.environment.items()):
                    key = key_environment_formatted if i == 0 else key_empty_formatted
                    alerts = ", ".join(secrets_alerts(k, v))
                    lines.append(f"{key} {k}={v} {alerts}")
            healtcheck = (
                "🛈 no healthcheck"
                if c.healthcheck is None
                else {getattr(c.healthcheck, "command", "")}
            )
            lines.append(f"{key_healthcheck_formatted} {healtcheck}")

            if c.command:
                for i, cmd in enumerate(c.command):
                    key = key_commands_formatted if i == 0 else key_empty_formatted
                    lines.append(f"{key} {cmd}")
            lines.append("")

    return "\n".join(lines)


def volume_evt_summaries(evts: list[ExecutionEvtVolume]) -> list[str]:
    summaries: list[str] = []
    for evt in evts:
        if isinstance(evt, ExecutionEvtVolumeExistsCheck):
            pass
        elif isinstance(evt, ExecutionEvtVolumeRemoved):
            summaries.append("🔴 removed")
        elif isinstance(evt, ExecutionEvtVolumeCreated):
            labels = " ".join(
                [k + "=" + v for k, v in (evt.volume.labels or {}).items()]
            )
            driver = f"driver={evt.volume.driver}" if evt.volume.driver else ""
            options = " ".join(
                [k + "=" + v for k, v in (evt.volume.driver_opts or {}).items()]
            )
            summaries.append(f"🟢 created {labels} {driver} {options}")
    return summaries


def network_evt_summaries(evts: list[ExecutionEvtNetwork]) -> list[str]:
    summaries: list[str] = []
    for evt in evts:
        if isinstance(evt, ExecutionEvtNetworkExistsCheck):
            pass
        elif isinstance(evt, ExecutionEvtNetworkRemoved):
            summaries.append("🔴 removed")
        elif isinstance(evt, ExecutionEvtNetworkCreated):
            details = f"driver={evt.network.driver}" if evt.network.driver else ""
            options = " ".join(
                [k + "=" + v for k, v in (evt.network.options or {}).items()]
            )
            summaries.append(f"🟢 created {details} {options}")
    return summaries


def image_str(image: str) -> str:
    alert = image_tag_alert(image)
    return " ".join(part for part in ["image:", image, alert] if part is not None)


def image_tag_alert(image: str) -> Optional[str]:
    """Returns a warning if the image uses a risky tag (latest, implicit, unstable)."""

    risky_tags = {"latest", "dev", "nightly", "snapshot", "beta", "alpha", "rc"}
    emoji_map = {
        "latest": "❌",
        "implicit": "❌",
        "unstable": "⚠️",
    }

    if ":" not in image:
        return (
            f"{emoji_map['implicit']}  image has no explicit tag (defaults to :latest)"
        )

    _, tag = image.rsplit(":", 1)

    if tag == "latest":
        return f"{emoji_map['latest']}  image uses tag :latest"

    if tag in risky_tags:
        return f"{emoji_map['unstable']}  image uses unstable tag :{tag}"

    if not any(char.isdigit() for char in tag):
        return f"{emoji_map['unstable']}  image tag is vague :{tag}"

    return None


def secrets_alerts(k: str, v: Union[str, SecretValue]) -> list[str]:
    alerts: list[str] = []
    secret_like_keys = {"password", "token", "secret", "key", "pwd", "pass"}
    lowered = k.lower()
    if any(hint in lowered for hint in secret_like_keys):
        if not isinstance(v, SecretValue):
            alerts.append(
                f"❌ {k} looks like a secret but is passed as plaintext — use containup.secret() to redact it safely"
            )

    return alerts


def mount_alert(mount: ServiceMount) -> list[str]:
    """Returns alerts on mount"""

    alerts: list[str] = []
    if isinstance(mount, BindMount):
        for prefix in ["etc", "var", "home", "root"]:
            if mount.source.startswith("/" + prefix):
                alerts.append("❌  sensitive host path")
        if mount.read_only is None:
            alerts.append("⚠️  default to read-write, make it explicit")

    return alerts


def healthcheck_alerts(healthcheck: Optional[Healthcheck]) -> list[str]:
    """Returns alerts on healthcheck"""
    alerts: list[str] = []
    if healthcheck is None:
        alerts.append("⚠️  no health check")
    return alerts
