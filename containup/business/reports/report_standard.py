from dataclasses import dataclass
from containup.business.audit.audit_alert import (
    AuditAlertType,
    AuditAlert,
    AuditAlertLocation,
)
from containup.business.audit.audit_report import AuditResult
from containup.business.execution_listener import (
    ExecutionListener,
    ExecutionEvtNetwork,
    ExecutionEvtVolume,
    ExecutionEvtVolumeExistsCheck,
    ExecutionEvtVolumeRemoved,
    ExecutionEvtVolumeCreated,
    ExecutionEvtNetworkExistsCheck,
    ExecutionEvtNetworkRemoved,
    ExecutionEvtNetworkCreated,
)
from containup.containup_cli import Config
from containup.stack.network import Network
from containup.stack.service_mounts import BindMount, VolumeMount
from containup.stack.stack import Service, Stack
from containup.stack.volume import Volume


def report_standard(
    execution_listener: ExecutionListener,
    stack: Stack,
    config: Config,
    audit_report: AuditResult,
) -> str:
    lines: list[str] = []

    services_joined = ", ".join(config.services)
    services_annotated = f"[{services_joined}]" if services_joined else ""

    lines.append(
        f"🧱 Stack: {stack.name} (dry-run) {config.command} {services_annotated}\n"
    )

    volumes = [v for _, v in stack.mounts.items()]
    networks = [v for _, v in stack.networks.items()]

    max_key_len_volumes = max((len(n.name) for n in volumes), default=0)
    max_key_len_networks = max((len(n.name) for n in networks), default=0)
    max_key_len = max(max_key_len_volumes, max_key_len_networks)

    if volumes:
        lines.append("📦 Volumes")
        for volume in volumes:
            lines += report_volume(volume, execution_listener, max_key_len)
        lines.append("")

    if networks:
        lines.append("🔗 Networks")
        for network in networks:
            lines += report_network(network, execution_listener, max_key_len)
        lines.append("")

    lines.append("🚀 Containers\n")
    container_number: int = 0
    for container in stack.services:
        container_number += 1
        lines += report_container(container_number, container, audit_report)
        lines.append("")

    return "\n".join(lines)


class VolumeEvts:
    def __init__(self, volume_id: str, evts: list[ExecutionEvtVolume]):
        self.volume_id = volume_id
        self.evts = evts


def report_volume(
    volume: Volume, evts: ExecutionListener, max_key_len: int
) -> list[str]:
    volume_evts: list[ExecutionEvtVolume] = []
    for evt in evts.get_events():
        if isinstance(evt, ExecutionEvtVolume) and evt.volume_id == volume.name:
            volume_evts.append(evt)
    line = f"  - {volume.name:<{max_key_len}} : " + " → ".join(
        volume_evt_summaries(volume_evts)
    )
    return [line]


def report_network(
    network: Network, evts: ExecutionListener, max_key_len: int
) -> list[str]:
    network_evts: list[ExecutionEvtNetwork] = []
    for evt in evts.get_events():
        if isinstance(evt, ExecutionEvtNetwork) and evt.network_id == network.name:
            network_evts.append(evt)
    line = f"  - {network.name:<{max_key_len}} : " + " → ".join(
        network_evt_summaries(network_evts)
    )
    return [line]


@dataclass
class ContainerItemKey:
    name: str


class ContainerItemNames:
    network = ContainerItemKey("Network")
    ports = ContainerItemKey("Ports")
    mounts = ContainerItemKey("Mounts")
    environment = ContainerItemKey("Environment")
    healthcheck = ContainerItemKey("Healthcheck")
    depends_on = ContainerItemKey("Depends on")
    commands = ContainerItemKey("Commands")
    labels = ContainerItemKey("Labels")

    def __init__(self):
        self.max_length = self._container_item_names_max_length()
        key_empty = ""
        self.key_empty_formatted = f"   {key_empty:<{self.max_length}} "
        pass

    def _container_item_names_max_length(self):
        bigger = max(
            (
                v.name
                for k, v in vars(ContainerItemNames).items()
                if isinstance(v, ContainerItemKey) and not k.startswith("__")
            ),
            key=len,
        )
        return len(bigger)

    def format(self, item_key: ContainerItemKey, lines: list[str]) -> list[str]:
        result: list[str] = []
        for i, value in enumerate(lines):
            key = (
                self.key_empty_formatted
                if i > 0
                else f"    {item_key.name:<{self.max_length}}:"
            )
            result.append(key + " " + value)
        return result


def report_container(
    container_number: int, c: Service, audit_report: AuditResult
) -> list[str]:
    lines: list[str] = []

    item_names = ContainerItemNames()

    image_alerts_fmt = format_alerts_single_line(
        audit_report, AuditAlertLocation.service(c.name).image()
    )

    lines.append(
        f"{container_number}. {c.name} ({image_str(c.image, image_alerts_fmt)})"
    )
    if c.network:
        lines.extend(item_names.format(item_names.network, [c.network]))

    if c.ports:
        port_lines: list[str] = []
        for p in c.ports:
            if p.host_port:
                port_lines.append(f"{p.host_port}:{p.container_port}/{p.protocol}")
            else:
                port_lines.append(f"{p.container_port}/{p.protocol}")
        lines.extend(item_names.format(item_names.network, [", ".join(port_lines)]))

    if c.volumes:
        volume_lines: list[str] = []
        for vol in c.volumes:
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
            volume_lines.append(f"{vol.target} → ({vol.type()}) {source} {rw}")
            location = AuditAlertLocation.service(c.name).mount(vol.id)
            alerts = to_formatted_alert_list(audit_report.query(location))
            for alert in alerts:
                volume_lines.append(f"     {alert}")
        lines.extend(item_names.format(item_names.mounts, volume_lines))

    if c.environment:
        environment_lines: list[str] = []
        for env_key, env_value in c.environment.items():
            location = AuditAlertLocation.service(c.name).environment(env_key)
            alerts = to_formatted_alert_list(audit_report.query(location))
            environment_lines.append(f"{env_key}={env_value}")
            for alert in alerts:
                environment_lines.append(f"     {alert}")
        lines.extend(item_names.format(item_names.environment, environment_lines))

    for dependency_name in c.depends_on:
        depends_on_lines: list[str] = []
        depends_on_lines.append(dependency_name)
        location = AuditAlertLocation.service(c.name).depends_on(dependency_name)
        alerts = to_formatted_alert_list(audit_report.query(location))
        for alert in alerts:
            depends_on_lines.append(f"     {alert}")
        lines.extend(item_names.format(item_names.depends_on, depends_on_lines))

    if c.command:
        cmd = " ".join(c.command)
        lines.extend(item_names.format(item_names.commands, [cmd]))

    healthcheck = c.healthcheck
    name = None if healthcheck is None else healthcheck.summary()
    base_line = name
    healthcheck_lines = [base_line] + to_formatted_alert_list(
        audit_report.query(AuditAlertLocation.service(c.name).healthcheck())
    )
    healthcheck_lines_safe = [line for line in healthcheck_lines if line is not None]
    lines.extend(item_names.format(item_names.healthcheck, healthcheck_lines_safe))

    label_lines: list[str] = []
    for name, value in c.labels.items():
        label_lines.append(name + "=" + value)
    lines.extend(item_names.format(item_names.labels, label_lines))

    return lines


def format_alerts_single_line(
    audit_report: AuditResult, location: AuditAlertLocation
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
    return (emoji_map[alert.severity] or "") + "  " + alert.message


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


def image_str(image: str, image_alerts_fmt: str) -> str:
    return " ".join(part for part in ["image:", image, image_alerts_fmt] if part != "")
