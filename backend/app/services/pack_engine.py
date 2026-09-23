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


def volume_cap_for(item: StopItem, max_volume: float, max_cold_volume: float | None) -> float:
    """冷链站用更严的冷链体积上限；未配置冷链上限时回落到普通上限。"""
    if item.is_cold and max_cold_volume is not None:
        return max_cold_volume
    return max_volume


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
    ordered = sorted(stops, key=lambda s: s.seq)
    bags: list[Bag] = []
    rejects: list[tuple[StopItem, str]] = []
    current: Bag | None = None

    for item in ordered:
        volume_cap = volume_cap_for(item, max_volume, max_cold_volume)
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

        # 保持现网 next-fit 顺序：沿路线顺序只往当前袋装；
        # 冷热类型切换或当前袋装不下时，才封袋另开新袋。
        if (
            current is None
            or current.is_cold != item.is_cold
            or not can_fit(current, item, max_weight, volume_cap)
        ):
            current = Bag(bag_index=len(bags) + 1, is_cold=item.is_cold)
            bags.append(current)

        current.items.append(item)
        current.weight_kg += item.weight_kg
        current.volume_l += item.volume_l

    return PackResult(bags=bags, rejects=rejects)
