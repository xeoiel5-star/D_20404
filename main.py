import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # 선 굵기와 색상을 상세히 조절하기 위해 추가로 불러옵니다.

# [1. 데이터 불러오기]
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)
    
    # [2. 날짜 전처리]
    df = df.dropna()
    df["기준일자"] = pd.to_datetime(df["기준일자"])
    df = df.sort_values(by="기준일자", ascending=True)
    
    return df

# 제목 설정
st.title("🎬 영화 관객수 분석 대시보드")

# 함수를 호출하여 데이터를 불러옵니다.
df = load_data()


# [3. 영화 선택 기능]
# 영화별 누적관객수 최댓값을 구해 내림차순 정렬 (가장 흥행한 순서)
movie_cumulative = df.groupby("영화명")["누적관객수"].max().sort_values(ascending=False)
movie_list = movie_cumulative.index.tolist()

# 사용자가 개별 분석을 위해 영화를 선택하는 드롭다운
selected_movie = st.selectbox("영화를 선택하세요 (1, 2번 그래프용):", movie_list)

# 선택한 영화와 일치하는 데이터만 필터링 (1, 2번 그래프에 사용)
filtered_df = df[df["영화명"] == selected_movie]


# [4. 그래프 그리기 & 5. 기타 (구역 나누기)]

# --- 첫 번째 그래프 구역 (선택한 영화의 일별 관객수) ---
st.header("1. 일별 관객수 변화 추이")

fig1 = px.line(filtered_df, x="기준일자", y="해당일관객수", title=f"[{selected_movie}] 일별 관객수")
st.plotly_chart(fig1, use_container_width=True)

st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 개봉 첫 주말에 관객수가 급증했다가 이후 서서히 감소하는 추세를 보인다.)")


st.divider() # 구역 나누는 가로선


# --- 두 번째 그래프 구역 (선택한 영화의 누적 관객수) ---
st.header("2. 누적 관객수 변화 추이")

fig2 = px.area(filtered_df, x="기준일자", y="누적관객수", title=f"[{selected_movie}] 누적 관객수 변화")
st.plotly_chart(fig2, use_container_width=True)

st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 개봉 이후 누적 관객수가 얼마나 가파르게 증가했는지, 성장세가 둔화되는 시점은 언제인지 파악할 수 있다.)")


st.divider() # 구역 나누는 가로선


# --- 세 번째 그래프 구역 (Top 5 영화 다중 선그래프 비교) ---
st.header("3. Top 5 영화 흥행 속도 비교 (장기 흥행작)")

movie_appearance_counts = df["영화명"].value_counts()
movies_20_days_or_more = movie_appearance_counts[movie_appearance_counts >= 20].index
top5_long_run_movies = movie_cumulative[movie_cumulative.index.isin(movies_20_days_or_more)].head(5).index.tolist()
top5_df = df[df["영화명"].isin(top5_long_run_movies)]

fig3 = px.line(top5_df, x="기준일자", y="누적관객수", color="영화명", title="누적 관객수 상위 5개 영화 비교 (20일 이상 진입작 기준)")
st.plotly_chart(fig3, use_container_width=True)

st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 초반 반짝 흥행하고 사라진 영화를 제외하고, 꾸준히 인기를 끈 영화들 간의 장기 흥행 속도를 비교할 수 있다.)")


st.divider() # 구역 나누는 가로선


# --- 네 번째 그래프 구역 (극장가 전체 관객수 및 이동평균) ---
st.header("4. 극장가 전체 관객수 흐름 (7일 이동평균)")

# 1. 기준일자별로 박스오피스 TOP10 영화들의 '해당일관객수'를 모두 더합니다.
daily_total = df.groupby("기준일자")["해당일관객수"].sum().reset_index()

# 2. 7일 이동평균을 계산합니다. (최근 7일치의 평균을 구해 요일별로 튀는 값을 부드럽게 깎아줍니다.)
# min_periods=1을 넣으면 첫 1~6일차 데이터도 비워두지 않고 가능한 개수만큼 평균을 냅니다.
daily_total["7일_이동평균"] = daily_total["해당일관객수"].rolling(window=7, min_periods=1).mean()

# 3. 빈 도화지(Figure)를 만들고 그 위에 두 개의 선을 겹쳐 그립니다.
fig4 = go.Figure()

# 원본 합계 선 (연한 회색, 얇게)
fig4.add_trace(go.Scatter(
    x=daily_total["기준일자"], 
    y=daily_total["해당일관객수"],
    mode="lines",
    name="일일 관객수 합계",
    line=dict(color="lightgray", width=1.5)
))

# 7일 이동평균 선 (파란색, 진하고 두껍게)
fig4.add_trace(go.Scatter(
    x=daily_total["기준일자"], 
    y=daily_total["7일_이동평균"],
    mode="lines",
    name="7일 이동평균",
    line=dict(color="royalblue", width=3)
))

# 그래프의 제목과 축 이름을 깔끔하게 설정해줍니다.
fig4.update_layout(title="전체 관객수 및 7일 이동평균 추이", xaxis_title="기준일자", yaxis_title="관객수")

# 스트림릿에 그래프 출력
st.plotly_chart(fig4, use_container_width=True)

st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 매주 주말마다 관객수가 치솟는 뾰족한 현상(연한 선)에 가려진, 실제 극장가의 전반적인 관객수 상승·하락 흐름(진한 선)을 정확히 파악할 수 있다.)")
