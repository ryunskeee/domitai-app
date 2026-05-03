import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from heapq import nlargest

# ---- 認証・シート取得 ---- #
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheet_data(spreadsheet_url):
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_url(spreadsheet_url).sheet1
    return sheet.get_all_values()

# ---- 得点処理 ---- #
def parse_scores(data, floors, judges):
    names = []
    total_scores = []
    quality_scores = []
    cute_scores = []

    a = 0
    for j in range(int(judges)):
        a += 1
        b = 0
        for i in range(int(floors)):
            # 名前は最初の審査員だけ取得
            if j == 0:
                names.append(data[a][b+1])

            # 数値変換
            score2 = float(data[a][2+b])
            score3 = float(data[a][3+b])
            score4 = float(data[a][4+b])
            score5 = float(data[a][5+b])
            score6 = float(data[a][6+b])

            # 合計点
            total_scores.append(
                score2 + score3 + score4 + score5 * 0.8 + score6 * 0.8
            )

            # クオリティ
            quality_scores.append(
                score2 + score3 + score4 * 1.5
            )

            # かわいい
            cute_scores.append(
                score2 + score3 + score6 * 1.5
            )

            b += 6

    return names, total_scores, quality_scores, cute_scores

def summarize(scores, floors, judges):
    return [
        sum(scores[i + j * floors] for j in range(judges))
        for i in range(floors)
    ]

def get_ranking(scores, names):
    ranked = nlargest(len(scores), [(score, i) for i, score in enumerate(scores)])
    return [(i+1, names[r[1]], r[0]) for i, r in enumerate(ranked)]

# ---- Streamlit UI ---- #
st.title("🎓 寮祭採点集計ツール")

spreadsheet_url = "https://docs.google.com/spreadsheets/d/1_wYmDxcOdwTIEufJFnkT-WXPMBN22DqgR0YSVfia0K8/edit?usp=sharing"

floors = st.number_input("階（グループ）の数", min_value=1, step=1)
judges = st.number_input("審査員の数", min_value=1, step=1)

title_quality = st.text_input("クオリティ賞の名前", value="冷え賞")
title_cute = st.text_input("かわいい賞の名前", value="可愛すぎて滅")

if spreadsheet_url and floors and judges:
    try:
        data = get_sheet_data(spreadsheet_url)
        names, t, q, c = parse_scores(data, floors, judges)

        sum_t = summarize(t, floors, judges)
        sum_q = summarize(q, floors, judges)
        sum_c = summarize(c, floors, judges)

        st.subheader("📋 部門別ランキング")

        def show_table(title, ranking):
            st.markdown(f"### 🏆 {title}")
            df = pd.DataFrame({
                "順位": [r[0] for r in ranking],
                "名前": [r[1] for r in ranking],
                "得点": [r[2] for r in ranking]
            })
            st.dataframe(df.style.format({"得点": "{:.1f}"}), use_container_width=True)

        show_table("合計点", get_ranking(sum_t, names))
        show_table(title_quality, get_ranking(sum_q, names))
        show_table(title_cute, get_ranking(sum_c, names))

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")