from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import DeliveryRoute, SubscriberStop

# 冷链样例：r1 冷链体积上限 8L（严于普通 18L）
# - 鲜奶自提柜 10L：超过冷链上限 8L、但未超过普通上限 18L，应按冷链超体积拒收
# - 烘焙工坊冷柜 / 社区食堂冷库：两笔冷链合袋（合计 6L / 4kg）
COLD_EXAMPLES = [
    ("城东晨线", 6, "鲜奶自提柜", 2.0, 10.0),
    ("城东晨线", 7, "烘焙工坊冷柜", 2.0, 3.0),
    ("城东晨线", 8, "社区食堂冷库", 2.0, 3.0),
]


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(DeliveryRoute.id).limit(1)):
        _seed_cold_examples(db)
        return
    r1 = DeliveryRoute(
        name="城东晨线", max_weight_kg=8.0, max_volume_l=18.0, max_cold_volume_l=8.0
    )
    r2 = DeliveryRoute(
        name="园区午线", max_weight_kg=6.0, max_volume_l=14.0, max_cold_volume_l=6.0
    )
    db.add_all([r1, r2])
    db.flush()
    db.add_all(
        [
            SubscriberStop(route_id=r1.id, seq=1, name="松林里 3 栋", weight_kg=2.2, volume_l=4.0),
            SubscriberStop(route_id=r1.id, seq=2, name="梧桐苑门岗", weight_kg=3.5, volume_l=5.5),
            SubscriberStop(route_id=r1.id, seq=3, name="地铁口快递柜", weight_kg=1.8, volume_l=3.0),
            SubscriberStop(route_id=r1.id, seq=4, name="超大件样例", weight_kg=9.5, volume_l=6.0),
            SubscriberStop(route_id=r1.id, seq=5, name="咖啡店后门", weight_kg=2.0, volume_l=4.5),
            SubscriberStop(route_id=r1.id, seq=6, name="鲜奶自提柜", weight_kg=2.0, volume_l=10.0, is_cold=True),
            SubscriberStop(route_id=r1.id, seq=7, name="烘焙工坊冷柜", weight_kg=2.0, volume_l=3.0, is_cold=True),
            SubscriberStop(route_id=r1.id, seq=8, name="社区食堂冷库", weight_kg=2.0, volume_l=3.0, is_cold=True),
            SubscriberStop(route_id=r2.id, seq=1, name="A 座前台", weight_kg=1.5, volume_l=3.0),
            SubscriberStop(route_id=r2.id, seq=2, name="B 座茶水间", weight_kg=2.0, volume_l=4.0),
            SubscriberStop(route_id=r2.id, seq=3, name="地下车库岗亭", weight_kg=2.8, volume_l=5.0),
        ]
    )
    db.commit()


def _seed_cold_examples(db: Session) -> None:
    """幂等补插冷链样例（旧库升级时）；样例已存在则不动用户改过的上限。"""
    existing = set(db.scalars(select(SubscriberStop.name)).all())
    missing = [e for e in COLD_EXAMPLES if e[2] not in existing]
    if not missing:
        return
    routes = {r.name: r for r in db.scalars(select(DeliveryRoute)).all()}
    for route_name, seq, name, weight, volume in missing:
        route = routes.get(route_name)
        if route is None:
            continue
        # 首次补插时落成种子冷链上限；用户之后修改不会被覆盖（样例已在即跳过）
        route.max_cold_volume_l = 8.0
        db.add(
            SubscriberStop(
                route_id=route.id,
                seq=seq,
                name=name,
                weight_kg=weight,
                volume_l=volume,
                is_cold=True,
            )
        )
    db.commit()
