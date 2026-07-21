"""可展示已验证道具瞄点图的 Streamlit 页面。"""

import streamlit as st

from cs2_rag.generator import generate_answer
from cs2_rag.retriever import ACTIVE_DUTY_MAPS, detect_map, get_map_label, retrieve
from cs2_rag.utility_lineups import find_verified_lineups, image_path


st.set_page_config(page_title="CS2 战术助手", page_icon="🎯", layout="wide")
st.title("CS2 战术助手")
st.caption("回答仅依据本地战术资料；下方仅展示已验证的道具瞄点图。")

map_options = {"自动识别": None}
map_options.update({label: map_name for map_name, label, _ in ACTIVE_DUTY_MAPS})

query = st.text_input(
    "问题",
    placeholder="例如：Mirage A 坪三烟快攻时，三颗烟怎么投？",
)
selected_label = st.selectbox("地图筛选", list(map_options))

if st.button("查询", type="primary"):
    if not query.strip():
        st.warning("请先输入问题。")
        st.stop()

    map_name = map_options[selected_label] or detect_map(query)
    if map_name is None:
        st.warning("请在问题中写明地图，或通过地图筛选指定一张地图。")
        st.stop()

    with st.spinner("正在检索战术资料并生成回答..."):
        evidence = retrieve(query, map_filter=map_name)
        answer = generate_answer(query, evidence, map_name=map_name)

    st.subheader(f"回答｜{get_map_label(map_name)}")
    st.write(answer)

    lineups = find_verified_lineups(evidence)
    if lineups:
        st.subheader("已验证道具瞄点")
        for lineup in lineups:
            st.markdown(f"#### {lineup['label']}｜{lineup['throw_type']}")
            st.caption(lineup.get("notes", ""))

            images = sorted(lineup["images"], key=lambda item: item["step"])
            columns = st.columns(len(images))
            for column, image in zip(columns, images):
                with column:
                    path = image_path(image)
                    if path.is_file():
                        st.image(str(path), caption=image["caption"], use_container_width=True)
                    else:
                        st.error(f"缺少图片：{path}")
    else:
        st.info("当前检索结果没有关联的已验证道具瞄点图。")

    with st.expander("检索证据"):
        for index, item in enumerate(evidence, start=1):
            st.markdown(
                f"**[{index}] {item['metadata'].get('source', '未知来源')}**  "
                f"\n{item['text']}"
            )
