from app.services.pack_engine import StopItem, pack_route


def test_packs_in_route_order_splitting_bags():
    stops = [
        StopItem(1, 1, 2.0, 3.0),
        StopItem(2, 2, 2.5, 3.0),
        StopItem(3, 3, 1.0, 1.0),
    ]
    result = pack_route(stops, max_weight=4.0, max_volume=10.0)
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1]
    assert [i.stop_id for i in result.bags[1].items] == [2, 3]
    assert not result.rejects


def test_reject_oversized_stop():
    stops = [StopItem(1, 1, 9.0, 1.0, "大件"), StopItem(2, 2, 1.0, 1.0)]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert len(result.rejects) == 1
    assert result.rejects[0][0].stop_id == 1
    assert len(result.bags) == 1
    assert result.bags[0].items[0].stop_id == 2


def test_volume_cap_triggers_new_bag():
    stops = [StopItem(1, 1, 1.0, 4.0), StopItem(2, 2, 1.0, 4.0)]
    result = pack_route(stops, max_weight=10.0, max_volume=5.0)
    assert len(result.bags) == 2


def test_cold_and_normal_stops_never_share_bag():
    # 顺序：普通、冷链、普通、冷链——每次类型切换都必须另开新袋
    stops = [
        StopItem(1, 1, 1.0, 1.0, "普通1", is_cold=False),
        StopItem(2, 2, 1.0, 1.0, "冷链1", is_cold=True),
        StopItem(3, 3, 1.0, 1.0, "普通2", is_cold=False),
        StopItem(4, 4, 1.0, 1.0, "冷链2", is_cold=True),
    ]
    result = pack_route(stops, max_weight=10.0, max_volume=10.0, max_cold_volume=10.0)
    assert len(result.bags) == 4
    assert all(len(b.items) == 1 for b in result.bags)
    assert [b.is_cold for b in result.bags] == [False, True, False, True]


def test_two_cold_stops_share_cold_bag_when_they_fit():
    # 两笔冷链合袋（与种子一致）
    stops = [
        StopItem(1, 1, 2.0, 3.0, "冷链A", is_cold=True),
        StopItem(2, 2, 2.0, 3.0, "冷链B", is_cold=True),
    ]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0, max_cold_volume=8.0)
    assert len(result.bags) == 1
    assert result.bags[0].is_cold is True
    assert [i.stop_id for i in result.bags[0].items] == [1, 2]
    assert not result.rejects


def test_cold_volume_cap_alone_rejects():
    # 冷链站体积超过冷链上限、但未超过普通上限——只能按冷链超体积拒收
    stops = [StopItem(1, 1, 2.0, 10.0, "冷链大件", is_cold=True)]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0, max_cold_volume=8.0)
    assert len(result.rejects) == 1
    item, reason = result.rejects[0]
    assert item.stop_id == 1
    assert "冷链超体积" in reason
    assert not result.bags


def test_same_volume_is_fine_for_normal_stop():
    # 同一笔体积（10L）对非冷链站完全合法：对照的是普通上限 18L
    stops = [StopItem(1, 1, 2.0, 10.0, "普通件", is_cold=False)]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0, max_cold_volume=8.0)
    assert not result.rejects
    assert len(result.bags) == 1
