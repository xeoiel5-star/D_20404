# main.py
import datetime
import pandas as pd
import pytz
import requests
import streamlit as st

# 1. 웹앱 페이지 제목 및 기본 설정
st.set_page_config(
    page_title="일별 박스오피스 조회",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 일별 박스오피스 조회")

# 2. 비밀 금고(Secrets)에서 KOBIS API 인증키 불러오기
# Streamlit Cloud의 Secrets 설정에 KOBIS_KEY가 없는 경우 안내 메시지 출력
if "KOBIS_KEY" not in st.secrets:
    st.error("🔑 API 인증키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info(
        "**[확인할 사항]**\n"
        "1. Streamlit Cloud의 **Secrets** 설정에 `KOBIS_KEY = \"발급받은키\"`를 등록해 주세요.\n"
        "2. 로컬 개발 환경이라면 `.streamlit/secrets.toml` 파일 안에 키가 올바르게 작성되었는지 확인해 주세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 3. 한국 시간(KST) 기준 '어제' 날짜 계산 및 달력(st.date_input) 위젯
# 배포 서버의 시계가 해외 기준(UTC)일 수 있으므로 서울 시간대로 명시적으로 설정합니다.
kst = pytz.timezone("Asia/Seoul")
today_kst = datetime.datetime.now(kst).date()
yesterday = today_kst - datetime.timedelta(days=1)

# 달력에서 조회할 날짜를 선택합니다. (최대 선택 가능 날짜: 어제)
selected_date = st.date_input(
    "📅 박스오피스를 조회할 날짜를 선택하세요:",
    value=yesterday,
    max_value=yesterday,
    help="오늘 날짜의 박스오피스는 아직 집계 전이므로 선택할 수 없습니다."
)

# API 요청용 문자열(YYYYMMDD)과 화면 표시용 문자열 변환
target_dt = selected_date.strftime("%Y%m%d")
formatted_date = selected_date.strftime("%Y년 %m월 %d일")

st.caption(f"🔍 현재 조회 중인 날짜: **{formatted_date}** (한국 시간 기준)")

# 4. KOBIS API 호출 함수 (1시간 데이터 기억/캐싱)
# 선택한 날짜별로 결과를 1시간 동안 캐시(기억)하여 API 중복 호출을 방지합니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(key, date_str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": key,
        "targetDt": date_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        # 네트워크 오류(4xx, 5xx) 체크
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        # 통신 에러 발생 시 None 반환
        return None

# API 데이터 요청 실행
data = fetch_box_office_data(api_key, target_dt)

# 5. 예외 및 오류 처리 (한국어 안내)
# (1) 네트워크 요청 자체가 실패했을 때
if data is None:
    st.error("⚠️ 박스오피스 데이터를 불러오지 못했습니다.")
    st.info(
        "**[확인할 사항]**\n"
        "1. 인터넷 및 서버의 네트워크 연결 상태를 확인해 주세요.\n"
        "2. 영화진흥위원회(KOBIS) API 서버가 점검 중인지 확인해 주세요."
    )
    st.stop()

# (2) API 인증키가 틀렸거나 오류 응답(faultInfo)이 왔을 때
if "faultInfo" in data:
    error_msg = data["faultInfo"].get("message", "알 수 없는 에러가 발생했습니다.")
    st.error(f"⚠️ KOBIS API 오류 발생: {error_msg}")
    st.info(
        "**[확인할 사항]**\n"
        "1. Secrets에 등록된 `KOBIS_KEY` 값이 정확한지 확인해 주세요.\n"
        "2. KOBIS 오픈API 웹사이트에서 발급받은 키의 사용 권한 및 상태를 점검해 주세요."
    )
    st.stop()

# (3) 선택한 날짜의 영화 목록이 비어 있을 때
box_office_result = data.get("boxOfficeResult", {})
movie_list = box_office_result.get("dailyBoxOfficeList", [])

if not movie_list:
    st.warning("⚠️ 해당 날짜의 영화 박스오피스 목록 데이터가 비어 있습니다.")
    st.info("💡 **그날은 아직 집계 전입니다.** 다른 날짜를 선택해 주세요.")
    st.stop()

# 6. 데이터 가공 및 변환
df = pd.DataFrame(movie_list)

# 숫자로 변환할 컬럼 목록 (문자열 -> 정수)
numeric_columns = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# (1) 전날 대비 순위 증감(rankInten) 화살표 표시 가공
def format_rank_change(val):
    if val > 0:
        return f"🔴 ▲{val}"
    elif val < 0:
        return f"🔵 ▼{abs(val)}"
    else:
        return "-"

df["rankChangeFormatted"] = df["rankInten"].apply(format_rank_change)

# (2) 누적관객 100만 명 이상인 영화명 옆에 트로피(🏆) 이모지 추가
def format_movie_title(row):
    title = row["movieNm"]
    if row["audiAcc"] >= 1_000_000:
        return f"{title} 🏆"
    return title

df["movieNmFormatted"] = df.apply(format_movie_title, axis=1)

# 화면에 보여줄 컬럼명 한국어 매핑 및 순서 지정
column_mapping = {
    "rank": "순위",
    "rankChangeFormatted": "순위 변동",
    "movieNmFormatted": "영화명",
    "openDt": "개봉일",
    "audiCnt": "관객수",
    "audiAcc": "누적관객",
    "scrnCnt": "스크린수"
}

df_display = df[list(column_mapping.keys())].rename(columns=column_mapping)
# 순위 기준 오름차순 정렬
df_display = df_display.sort_values(by="순위", ascending=True)

# 7. 1위 영화 강조 지표 카드 세 장
top1_movie = df_display.iloc[0]

st.subheader("🏆 1위 영화")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="영화 제목", value=top1_movie["영화명"])

with col2:
    st.metric(label="당일 관객수", value=f"{top1_movie['관객수']:,} 명")

with col3:
    st.metric(label="누적 관객수", value=f"{top1_movie['누적관객']:,} 명")

st.divider()

# 8. 관객수 상위 5편 막대그래프
st.subheader("📊 관객수 상위 5개 영화")
top5_df = df_display.head(5)

st.bar_chart(
    data=top5_df,
    x="영화명",
    y="관객수",
    use_container_width=True
)

st.divider()

# 9. 전체 박스오피스 순위 표
st.subheader("📋 전체 순위표")

st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "관객수": st.column_config.NumberColumn("관객수", format="%d 명"),
        "누적관객": st.column_config.NumberColumn("누적관객", format="%d 명"),
        "스크린수": st.column_config.NumberColumn("스크린수", format="%d 개")
    }
)
