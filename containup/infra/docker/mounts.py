from docker.types import Mount

from containup.stack.service_mounts import (
    BindMount,
    ServiceMounts,
    ServiceMount,
    TmpfsMount,
    VolumeMount,
)
from containup.utils.absolute_paths import to_absolute_path


def mounts_to_docker_specs(mount_list: ServiceMounts) -> list[Mount]:
    """Transforms service mounts into a list of Mount objects for the docker API"""
    result: list[Mount] = []
    for m in mount_list:
        result.append(mount_to_docker_specs(m))
    return result


def mount_to_docker_specs(mount: ServiceMount) -> Mount:
    """Transforms one service mount into a Mount object for the docker API"""
    if isinstance(mount, BindMount):
        return Mount(
            type="bind",
            source=to_absolute_path(mount.source),
            target=mount.target,
            read_only=False if mount.read_only is None else mount.read_only,
            consistency=mount.consistency,
            propagation=mount.propagation,
        )

    elif isinstance(mount, VolumeMount):
        return Mount(
            type="volume",
            source=mount.source,
            target=mount.target,
            read_only=False if mount.read_only is None else mount.read_only,
            consistency=mount.consistency,
            no_copy=mount.no_copy,
            labels=mount.labels,
            driver_config=mount.driver_config,
        )

    elif isinstance(mount, TmpfsMount):  # type: ignore
        return Mount(
            source=None,
            type="tmpfs",
            target=mount.target,
            read_only=False if mount.read_only is None else mount.read_only,
            consistency=mount.consistency,
            tmpfs_size=mount.tmpfs_size,
            tmpfs_mode=mount.tmpfs_mode,
        )

    else:
        raise TypeError(f"Unsupported mount type: {type(mount)}")
