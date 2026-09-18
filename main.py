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

    # px.treemap 중복 오류 방지: 동일 영화명이 있을 경우 대표값 처리 (중복 제거)
    df = df.drop_duplicates(subset=["main_genre", "movieNm"])

    return df


df = load_data()

# ---------------------------------------------------------
# 1. 장르별 영화 편수 (도넛 그래프)
# ---------------------------------------------------------
st.header("1. 장르별 영화 편수 분포")

genre_counts = df["main_genre"].value_counts().reset_index(name="count")
genre_counts.columns = ["genre", "count"]

fig1 = px.pie(
    genre_counts,
    names="genre",
    values="count",
    hole=0.4,
    title="장르별 영화 편수 비율",
)

fig1.update_traces(
    hovertemplate="<b>장르: %{label}</b><br>편수: %{value}편<br>비율: %{percent}"
)

st.plotly_chart(fig1, use_container_width=True)

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

fig2 = px.treemap(
    df,
    path=[px.Constant("전체 장르"), "main_genre", "movieNm"],
    values="total_audi",
    title="장르 및 영화별 총 관객 수 분포",
)

fig2.update_traces(
    hovertemplate="<b>영화명: %{label}</b><br>총 관객 수: %{value:,.0f}명"
)

st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "장르 전체에서 각 장르와 개별 영화가 차지하는 총 관객 수 비중을 면적 크기로 직관적으로 파악할 수 있습니다."
)
st.divider()

# ---------------------------------------------------------
# 3. 총 관객 수 분포 (히스토그램)
# ---------------------------------------------------------
st.header("3. 총 관객 수 분포 히스토그램")

fig3 = px.histogram(
    df,
    x="total_audi",
    nbins=30,
    title="총 관객 수 구간별 영화 편수 분포",
    labels={"total_audi": "총 관객 수(명)"},
)

fig3.update_layout(yaxis_title_text="영화 편수(개)")

fig3.update_traces(
    hovertemplate="<b>관객 수 구간: %{x:,.0f}명 주변</b><br>영화 편수: %{y}편"
)

st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "대부분의 흥행 영화가 특정 관객 수 구간에 얼마나 집중되어 있는지, 그리고 극소수의 초대형 흥행작(아웃라이어)이 어느 위치에 있는지 분포 형태를 확인할 수 있습니다."
)
st.divider()

# ---------------------------------------------------------
# 4. 개봉일 스크린 수와 총 관객 수의 관계 (산점도)
# ---------------------------------------------------------
st.header("4. 개봉일 스크린 수와 총 관객 수의 상관관계")

fig4 = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    color="main_genre",
    hover_name="movieNm",
    title="개봉일 스크린 수 vs 총 관객 수 관계",
    labels={
        "first_scrn": "개봉일 스크린 수(개)",
        "total_audi": "총 관객 수(명)",
        "main_genre": "장르",
    },
)

fig4.update_traces(
    hovertemplate="<b>영화명: %{hovertext}</b><br>개봉일 스크린 수: %{x:,.0f}개<br>총 관객 수: %{y:,.0f}명"
)

st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "초기 스크린 확보 수(초반 배급 규모)가 최종 흥행(총 관객 수)에 미치는 영향 및 양의 상관관계 여부를 파악할 수 있습니다."
)
st.divider()
