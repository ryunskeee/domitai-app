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
    names, total_scores, funny_scores, quality_scores, cute_scores = [], [], [], [], []
    a=0
    for j in range(int(judges)):
        a=a+1
        b=0
        for _ in range(int(floors)):
            if j==0:
                names.append(data[a][b+1])
            total_scores.append(float(data[a][2+b])+float(data[a][3+b])+float(data[a][4+b])+float(data[a][5+b]*0.8)+float(data[a][6+b]*0.8))
            quality_scores.append(float(data[a][2+b])+(float(data[a][3+b]))+(float(data[a][4+b])*1.5))
            cute_scores.append(float(data[a][2+b])+float(data[a][3+b])+float(data[a][6+b])*1.5)
            b=b+6
    return names, total_scores, funny_scores, quality_scores, cute_scores

def summarize(scores, floors, judges):
    return [sum(scores[i + j * floors] for j in range(judges)) for i in range(floors)]

def get_ranking(scores, names):
    ranked = nlargest(len(scores), [(score, i) for i, score in enumerate(scores)])
    return [(i+1, names[r[1]], r[0]) for i, r in enumerate(ranked)]

# ---- Streamlit UI ---- #
st.title("🎓 寮祭採点集計ツール")

json_file = "C:/Users/rinry/Downloads/service_account.json"
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1_wYmDxcOdwTIEufJFnkT-WXPMBN22DqgR0YSVfia0K8/edit?usp=sharin"

floors = st.number_input("階（グループ）の数", min_value=1, step=1)
judges = st.number_input("審査員の数", min_value=1, step=1)


title_quality = st.text_input("1つ目の賞名", value="冷え賞")

title_cute = st.text_input("2つ目の賞名", value="可愛すぎて滅")



if spreadsheet_url and floors and judges:
    try:
        data = get_sheet_data(spreadsheet_url)
        names, t, f, q, c = parse_scores(data, floors, judges)
        sum_t = summarize(t, floors, judges)
        sum_f = summarize(f, floors, judges)
        sum_q = summarize(q, floors, judges)
        sum_c = summarize(c, floors, judges)

        st.subheader("📋 部門別ランキング")

        def show_table(title, ranking):
            st.markdown(f"### 🏆 {title}")
            df = pd.DataFrame({ "順位": [r[0] for r in ranking],
                       "名前": [r[1] for r in ranking],
                       "得点": [r[2] for r in ranking] })
            st.dataframe(df.style.format({"得点": "{:.1f}"}), use_container_width=True)
        show_table("合計点", get_ranking(sum_t, names))
        show_table(title_funny, get_ranking(sum_f, names))
        show_table(title_quality, get_ranking(sum_q, names))
        show_table(title_cute, get_ranking(sum_c, names))

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
