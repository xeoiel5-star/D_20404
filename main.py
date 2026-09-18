import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계", layout="wide"
)

st.title("영화 데이터 그래프 도감 2 - 분포와 관계")
st.write("1년간 박스오피스 Top 10에 든 개봉 영화 216편의 데이터 시각화")


# 데이터 로드 및 전처리
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)

    # 장르가 세로막대 기호(|)로 분리되어 있는 경우 첫 번째 장르만 추출
    df["main_genre"] = (
        df["genre"].dropna().astype(str).apply(lambda x: x.split("|")[0])
    )
    return df


df = load_data()

# ---------------------------------------------------------
# 1. 장르별 영화 편수 (도넛 그래프)
# ---------------------------------------------------------
st.header("1. 장르별 영화 편수 분포")

# 장르별 영화 수 집계
genre_counts = (
    df["main_genre"].value_counts().reset_index(name="count")
)
genre_counts.columns = ["genre", "count"]

# Plotly 도넛 차트 생성
fig = px.pie(
    genre_counts,
    names="genre",
    values="count",
    hole=0.4,
    title="장르별 영화 편수 비율",
)

# 호버 시 편수(value)와 비율(percent) 모두 표시
fig.update_traces(
    hovertemplate="<b>장르: %{label}</b><br>편수: %{value}편<br>비율: %{percent}"
)

# 그래프 출력
st.plotly_chart(fig, use_container_width=True)

# 시각화 해석 영역
st.divider()
st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "박스오피스 상위권 영화 중 특정 주요 장르가 차지하는 비중과 장르별 편수 분포를 한눈에 비교할 수 있습니다."
)
st.divider()
# ── 그래프 2. 장르 안의 영화 (트리맵) ──
st.header("2. 장르 안의 영화 (트리맵)")
fig2 = px.treemap(df, path=["장르", "movieNm"], values="total_audi",
                  hover_data=["total_audi"])
st.plotly_chart(fig2, width="stretch")
st.caption("이 그래프로 알 수 있는 것: (한 문장으로 적어 보세요)")
