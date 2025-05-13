from docker.types import Mount, DriverConfig

from containup import BindMount, VolumeMount, TmpfsMount
from containup.infra.docker.mounts import mount_to_docker_specs, mounts_to_docker_specs


def test_bind_mount():
    # Mount objects are just arbitrary dictionaries in Docker SDK
    m: Mount = mount_to_docker_specs(
        BindMount("/home/me/data", "/opt/data", True, "default", "private")
    )
    assert m["Source"] == "/home/me/data"
    assert m["Target"] == "/opt/data"
    assert m["Type"] == "bind"
    assert m["ReadOnly"] == True
    assert m["Consistency"] == "default"
    assert m["BindOptions"]["Propagation"] == "private"


def test_volume_mount():
    # Mount objects are just arbitrary dictionaries in Docker SDK
    m: Mount = mount_to_docker_specs(
        VolumeMount(
            source="volume_name",
            target="/opt/data",
            read_only=True,
            consistency="consistent",
            no_copy=True,
            labels={"label1": "value1", "label2": "value2"},
            driver_config=DriverConfig(
                name="mydriver",
                options={"option1": "optionValue1", "option2": "optionValue2"},
            ),
        )
    )
    assert m["Source"] == "volume_name"
    assert m["Target"] == "/opt/data"
    assert m["Type"] == "volume"
    assert m["ReadOnly"] == True
    assert m["Consistency"] == "consistent"
    assert m["VolumeOptions"]["NoCopy"] == True
    assert m["VolumeOptions"]["Labels"] == {"label1": "value1", "label2": "value2"}
    assert m["VolumeOptions"]["DriverConfig"]["Name"] == "mydriver"
    assert m["VolumeOptions"]["DriverConfig"]["Options"]["option1"] == "optionValue1"
    assert m["VolumeOptions"]["DriverConfig"]["Options"]["option2"] == "optionValue2"


def test_volume_tmpfs():
    # Mount objects are just arbitrary dictionaries in Docker SDK
    m: Mount = mount_to_docker_specs(
        TmpfsMount(
            target="/opt/data",
            read_only=True,
            consistency="cached",
            tmpfs_mode=770,
            tmpfs_size=123456,
        )
    )
    assert m["Source"] is None
    assert m["Target"] == "/opt/data"
    assert m["Type"] == "tmpfs"
    assert m["Consistency"] == "cached"
    assert m["TmpfsOptions"]["Mode"] == 770
    assert m["TmpfsOptions"]["SizeBytes"] == 123456


def test_list_empty():
    assert mounts_to_docker_specs([]) == []


def test_list_filled():
    lst = mounts_to_docker_specs(
        [
            BindMount("/home/me/data1", "/opt/data1", True, "default", "private"),
            VolumeMount(
                source="volume_name",
                target="/opt/data",
                read_only=True,
                consistency="consistent",
                no_copy=True,
                labels={"label1": "value1", "label2": "value2"},
                driver_config=DriverConfig(
                    name="mydriver",
                    options={"option1": "optionValue1", "option2": "optionValue2"},
                ),
            ),
        ]
    )
    first = lst[0]
    second = lst[1]

    assert first["Source"] == "/home/me/data1"
    assert first["Target"] == "/opt/data1"
    assert first["Type"] == "bind"

    assert second["Source"] == "volume_name"
    assert second["Target"] == "/opt/data"
    assert second["Type"] == "volume"
