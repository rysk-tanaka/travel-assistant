#!/usr/bin/env python3
"""
交通手段別調整のデモンストレーション

各交通手段でどのような持ち物が追加されるかを確認するスクリプト。
"""

import sys

sys.path.insert(0, ".")

from src.core.transport_rules import TransportRulesLoader


def extract_additional_conditions(params: dict[str, any]) -> dict[str, any]:
    """パラメータから追加条件を抽出する."""
    additional_conditions = {}

    # 条件のキーリスト
    condition_keys = ["is_shinkansen", "is_rental", "is_highway", "night_bus"]

    for key in condition_keys:
        if key in params:
            additional_conditions[key] = params.pop(key)

    # 距離の推定
    if params["duration"] >= 2:
        additional_conditions["long_distance"] = True
        if params["transport_method"] == "car":
            additional_conditions["distance"] = 200

    return additional_conditions


def print_trip_details(
    title: str, params: dict[str, any], items: list, loader: TransportRulesLoader
) -> None:
    """旅行の詳細と持ち物を表示する."""
    print(f"\n🎯 {title}")
    print("-" * 40)

    print(f"📍 目的地: {params['destination']}")
    print(f"🚗 交通手段: {params['transport_method']}")
    print(f"📅 期間: {params['duration']}泊{params['duration'] + 1}日")
    print(f"🗓️ 月: {params['month']}月")

    # 追加条件がある場合は表示
    if params.get("additional_conditions"):
        print(f"🔧 追加条件: {params['additional_conditions']}")

    print(f"\n📋 追加される持ち物 ({len(items)}個):")

    # カテゴリ別に整理
    categories = {}
    for item in items:
        if item.category not in categories:
            categories[item.category] = []
        categories[item.category].append(item)

    for category, category_items in categories.items():
        print(f"\n  【{category}】")
        for item in category_items:
            print(f"    ✓ {item.name}")
            if item.reason:
                print(f"      → {item.reason}")

    # 推奨事項も表示
    recommendations = loader.get_recommendations(params["transport_method"])
    if recommendations:
        print("\n  💡 推奨事項:")
        for rec in recommendations[:3]:  # 最初の3つのみ表示
            print(f"    • {rec}")

    print()


def demo_transport_adjustments() -> None:
    """交通手段別調整のデモ."""
    loader = TransportRulesLoader()

    # デモ用の旅行リクエスト
    destinations = {
        "飛行機で札幌へ": {
            "destination": "札幌",
            "transport_method": "airplane",
            "duration": 2,
            "month": 6,
        },
        "新幹線で大阪へ": {
            "destination": "大阪",
            "transport_method": "train",
            "duration": 1,
            "month": 7,
            "is_shinkansen": True,
        },
        "車で長野へ（冬）": {
            "destination": "長野",
            "transport_method": "car",
            "duration": 2,
            "month": 1,
            "is_rental": False,
        },
        "夜行バスで福岡へ": {
            "destination": "福岡",
            "transport_method": "bus",
            "duration": 0,
            "month": 9,
            "is_highway": True,
            "night_bus": True,
        },
        "レンタカーで沖縄観光": {
            "destination": "沖縄",
            "transport_method": "car",
            "duration": 3,
            "month": 8,
            "is_rental": True,
        },
    }

    print("🚄 交通手段別調整デモンストレーション\n" + "=" * 50)

    for title, params in destinations.items():
        # 追加条件を分離する関数を使用
        additional_conditions = extract_additional_conditions(params)

        items = loader.get_transport_items(
            transport_method=params["transport_method"],
            trip_duration=params["duration"],
            is_domestic=True,
            month=params["month"],
            additional_conditions=additional_conditions,
        )

        # 表示処理を関数化
        params["additional_conditions"] = additional_conditions  # 表示用に追加
        print_trip_details(title, params, items, loader)
        params.pop("additional_conditions")  # クリーンアップ


if __name__ == "__main__":
    demo_transport_adjustments()
