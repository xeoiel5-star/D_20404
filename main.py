import streamlit as st
import pandas as pd
import plotly.express as px

# [1. 데이터 불러오기]
# @st.cache_data 데코레이터를 사용하면 앱이 재실행될 때마다 데이터를 다시 다운로드하지 않고 메모리에 저장해둔(캐싱) 데이터를 재사용합니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)
    
    # [2. 날짜 전처리]
    # 2-1. 결측치(데이터가 없는 빈 칸)가 포함된 행을 모두 삭제합니다.
    df = df.dropna()
    
    # 2-2. "기준일자" 컬럼을 단순한 글자(문자열)에서 날짜(datetime) 형식으로 변환합니다.
    df["기준일자"] = pd.to_datetime(df["기준일자"])
    
    # 2-3. 데이터를 "기준일자" 순서대로 오름차순(과거 -> 최신) 정렬합니다.
    df = df.sort_values(by="기준일자", ascending=True)
    
    return df

# 제목 설정
st.title("🎬 영화 관객수 분석 대시보드")

# 함수를 호출하여 데이터를 불러옵니다.
df = load_data()


# [3. 영화 선택 기능]
# 영화별 최종 누적관객수를 구하기 위해, 영화명으로 그룹을 묶고 누적관객수의 최댓값을 찾습니다.
# 그 후 누적관객수를 기준으로 내림차순(가장 많은 순서대로) 정렬합니다.
movie_cumulative = df.groupby("영화명")["누적관객수"].max().sort_values(ascending=False)

# 정렬된 영화 이름들만 뽑아서 리스트로 만듭니다. (중복 없이 누적관객수 순으로 정렬된 상태)
movie_list = movie_cumulative.index.tolist()

# 사용자가 영화를 선택할 수 있는 드롭다운(선택 상자)을 만듭니다.
selected_movie = st.selectbox("영화를 선택하세요:", movie_list)

# 선택한 영화와 이름이 일치하는 데이터만 걸러냅니다.
filtered_df = df[df["영화명"] == selected_movie]


# [4. 선그래프 그리기 & 5. 기타 (구역 나누기)]

# --- 첫 번째 그래프 구역 ---
st.header("1. 일별 관객수 변화 추이")

# Plotly를 이용해 선 그래프(line)를 그립니다. x축은 날짜, y축은 해당일관객수로 설정합니다.
fig1 = px.line(filtered_df, x="기준일자", y="해당일관객수", title=f"[{selected_movie}] 일별 관객수")

# 완성된 그래프를 스트림릿 화면에 출력합니다.
st.plotly_chart(fig1, use_container_width=True)

# 그래프 아래에 인사이트(알 수 있는 점)를 적을 수 있는 문구 자리를 만듭니다.
st.caption("💡 **이 그래프로 알 수 있는 것:** (예시: 개봉 첫 주말에 관객수가 급증했다가 이후 서서히 감소하는 추세를 보인다.)")


st.divider() # 구역을 나누는 가로선을 긋습니다.


# --- 두 번째 그래프 구역 (추가 예정) ---
st.header("2. 추가 그래프 구역 (예정)")

st.info("여기에 새로운 데이터를 분석한 그래프가 추가될 예정입니다.")

st.caption("💡 **이 그래프로 알 수 있는 것:** (여기에 분석 내용을 적어주세요)")
