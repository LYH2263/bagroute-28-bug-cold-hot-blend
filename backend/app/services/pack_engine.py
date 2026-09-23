"""Route-order bag packing with weight + volume caps; reject when exceed.

冷链规则：
- 冷链站只能装入冷链袋，非冷链站只能装入普通袋，冷热不混袋。
- 冷链站对照重量上限与更严的冷链体积上限。
- 非冷链站仍对照路线普通重量/体积双上限。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StopItem:
    stop_id: int
    seq: int
    weight_kg: float
    volume_l: float
    label: str = ""
    is_cold: bool = False


@dataclass
class Bag:
    bag_index: int
    items: list[StopItem] = field(default_factory=list)
    weight_kg: float = 0.0
    volume_l: float = 0.0
    is_cold: bool = False


@dataclass(frozen=True)
class PackResult:
    bags: list[Bag]
    rejects: list[tuple[StopItem, str]]


def can_fit(bag: Bag, item: StopItem, max_weight: float, max_volume: float) -> bool:
    return (
        bag.weight_kg + item.weight_kg <= max_weight + 1e-9
        and bag.volume_l + item.volume_l <= max_volume + 1e-9
    )


def pack_route(
    stops: list[StopItem],
    max_weight: float,
    max_volume: float,
    max_cold_volume: float | None = None,
) -> PackResult:
    cold_volume = max_cold_volume if max_cold_volume is not None else max_volume
    ordered = sorted(stops, key=lambda s: s.seq)
    bags: list[Bag] = []
    rejects: list[tuple[StopItem, str]] = []
    current: Bag | None = None

    for item in ordered:
        volume_cap = cold_volume if item.is_cold else max_volume
        if item.weight_kg > max_weight or item.volume_l > volume_cap:
            reason = []
            if item.weight_kg > max_weight:
                reason.append(f"超重 {item.weight_kg}>{max_weight}")
            if item.volume_l > volume_cap:
                if item.is_cold:
                    reason.append(f"冷链超体积 {item.volume_l}>{volume_cap}")
                else:
                    reason.append(f"超体积 {item.volume_l}>{volume_cap}")
            rejects.append((item, "；".join(reason)))
            continue

        # next-fit：只保留一个当前袋；放不下或温层不同才开新袋（新袋温层跟随首个装入的站点）
        if (
            current is None
            or current.is_cold != item.is_cold
            or not can_fit(current, item, max_weight, volume_cap)
        ):
            current = Bag(bag_index=len(bags) + 1, is_cold=item.is_cold)
            bags.append(current)

        if not can_fit(current, item, max_weight, volume_cap):
            rejects.append((item, "无法装入新袋"))
            continue

        current.items.append(item)
        current.weight_kg += item.weight_kg
        current.volume_l += item.volume_l

    return PackResult(bags=bags, rejects=rejects)
