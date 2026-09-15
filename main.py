import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# 기준일자별로 박스오피스 TOP10 영화들의 '해당일관객수'를 모두 더합니다.
daily_total = df.groupby("기준일자")["해당일관객수"].sum().reset_index()

# 7일 이동평균 계산
daily_total["7일_이동평균"] = daily_total["해당일관객수"].rolling(window=7, min_periods=1).mean()

fig4 = go.Figure()

# 원본 합계 선
fig4.add_trace(go.Scatter(
    x=daily_total["기준일자"], 
    y=daily_total["해당일관객수"],
    mode="lines",
    name="일일 관객수 합계",
    line=dict(color="lightgray", width=1.5)
))

# 7일 이동평균 선
fig4.add_trace(go.Scatter(
    x=daily_total["기준일자"], 
    y=daily_total["7일_이동평균"],
    mode="lines",
    name="7일 이동평균",
    line=dict(color="royalblue", width=3)
))

fig4.update_layout(title="전체 관객수 및 7일 이동평균 추이", xaxis_title="기준일자", yaxis_title="관객수")
st.plotly_chart(fig4, use_container_width=True)

st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 매주 주말마다 관객수가 치솟는 뾰족한 현상(연한 선)에 가려진, 실제 극장가의 전반적인 관객수 상승·하락 흐름(진한 선)을 정확히 파악할 수 있다.)")


st.divider() # 구역 나누는 가로선


# --- 다섯 번째 그래프 구역 (월별 총 관객수 막대그래프) ---
st.header("5. 월별 총 관객수 비교")

# daily_total 데이터의 기준일자에서 '연-월(YYYY-MM)' 추출
daily_total["연월"] = daily_total["기준일자"].dt.strftime("%Y-%m")

# 월 단위 그룹화
monthly_total = daily_total.groupby("연월")["해당일관객수"].sum().reset_index()

fig5 = px.bar(
    monthly_total, 
    x="연월", 
    y="해당일관객수", 
    title="월별 극장 전체 관객수 합계",
    text_auto=".2s"
)
fig5.update_layout(xaxis_title="월(Year-Month)", yaxis_title="총 관객수")
st.plotly_chart(fig5, use_container_width=True)

st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 월별 전체 관객수 합계를 통해 연중 극장가의 최대 성수기(여름/겨울 방학, 연말 등)와 비수기가 언제였는지 한눈에 비교할 수 있다.)")


st.divider() # 구역 나누는 가로선


# --- 여섯 번째 그래프 구역 (캘린더 히트맵) ---
st.header("6. 요일 및 주차별 관객수 분포 (캘린더 히트맵)")

# 1. 요일 이름 및 순서 정의 (월요일 ~ 일요일)
days_order = ["월", "화", "수", "목", "금", "토", "일"]
day_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}

# 2. 요일 컬럼 생성
daily_total["요일"] = daily_total["기준일자"].dt.dayofweek.map(day_map)

# 3. 월별 주차(Week of Month) 계산 함수
def get_week_of_month(dt):
    first_day = dt.replace(day=1)
    adjusted_dom = dt.day + first_day.weekday()
    return (adjusted_dom - 1) // 7 + 1

daily_total["주차"] = daily_total["기준일자"].apply(get_week_of_month)

# Y축에 표기할 '연-월 주차' 라벨 및 마우스 오버용 날짜 문자열(YYYY-MM-DD) 생성
daily_total["연월_주차"] = daily_total["기준일자"].dt.strftime("%Y-%m") + " " + daily_total["주차"].astype(str) + "주차"
daily_total["날짜_str"] = daily_total["기준일자"].dt.strftime("%Y-%m-%d")

# 4. 히트맵 생성을 위한 피벗 테이블(Pivot Table) 작성
# Z축: 해당일 관객수 합계
pivot_audience = daily_total.pivot(index="연월_주차", columns="요일", values="해당일관객수").reindex(columns=days_order)

# 마우스 오버 툴팁용: YYYY-MM-DD 날짜
pivot_date = daily_total.pivot(index="연월_주차", columns="요일", values="날짜_str").reindex(columns=days_order)

# 5. Plotly Heatmap 그리기
fig6 = go.Figure(data=go.Heatmap(
    z=pivot_audience.values,
    x=days_order,
    y=pivot_audience.index,
    text=pivot_date.values, # 마우스 오버 시 출력할 yyyy-mm-dd 날짜 데이터
    hovertemplate="<b>날짜: %{text}</b><br>요일: %{x}요일<br>관객수: %{z:,.0f}명<extra></extra>",
    colorscale="Reds", # 관객수가 많을수록 붉은색이 진해짐
))

# 위에서 아래로 시간 순서(주차)가 흐르도록 Y축 정렬 설정
fig6.update_layout(
    title="일별 관객수 캘린더 히트맵",
    xaxis_title="요일",
    yaxis_title="월 / 주차",
    yaxis=dict(autorange="reversed")
)

st.plotly_chart(fig6, use_container_width=True)

st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 주말(토, 일)과 특정 연휴 기간에 관객수가 붉게 집중되는 패턴을 확인할 수 있으며, 타일 위에 마우스를 올려 정확한 날짜(YYYY-MM-DD)별 관객수를 바로 파악할 수 있다.)")
