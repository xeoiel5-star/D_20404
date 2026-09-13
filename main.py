import streamlit as st
import pandas as pd
import plotly.express as px

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
st.header("3. Top 5 영화 흥행 속도 비교")

# 이미 누적관객수 내림차순으로 정렬된 movie_list에서 상위 5개 영화 이름만 뽑습니다.
top5_movies = movie_list[:5]

# 원본 데이터(df)에서 영화명이 상위 5개 리스트에 포함되는(.isin) 데이터만 걸러냅니다.
top5_df = df[df["영화명"].isin(top5_movies)]

# Plotly 다중 선 그래프를 그립니다. 
# color="영화명" 옵션을 주면, 영화별로 알아서 다른 색이 칠해지고 오른쪽에 범례(Legend)가 나타납니다.
fig3 = px.line(top5_df, x="기준일자", y="누적관객수", color="영화명", title="누적 관객수 상위 5개 영화 비교")

st.plotly_chart(fig3, use_container_width=True)

st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 가장 흥행한 5개 영화들이 각각 어느 시점에 관객을 폭발적으로 모았는지 한눈에 비교할 수 있다.)")
