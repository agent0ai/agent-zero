"""Tests for python/helpers/docker.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestDockerContainerManager:
    """Tests for DockerContainerManager."""

    def test_init_stores_params(self):
        """__init__ stores image, name, ports, volumes, logger."""
        with patch("python.helpers.docker.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client

            from python.helpers.docker import DockerContainerManager

            manager = DockerContainerManager(
                image="myimg",
                name="myname",
                ports={"80/tcp": 8080},
                volumes={"/host": {"bind": "/container", "mode": "rw"}},
                logger=MagicMock(),
            )
            assert manager.image == "myimg"
            assert manager.name == "myname"
            assert manager.ports == {"80/tcp": 8080}
            assert manager.volumes == {"/host": {"bind": "/container", "mode": "rw"}}
            assert manager.logger is not None

    def test_init_docker_connects_on_success(self):
        """init_docker connects to Docker and sets client."""
        with patch("python.helpers.docker.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client

            from python.helpers.docker import DockerContainerManager

            manager = DockerContainerManager(image="img", name="n")
            assert manager.client == mock_client
            assert manager.container is None

    def test_init_docker_retries_on_connection_refused(self):
        """init_docker retries when ConnectionRefusedError occurs."""
        with patch("python.helpers.docker.docker") as mock_docker:
            with patch("python.helpers.docker.format_error") as mock_fmt:
                mock_fmt.return_value = "ConnectionRefusedError(61, ...)"
                mock_docker.from_env.side_effect = [
                    ConnectionRefusedError(),
                    MagicMock(),
                ]
                with patch("python.helpers.docker.time.sleep"):
                    from python.helpers.docker import DockerContainerManager

                    manager = DockerContainerManager(image="img", name="n")
                    assert manager.client is not None

    def test_init_docker_raises_on_other_errors(self):
        """init_docker raises on non-connection errors."""
        with patch("python.helpers.docker.docker") as mock_docker:
            with patch("python.helpers.docker.format_error") as mock_fmt:
                mock_fmt.return_value = "SomeOtherError"
                mock_docker.from_env.side_effect = RuntimeError("other")

                from python.helpers.docker import DockerContainerManager

                with pytest.raises(RuntimeError):
                    DockerContainerManager(image="img", name="n")

    def test_cleanup_container_stops_and_removes(self):
        """cleanup_container stops and removes the container."""
        mock_container = MagicMock()

        with patch("python.helpers.docker.docker"):
            from python.helpers.docker import DockerContainerManager

            manager = DockerContainerManager(image="img", name="n")
            manager.container = mock_container

            manager.cleanup_container()

            mock_container.stop.assert_called_once()
            mock_container.remove.assert_called_once()

    def test_cleanup_container_handles_exception(self):
        """cleanup_container catches and logs exceptions."""
        mock_container = MagicMock()
        mock_container.stop.side_effect = RuntimeError("stop failed")

        with patch("python.helpers.docker.docker"):
            from python.helpers.docker import DockerContainerManager

            manager = DockerContainerManager(image="img", name="n", logger=MagicMock())
            manager.container = mock_container

            manager.cleanup_container()
            manager.logger.log.assert_called()

    def test_get_image_containers_returns_infos(self):
        """get_image_containers returns list of container infos."""
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.name = "c1"
        mock_container.status = "running"
        mock_container.image = "img:tag"
        mock_container.ports = {"80/tcp": [{"HostPort": "8080"}], "22/tcp": [{"HostPort": "2222"}]}

        with patch("python.helpers.docker.docker") as mock_docker:
            mock_client = MagicMock()
            mock_client.containers.list.return_value = [mock_container]
            mock_docker.from_env.return_value = mock_client

            from python.helpers.docker import DockerContainerManager

            manager = DockerContainerManager(image="img", name="n")
            manager.client = mock_client

            infos = manager.get_image_containers()
            assert len(infos) == 1
            assert infos[0]["id"] == "abc123"
            assert infos[0]["name"] == "c1"
            assert infos[0]["web_port"] == "8080"
            assert infos[0]["ssh_port"] == "2222"

    def test_start_container_starts_existing_stopped_container(self):
        """start_container starts existing stopped container."""
        mock_container = MagicMock()
        mock_container.name = "myname"
        mock_container.status = "exited"

        with patch("python.helpers.docker.docker") as mock_docker:
            mock_client = MagicMock()
            mock_client.containers.list.return_value = [mock_container]
            mock_docker.from_env.return_value = mock_client

            with patch("python.helpers.docker.time.sleep"):
                from python.helpers.docker import DockerContainerManager

                manager = DockerContainerManager(image="img", name="myname")
                manager.client = mock_client

                manager.start_container()

                mock_container.start.assert_called_once()
                assert manager.container == mock_container

    def test_start_container_uses_existing_running_container(self):
        """start_container uses existing running container without starting."""
        mock_container = MagicMock()
        mock_container.name = "myname"
        mock_container.status = "running"

        with patch("python.helpers.docker.docker") as mock_docker:
            mock_client = MagicMock()
            mock_client.containers.list.return_value = [mock_container]
            mock_docker.from_env.return_value = mock_client

            from python.helpers.docker import DockerContainerManager

            manager = DockerContainerManager(image="img", name="myname")
            manager.client = mock_client

            manager.start_container()

            mock_container.start.assert_not_called()
            assert manager.container == mock_container

    def test_start_container_runs_new_container_when_none_exists(self):
        """start_container runs new container when none exists."""
        with patch("python.helpers.docker.docker") as mock_docker:
            mock_client = MagicMock()
            mock_client.containers.list.return_value = []
            mock_client.containers.run.return_value = MagicMock()
            mock_docker.from_env.return_value = mock_client

            with patch("python.helpers.docker.time.sleep"):
                from python.helpers.docker import DockerContainerManager

                manager = DockerContainerManager(
                    image="img",
                    name="myname",
                    ports={"80/tcp": 8080},
                    volumes={"/x": {"bind": "/y", "mode": "rw"}},
                )
                manager.client = mock_client

                manager.start_container()

                mock_client.containers.run.assert_called_once_with(
                    "img",
                    detach=True,
                    ports={"80/tcp": 8080},
                    name="myname",
                    volumes={"/x": {"bind": "/y", "mode": "rw"}},
                )
