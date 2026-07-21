from .generator import generate_answer
from .retriever import (
    ACTIVE_DUTY_MAPS,
    detect_map,
    get_map_label,
    resolve_map,
    retrieve,
)
from .utility_lineups import find_verified_lineups, image_path


def choose_map(query: str) -> str | None:
    """允许用户按序号或名称选择；回车时从问题中自动识别地图。"""
    print("\n当前 CS2 服役地图：")
    for index, (_, label, _) in enumerate(ACTIVE_DUTY_MAPS, start=1):
        print(f"  {index}. {label}")

    selection = input("地图筛选（序号/名称；回车自动识别）：").strip()
    if not selection:
        return detect_map(query)

    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(ACTIVE_DUTY_MAPS):
            return ACTIVE_DUTY_MAPS[index - 1][0]
        raise ValueError("地图序号超出范围")

    return resolve_map(query, map_filter=selection)


def main() -> None:
    print("CS2 战术助手已启动。输入 exit 退出。")
    print("为避免混用地图战术，每次提问都需要指定或自动识别一张服役地图。")

    while True:
        query = input("\n问题：").strip()
        if query.lower() in {"exit", "quit"}:
            break
        if not query:
            continue

        try:
            map_name = choose_map(query)
        except ValueError as error:
            print(f"地图筛选无效：{error}")
            continue

        if map_name is None:
            print("未识别到地图。请在问题中写明地图，或输入上方对应的地图序号。")
            continue

        print(f"\n当前地图过滤：{get_map_label(map_name)}")
        evidence = retrieve(query, map_filter=map_name)
        answer = generate_answer(query, evidence, map_name=map_name)

        print(f"\n回答：\n{answer}")
        print("\n检索来源：")
        for index, item in enumerate(evidence, start=1):
            print(f"[{index}] {item['metadata'].get('source')} - "
                  f"{item['metadata'].get('map')} - "
                  f"{item['metadata'].get('side')}")

        lineups = find_verified_lineups(evidence)
        if lineups:
            print("\n已验证道具瞄点：")
            for lineup in lineups:
                print(f"- {lineup['label']}（{lineup['throw_type']}）")
                for image in sorted(lineup["images"], key=lambda item: item["step"]):
                    print(f"  {image['caption']}：{image_path(image)}")


if __name__ == "__main__":
    main()
