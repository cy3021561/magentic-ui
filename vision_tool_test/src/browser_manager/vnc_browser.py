from __future__ import annotations

import asyncio
import logging
import time

from pathlib import Path
import secrets
import socket

from autogen_core import Component
import docker
import docker.errors
from docker.models.containers import Container
from pydantic import BaseModel

from .base_browser import DockerPlaywrightBrowser


# Configure logging
logger = logging.getLogger(__name__)


class VncDockerPlaywrightBrowserConfig(BaseModel):
    """
    Configuration for the VNC Docker Playwright Browser.
    """

    bind_dir: Path
    image: str = "magentic-ui-vnc-browser"
    playwright_port: int = 37367
    novnc_port: int = 6080
    playwright_websocket_path: str | None = None
    inside_docker: bool = False


class VncDockerPlaywrightBrowser(
    DockerPlaywrightBrowser, Component[VncDockerPlaywrightBrowserConfig]
):
    """
    A Docker-based Playwright browser implementation with VNC support for visual interaction.
    Provides both programmatic browser control via Playwright and visual access through noVNC.
    """

    component_config_schema = VncDockerPlaywrightBrowserConfig
    component_type = "browser"

    def __init__(
        self,
        *,
        bind_dir: Path,
        image: str = "magentic-ui-vnc-browser",
        playwright_port: int = 37367,
        playwright_websocket_path: str | None = None,
        novnc_port: int = 6080,
        inside_docker: bool = False,
        network_name: str = "bridge",
    ):
        super().__init__()
        self._bind_dir = bind_dir
        self._image = image
        self._playwright_websocket_path = (
            playwright_websocket_path or secrets.token_hex(16)
        )
        self._inside_docker = inside_docker
        self._network_name = network_name
        self._generate_new_browser_address()  # Always generate random ports
        self._hostname = "127.0.0.1"  # Force IPv4
        self._docker_name = f"magentic-ui-vnc-browser_{self._playwright_websocket_path}_{self._novnc_port}"

    def _get_available_port(self) -> tuple[int, socket.socket]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        return port, s

    def _generate_new_browser_address(self) -> None:
        """
        Generate new ports for Playwright and noVNC.
        """
        self._playwright_port, playwright_sock = self._get_available_port()
        self._novnc_port, novnc_sock = self._get_available_port()
        self._hostname = (
            f"magentic-ui-vnc-browser_{self._playwright_websocket_path}_{self._novnc_port}"
            if self._inside_docker
            else "localhost"
        )
        self._docker_name = f"magentic-ui-vnc-browser_{self._playwright_websocket_path}_{self._novnc_port}"
        playwright_sock.close()
        novnc_sock.close()

    @property
    def browser_address(self) -> str:
        """
        Get the address of the Playwright browser.
        """
        return f"ws://{self._hostname}:{self._playwright_port}/{self._playwright_websocket_path}"

    @property
    def vnc_address(self) -> str:
        """
        Get the address of the noVNC server.
        """
        return f"http://localhost:{self._novnc_port}/vnc.html"

    @property
    def novnc_port(self) -> int:
        """
        Get the port of the noVNC server.
        """
        return self._novnc_port

    @property
    def playwright_port(self) -> int:
        """
        Get the port of the Playwright server.
        """
        return self._playwright_port

    async def create_container(self) -> Container:
        """
        Start a headless Playwright browser using the official Playwright Docker image.
        """
        logger.info(
            f"Starting VNC Playwright browser on port {self._playwright_port} and VNC on {self._novnc_port}..."
        )

        client = docker.from_env()

        return await asyncio.to_thread(
            client.containers.create,
            name=self._docker_name,
            image=self._image,
            detach=True,
            auto_remove=True,  # Re-enable auto-remove now that issues are fixed
            network=self._network_name if self._inside_docker else None,
            ports={
                f"6080/tcp": ("127.0.0.1", self._novnc_port),
                f"{self._playwright_port}/tcp": ("127.0.0.1", self._playwright_port)
            },
            volumes={
                str(self._bind_dir.resolve()): {"bind": "/workspace", "mode": "rw"}
            },
            environment={
                "PLAYWRIGHT_WS_PATH": self._playwright_websocket_path,
                "PLAYWRIGHT_PORT": str(self._playwright_port),
            },
        )

    def stop(self):
        logger.info("Stopping VNC browser...")
        if self._container:
            try:
                self._container.stop(timeout=10)
                logger.info(f"Container {self._container.short_id} stopped.")
                self._container.remove()
                logger.info(f"Container {self._container.short_id} removed.")
            except docker.errors.NotFound:
                logger.warning(
                    f"Container {self._container.short_id} not found, it may have been stopped already."
                )
            except Exception as e:
                logger.error(f"Error stopping or removing container: {e}")
            finally:
                self._container = None
                # Give the OS a moment to release the network ports
                time.sleep(5)

    def _to_config(self) -> VncDockerPlaywrightBrowserConfig:
        return VncDockerPlaywrightBrowserConfig(
            bind_dir=self._bind_dir,
            image=self._image,
            playwright_port=self._playwright_port,
            novnc_port=self._novnc_port,
            playwright_websocket_path=self._playwright_websocket_path,
            inside_docker=self._inside_docker,
        )

    @classmethod
    def _from_config(
        cls, config: VncDockerPlaywrightBrowserConfig
    ) -> VncDockerPlaywrightBrowser:
        return cls(
            bind_dir=config.bind_dir,
            image=config.image,
            playwright_port=config.playwright_port,
            novnc_port=config.novnc_port,
            playwright_websocket_path=config.playwright_websocket_path,
            inside_docker=config.inside_docker,
        )

    @property
    def container_name(self) -> str:
        return self._docker_name
