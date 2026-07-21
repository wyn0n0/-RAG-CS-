from openai import OpenAI

from .config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


def generate_answer(
    query: str,
    evidence: list[dict],
    map_name: str | None = None,
) -> str:
    if not evidence:
        map_hint = f" {map_name}" if map_name else ""
        return f"知识库中暂无{map_hint}的相关战术资料。"

    context = "\n\n".join(
        f"[{i + 1}] 来源：{item['metadata'].get('source', '未知')}；"
        f"地图：{item['metadata'].get('map', '未知')}；"
        f"阵营：{item['metadata'].get('side', '未知')}\n"
        f"{item['text']}"
        for i, item in enumerate(evidence)
    )

    map_rule = ""
    if map_name:
        map_rule = f"5. 当前指定地图是 {map_name}；不得引用或套用其他地图的战术。\n"

    prompt = f"""你是 CS2 战术助手。只能依据提供的战术资料回答。

要求：
1. 不要编造文档中不存在的战术、点位或时间。
2. 证据不足时明确回答“资料不足，无法判断”。
3. 用简明中文说明行动、目的和注意事项。
4. 在每个关键结论后标注对应资料编号，例如 [1]。
{map_rule}

用户问题：
{query}

战术资料：
{context}
"""

    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=800,
    )
    return response.choices[0].message.content.strip()
