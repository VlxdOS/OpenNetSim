"""Менеджер виртуальных машин QEMU.

Управляет жизненным циклом ВМ: запуск, остановка, автоматический
поиск свободных портов и настройка проброса (hostfwd) на 127.0.0.1.
"""

from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass


@dataclass
class RunningVM:
    """Описание запущенной виртуальной машины."""

    vm_id: str
    pid: int
    host_port: int  # порт на хосте для подключения (127.0.0.1:<host_port>)
    guest_ip: str  # внутренний IP в гостевой ОС


class QEmuManager:
    """Менеджер QEMU — запуск и управление ВМ."""

    BASE_PORT = 20001  # начальный порт для проброса

    def __init__(self) -> None:
        self._vms: dict[str, RunningVM] = {}

    @staticmethod
    def find_free_port(start_port: int = BASE_PORT) -> int:
        """Находит первый свободный порт начиная с ``start_port``."""
        port = start_port
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    port += 1
        raise RuntimeError("Не удалось найти свободный порт.")

    def start_vm(
        self, vm_id: str, image_path: str, guest_ip: str = "10.0.2.15"
    ) -> RunningVM:
        """Запускает ВМ с образом ``image_path`` и возвращает данные о ней."""
        host_port = self.find_free_port()
        process = subprocess.Popen(
            [
                "qemu-system-x86_64",
                "-m",
                "256",
                "-nic",
                f"user,model=e1000,hostfwd=tcp:127.0.0.1:{host_port}-{guest_ip}:8291",
                "-hda",
                image_path,
                "-display",
                "none",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        vm = RunningVM(
            vm_id=vm_id,
            pid=process.pid,
            host_port=host_port,
            guest_ip=guest_ip,
        )
        self._vms[vm_id] = vm
        return vm

    def stop_vm(self, vm_id: str) -> None:
        """Останавливает ВМ по идентификатору."""
        vm = self._vms.pop(vm_id, None)
        if vm is not None:
            try:
                import os
                import signal

                os.kill(vm.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

    def get_connection_info(self, vm_id: str) -> str:
        """Возвращает строку подключения вида ``127.0.0.1:<порт>``."""
        vm = self._vms.get(vm_id)
        if vm is None:
            raise KeyError(f"ВМ с id={vm_id} не найдена.")
        return f"127.0.0.1:{vm.host_port}"

    def list_vms(self) -> list[RunningVM]:
        """Возвращает список всех запущенных ВМ."""
        return list(self._vms.values())
