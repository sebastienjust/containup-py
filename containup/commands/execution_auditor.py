import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TextIO

from containup.business.audit.audit_report import AuditReport
from containup.business.model.audit_alert import (
    AuditAlertType,
    AuditAlert,
    AuditAlertLocation,
)
from containup.containup_cli import Config
from containup.stack.network import Network
from containup.stack.service_mounts import BindMount, VolumeMount
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
    def flush(self, audit_report: AuditReport) -> None:
        pass


class StdoutAuditor(ExecutionAuditor):
    def __init__(self, stack: Stack, config: Config, stream: Optional[TextIO] = None):
        self._messages: list[ExecutionEvt] = []
        self._stream: TextIO = stream or sys.stdout
        self._stack = stack
        self._config = config

    def record(self, message: ExecutionEvt) -> None:
        self._messages.append(message)

    def flush(self, audit_report: AuditReport) -> None:
        print(
            _render_readable_summary(
                self._messages, self._stack, self._config, audit_report
            ),
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
    evts: list[ExecutionEvt], stack: Stack, config: Config, audit_report: AuditReport
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

        for env_value in evt_volumes:
            lines.append(
                f"  - {env_value.volume_id:<{max_key_len}} : "
                + " → ".join(volume_evt_summaries(env_value.evts))
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
                    read_only = vol.read_only
                    rw = (
                        "(read-write)"
                        if read_only is None
                        else "read-only" if read_only else "read-write"
                    )
                    lines.append(f"{key} {vol.target} → ({vol.type()}) {source} {rw}")
                    location = AuditAlertLocation.service(c.name).mount(vol.id)
                    alerts = to_formatted_alert_list(audit_report.query(location))
                    for alert in alerts:
                        lines.append(f"{key_empty_formatted}     {alert}")
            if c.environment:
                for i, (env_key, env_value) in enumerate(c.environment.items()):
                    key = key_environment_formatted if i == 0 else key_empty_formatted
                    location = AuditAlertLocation.service(c.name).environment(env_key)
                    alerts = to_formatted_alert_list(audit_report.query(location))
                    lines.append(f"{key} {env_key}={env_value}")
                    for alert in alerts:
                        lines.append(f"{key_empty_formatted}     {alert}")

            base_line = getattr(c.healthcheck, "command", "") if c.healthcheck else None
            healthcheck_lines = [base_line] + to_formatted_alert_list(
                audit_report.query(AuditAlertLocation.service(c.name).healthcheck())
            )
            healthcheck_lines_safe = [
                line for line in healthcheck_lines if line is not None
            ]

            for i, healtcheck_line in enumerate(healthcheck_lines_safe):
                key = key_healthcheck_formatted if i == 0 else key_empty_formatted
                lines.append(f"{key} {healtcheck_line}")

            if c.command:
                for i, cmd in enumerate(c.command):
                    key = key_commands_formatted if i == 0 else key_empty_formatted
                    lines.append(f"{key} {cmd}")
            lines.append("")

    return "\n".join(lines)


def format_alerts_single_line(
    audit_report: AuditReport, location: AuditAlertLocation
) -> str:
    alert_list = audit_report.query(location)
    alert_fmt_list = to_formatted_alert_list(alert_list)
    alert_msg = ", ".join(alert_fmt_list)
    return alert_msg


def to_formatted_alert_list(alerts: list[AuditAlert]) -> list[str]:
    return [to_formatted_alert(alert) for alert in alerts]


def to_formatted_alert(alert: AuditAlert) -> str:
    emoji_map = {
        AuditAlertType.CRITICAL: "❌",
        AuditAlertType.WARN: "⚠️",
        AuditAlertType.INFO: "🛈",
    }
    return (emoji_map[alert.severity] or "") + " " + alert.message


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
