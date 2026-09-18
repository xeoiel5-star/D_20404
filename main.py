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
genre_counts = df["main_genre"].value_counts().reset_index(name="count")
genre_counts.columns = ["genre", "count"]

# Plotly 도넛 차트 생성
fig1 = px.pie(
    genre_counts,
    names="genre",
    values="count",
    hole=0.4,
    title="장르별 영화 편수 비율",
)

# 호버 시 편수(value)와 비율(percent) 모두 표시
fig1.update_traces(
    hovertemplate="<b>장르: %{label}</b><br>편수: %{value}편<br>비율: %{percent}"
)

# 그래프 출력
st.plotly_chart(fig1, use_container_width=True)

# 시각화 해석 영역
st.divider()
st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "박스오피스 상위권 영화 중 특정 주요 장르가 차지하는 비중과 장르별 편수 분포를 한눈에 비교할 수 있습니다."
)
st.divider()

# ---------------------------------------------------------
# 2. 장르 및 영화별 총 관객 수 (트리맵)
# ---------------------------------------------------------
st.header("2. 장르 및 영화별 총 관객 수 트리맵")

# Plotly 트리맵 생성 (계층 구조: main_genre -> movieNm, 칸 크기: total_audi)
fig2 = px.treemap(
    df,
    path=[px.Constant("전체 장르"), "main_genre", "movieNm"],
    values="total_audi",
    title="장르 및 영화별 총 관객 수 분포",
)

# 마우스 호버 시 영화명과 총 관객 수 표시
fig2.update_traces(
    hovertemplate="<b>영화명: %{label}</b><br>총 관객 수: %{value:,.0f}명"
)

# 그래프 출력
st.plotly_chart(fig2, use_container_width=True)

# 시각화 해석 영역
st.divider()
st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "장르 전체에서 각 장르와 개별 영화가 차지하는 총 관객 수 비중을 면적 크기로 직관적으로 파악할 수 있습니다."
)
st.divider()
