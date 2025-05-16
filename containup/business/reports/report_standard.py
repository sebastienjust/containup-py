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


def report_container(
    container_number: int, c: Service, audit_report: AuditResult
) -> list[str]:
    lines: list[str] = []
    key_network = "Network"
    key_ports = "Ports"
    key_mounts = "Volumes"
    key_environment = "Environment"
    key_healthcheck = "Healthcheck"
    key_depends_on = "Depends on"
    key_commands = "Commands"
    key_empty = ""
    key_len = max(
        len(key_network),
        len(key_mounts),
        len(key_environment),
        len(key_healthcheck),
        len(key_depends_on),
        len(key_commands),
    )
    key_network_formatted = f"   {key_network:<{key_len}}:"
    key_ports_formatted = f"   {key_ports:<{key_len}}:"
    key_mounts_formatted = f"   {key_mounts:<{key_len}}:"
    key_environment_formatted = f"   {key_environment:<{key_len}}:"
    key_healthcheck_formatted = f"   {key_healthcheck:<{key_len}}:"
    key_commands_formatted = f"   {key_commands:<{key_len}}:"
    key_depends_on_formatted = f"   {key_depends_on:<{key_len}}:"
    key_empty_formatted = f"   {key_empty:<{key_len}} "

    image_alerts_fmt = format_alerts_single_line(
        audit_report, AuditAlertLocation.service(c.name).image()
    )
    lines.append(
        f"{container_number}. {c.name} ({image_str(c.image, image_alerts_fmt)})"
    )
    if c.network:
        lines.append(f"{key_network_formatted} {c.network}")
    if c.ports:
        port_lines: list[str] = []
        for p in c.ports:
            if p.host_port:
                port_lines.append(f"{p.host_port}:{p.container_port}/{p.protocol}")
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

    for i, dependency_name in enumerate(c.depends_on):
        key = key_depends_on_formatted if i == 0 else key_empty_formatted
        lines.append(f"{key} {dependency_name}")
        location = AuditAlertLocation.service(c.name).depends_on(dependency_name)
        alerts = to_formatted_alert_list(audit_report.query(location))
        for alert in alerts:
            lines.append(f"{key_empty_formatted}     {alert}")

    if c.command:
        cmd = " ".join(c.command)
        lines.append(f"{key_commands_formatted} {cmd}")

    healthcheck = c.healthcheck
    name = None if healthcheck is None else healthcheck.summary()
    base_line = name
    healthcheck_lines = [base_line] + to_formatted_alert_list(
        audit_report.query(AuditAlertLocation.service(c.name).healthcheck())
    )
    healthcheck_lines_safe = [line for line in healthcheck_lines if line is not None]

    for i, healtcheck_line in enumerate(healthcheck_lines_safe):
        key = key_healthcheck_formatted if i == 0 else key_empty_formatted
        lines.append(f"{key} {healtcheck_line}")

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
