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

    # 1. 필수 데이터 결측치 제거
    df = df.dropna(subset=["movieCd", "movieNm", "total_audi"])

    # 2. 장르 첫 번째 값만 추출
    df["main_genre"] = (
        df["genre"].dropna().astype(str).apply(lambda x: x.split("|")[0])
    )
    df["main_genre"] = df["main_genre"].fillna("미분류")

    # 3. 고유 식별자(movieCd) 기준 중복 제거
    df = df.drop_duplicates(subset=["movieCd"])

    # 4. 트리맵용 고유 라벨 생성
    df["movie_label"] = df["movieNm"] + " (" + df["movieCd"].astype(str) + ")"

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
# 2. 장르 안의 영화 (트리맵)
# ---------------------------------------------------------
st.header("2. 장르 안의 영화 (트리맵)")

fig2 = px.treemap(
    df,
    path=["main_genre", "movie_label"],
    values="total_audi",
    title="장르 및 영화별 총 관객 수 분포",
    hover_data={"movieNm": True, "total_audi": ":,.0f", "movie_label": False},
)

fig2.update_traces(
    hovertemplate="<b>영화명: %{customdata[0]}</b><br>총 관객 수: %{value:,.0f}명"
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

# 히스토그램 생성
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

# ── 데이터 자동 계산 (텍스트 출력용) ──
# 1. 가장 관객이 많은 영화 데이터
max_audi_movie = df.loc[df["total_audi"].idxmax()]
max_title = max_audi_movie["movieNm"]
max_audi_val = max_audi_movie["total_audi"]

# 2. 가장 집중된 구간 계산 (300만 미만 집중 여부)
under_3m_count = len(df[df["total_audi"] < 3000000])
under_3m_ratio = (under_3m_count / len(df)) * 100

st.divider()
st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    f"대부분의 영화({under_3m_ratio:.1f}%)가 **총 관객 수 300만 명 미만 구간**에 밀집해 있으며, "
    f"가장 관객이 많은 영화는 **'{max_title}'**(약 {max_audi_val:,.0f}명)입니다."
)
st.divider()
