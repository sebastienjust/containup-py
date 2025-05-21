from dataclasses import dataclass
from containup.business.audit.audit_alert import (
    AuditAlertType,
    AuditAlert,
    AuditAlertLocation,
)
from containup.business.audit.audit_report import AuditResult
from containup.business.live_state.stack_state import ContainerState
from containup.business.live_state.stack_state import VolumeState
from containup.business.live_state.stack_state import ImageState
from containup.business.live_state.stack_state import NetworkState
from containup.business.execution_listener import (
    ExecutionEvtContainer,
    ExecutionEvtContainerRemoved,
    ExecutionEvtContainerRun,
    ExecutionEvtImage,
    ExecutionEvtImagePull,
    ExecutionListener,
    ExecutionEvtNetwork,
    ExecutionEvtVolume,
    ExecutionEvtVolumeRemoved,
    ExecutionEvtVolumeCreated,
    ExecutionEvtNetworkRemoved,
    ExecutionEvtNetworkCreated,
)
from containup.business.live_state.stack_state import StackState
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
    state: StackState,
    live_operations: bool,
) -> str:
    lines: list[str] = []

    services_joined = ", ".join(config.services)
    services_annotated = f"[{services_joined}]" if services_joined else ""

    lines.append(
        f"🧱 Stack: {stack.name} (dry-run) {config.command} {services_annotated}\n"
    )

    volumes = stack.volumes
    networks = stack.networks

    max_key_len_volumes = max((len(n.name) for n in volumes), default=0)
    max_key_len_networks = max((len(n.name) for n in networks), default=0)
    max_key_len = max(max_key_len_volumes, max_key_len_networks)

    if volumes:
        lines.append("📦 Volumes")
        for volume in volumes:
            lines += report_volume(
                volume, execution_listener, max_key_len, state, live_operations
            )
        lines.append("")

    if networks:
        lines.append("🔗 Networks")
        for network in networks:
            lines += report_network(
                network, execution_listener, max_key_len, state, live_operations
            )
        lines.append("")

    lines.append("🚀 Containers\n")
    container_number: int = 0
    for container in stack.services:
        container_number += 1
        lines += report_container(
            container_number,
            container,
            execution_listener,
            audit_report,
            state,
            live_operations,
        )
        lines.append("")

    return "\n".join(lines)


class VolumeEvts:
    def __init__(self, volume_id: str, evts: list[ExecutionEvtVolume]):
        self.volume_id = volume_id
        self.evts = evts


def report_volume(
    volume: Volume,
    evts: ExecutionListener,
    max_key_len: int,
    state: StackState,
    live_operations: bool,
) -> list[str]:
    volume_evts: list[ExecutionEvtVolume] = []
    for evt in evts.get_events():
        if isinstance(evt, ExecutionEvtVolume) and evt.volume_id == volume.name:
            volume_evts.append(evt)
    line = f"  - {volume.name:<{max_key_len}} : " + " → ".join(
        volume_evt_summaries(
            state.get_volume_state(volume.name), volume_evts, live_operations
        )
    )
    return [line]


def report_network(
    network: Network,
    evts: ExecutionListener,
    max_key_len: int,
    state: StackState,
    live_operations: bool,
) -> list[str]:

    network_evts: list[ExecutionEvtNetwork] = []
    for evt in evts.get_events():
        if isinstance(evt, ExecutionEvtNetwork) and evt.network_id == network.name:
            network_evts.append(evt)
    line = f"  - {network.name:<{max_key_len}} : " + " → ".join(
        network_evt_summaries(
            state.get_network_state(network.name), network_evts, live_operations
        )
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
    image = ContainerItemKey("Image")
    container = ContainerItemKey("Container")

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
                else f"   {item_key.name:<{self.max_length}}:"
            )
            result.append(key + " " + value)
        return result


def report_container(
    container_number: int,
    c: Service,
    execution_listener: ExecutionListener,
    audit_report: AuditResult,
    state: StackState,
    live_operations: bool,
) -> list[str]:
    lines: list[str] = []

    item_names = ContainerItemNames()

    # Title (1. Container Name)

    container_number_fmt: str = "" + str(container_number) + "."

    container_state = state.get_container_state(c.container_name_safe())
    container_evts: list[ExecutionEvtContainer] = []
    for evt in execution_listener.get_events():
        if (
            isinstance(evt, ExecutionEvtContainer)
            and evt.container_id == c.container_name_safe()
        ):
            container_evts.append(evt)
    container_evt_summary = " → ".join(
        container_evt_summaries(container_state, container_evts, live_operations)
    )

    lines.append(f"{container_number_fmt:<2} {c.name}")
    if container_evt_summary:
        lines.extend(item_names.format(item_names.container, [container_evt_summary]))

    # Image

    image_evts: list[ExecutionEvtImage] = []
    for evt in execution_listener.get_events():
        if isinstance(evt, ExecutionEvtImage) and evt.image_id == c.image:
            image_evts.append(evt)

    image_evt_summary = " → ".join(
        image_evt_summaries(state.get_image_state(c.image), image_evts, live_operations)
    )
    image_lines = [c.image + " " + image_evt_summary]
    image_lines += tab_messages(
        to_formatted_alert_list(
            audit_report.query(AuditAlertLocation.service(c.name).image())
        )
    )

    lines.extend(item_names.format(item_names.image, image_lines))

    # Network

    if c.network:
        lines.extend(item_names.format(item_names.network, [c.network]))

    # Ports

    if c.ports:
        port_lines: list[str] = []
        for p in c.ports:
            if p.host_port:
                port_lines.append(f"{p.host_port}:{p.container_port}/{p.protocol}")
            else:
                port_lines.append(f"{p.container_port}/{p.protocol}")
        lines.extend(item_names.format(item_names.ports, [", ".join(port_lines)]))

    # Mounts (volumes)

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
            volume_lines += tab_messages(
                to_formatted_alert_list(audit_report.query(location))
            )
        lines.extend(item_names.format(item_names.mounts, volume_lines))

    # Environment variables

    if c.environment:
        environment_lines: list[str] = []
        for env_key, env_value in c.environment.items():
            location = AuditAlertLocation.service(c.name).environment(env_key)
            environment_lines.append(f"{env_key}={env_value}")
            environment_lines += tab_messages(
                to_formatted_alert_list(audit_report.query(location))
            )
        lines.extend(item_names.format(item_names.environment, environment_lines))

    # Dependencies

    for dependency_name in c.depends_on:
        depends_on_lines: list[str] = []
        depends_on_lines.append(dependency_name)
        location = AuditAlertLocation.service(c.name).depends_on(dependency_name)
        depends_on_lines += tab_messages(
            to_formatted_alert_list(audit_report.query(location))
        )
        lines.extend(item_names.format(item_names.depends_on, depends_on_lines))

    # Commands

    if c.command:
        cmd = " ".join(c.command)
        lines.extend(item_names.format(item_names.commands, [cmd]))

    # Healthcheck

    healthcheck = c.healthcheck
    name = None if healthcheck is None else healthcheck.summary()
    base_line = name
    healthcheck_lines = [base_line] + to_formatted_alert_list(
        audit_report.query(AuditAlertLocation.service(c.name).healthcheck())
    )
    healthcheck_lines_safe = [line for line in healthcheck_lines if line is not None]
    lines.extend(item_names.format(item_names.healthcheck, healthcheck_lines_safe))

    # Labels

    label_lines: list[str] = []
    for name, value in c.labels.items():
        label_lines.append(name + "=" + value)
    lines.extend(item_names.format(item_names.labels, label_lines))

    return lines


def container_evt_summaries(
    state: ContainerState, evts: list[ExecutionEvtContainer], live_operations: bool
) -> list[str]:
    summaries: list[str] = (
        []
        if not live_operations
        else [
            (
                "🟢 exists"
                if state == "exists"
                else "⚫ missing" if state == "missing" else "🟤 unknown"
            )
        ]
    )
    for evt in evts:
        if isinstance(evt, ExecutionEvtContainerRemoved):
            summaries.append("🔴 removed")
        elif isinstance(evt, ExecutionEvtContainerRun):
            summaries.append("🟢 run")
    return summaries


def image_evt_summaries(
    state: ImageState, evts: list[ExecutionEvtImage], live_operations: bool
) -> list[str]:
    summaries: list[str] = (
        []
        if not live_operations
        else [
            (
                "🟢 exists"
                if state == "exists"
                else "⚫ missing" if state == "missing" else "🟤 unknown"
            )
        ]
    )
    for evt in evts:
        if isinstance(evt, ExecutionEvtImagePull):
            summaries.append("📥 pulled")
    return summaries


def volume_evt_summaries(
    state: VolumeState, evts: list[ExecutionEvtVolume], live_operations: bool
) -> list[str]:
    summaries: list[str] = (
        []
        if not live_operations
        else [
            (
                "🟢 exists"
                if state == "exists"
                else "⚫ missing" if state == "missing" else "🟤 unknown"
            )
        ]
    )
    for evt in evts:
        if isinstance(evt, ExecutionEvtVolumeRemoved):
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


def network_evt_summaries(
    state: NetworkState, evts: list[ExecutionEvtNetwork], live_operations: bool
) -> list[str]:
    summaries: list[str] = (
        []
        if not live_operations
        else [
            (
                "🟢 exists"
                if state == "exists"
                else "⚫ missing" if state == "missing" else "🟤 unknown"
            )
        ]
    )
    for evt in evts:
        if isinstance(evt, ExecutionEvtNetworkRemoved):
            summaries.append("🔴 removed")
        elif isinstance(evt, ExecutionEvtNetworkCreated):
            details = f"driver={evt.network.driver}" if evt.network.driver else ""
            options = " ".join(
                [k + "=" + v for k, v in (evt.network.options or {}).items()]
            )
            summaries.append(f"🟢 created {details} {options}")
    return summaries


# -----------------------------------------------------------------------------
# Tabulations
# -----------------------------------------------------------------------------


def tab_messages(msg: list[str]) -> list[str]:
    return ["  " + message for message in msg]


# -----------------------------------------------------------------------------
# Alerts formatting
# -----------------------------------------------------------------------------


def to_formatted_alert_list(alerts: list[AuditAlert]) -> list[str]:
    return [to_formatted_alert(alert) for alert in alerts]


def to_formatted_alert(alert: AuditAlert) -> str:
    emoji_map = {
        AuditAlertType.CRITICAL: "❌",
        AuditAlertType.WARN: "⚠️ ",
        AuditAlertType.INFO: "🛈",
    }
    return (emoji_map[alert.severity] or "") + " " + alert.message
