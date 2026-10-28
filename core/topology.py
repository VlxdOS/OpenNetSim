"""Симуляционное ядро — хранилище состояния сети и расчёт пакетов.

Этот модуль отвечает за:
  - хранение топологии (устройства, интерфейсы, линки);
  - расчёт прохождения пакетов для «лёгкого» режима (без реального образа);
  - симуляцию базовых протоколов: ARP, ICMP (ping), статическая маршрутизация.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Interface:
    """Сетевой интерфейс устройства."""

    name: str
    ip_address: str | None = None
    mac_address: str | None = None


@dataclass
class Device:
    """Устройство в топологии."""

    id: str
    name: str
    device_type: str  # "router", "switch"
    vendor: str  # "MikroTik", "Huawei", ...
    interfaces: list[Interface] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "interfaces": [
                {
                    "name": iface.name,
                    "ip_address": iface.ip_address,
                    "mac_address": iface.mac_address,
                }
                for iface in self.interfaces
            ],
        }


@dataclass
class Link:
    """Физическая или логическая связь между двумя интерфейсами."""

    device_a: str
    interface_a: str
    device_b: str
    interface_b: str


@dataclass
class Topology:
    """Полное описание топологии сети."""

    devices: list[Device] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)

    def add_device(self, device: Device) -> None:
        self.devices.append(device)

    def add_link(self, link: Link) -> None:
        self.links.append(link)

    def to_dict(self) -> dict[str, Any]:
        return {
            "devices": [d.to_dict() for d in self.devices],
            "links": [
                {
                    "device_a": link.device_a,
                    "interface_a": link.interface_a,
                    "device_b": link.device_b,
                    "interface_b": link.interface_b,
                }
                for link in self.links
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Topology:
        topo = cls()
        for d in data.get("devices", []):
            device = Device(
                id=d["id"],
                name=d["name"],
                device_type=d["device_type"],
                vendor=d["vendor"],
                interfaces=[
                    Interface(
                        name=iface["name"],
                        ip_address=iface.get("ip_address"),
                        mac_address=iface.get("mac_address"),
                    )
                    for iface in d.get("interfaces", [])
                ],
            )
            topo.add_device(device)
        for link in data.get("links", []):
            topo.add_link(
                Link(
                    device_a=link["device_a"],
                    interface_a=link["interface_a"],
                    device_b=link["device_b"],
                    interface_b=link["interface_b"],
                )
            )
        return topo
