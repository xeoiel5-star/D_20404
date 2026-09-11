# main.py
import datetime
import pandas as pd
import pytz
import requests
import streamlit as st

# 1. 웹앱 페이지 제목 및 기본 설정
st.set_page_config(
    page_title="어제 박스오피스 순위",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제 일별 박스오피스")

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

# 3. 한국 시간(KST) 기준 '어제' 날짜 계산
# 배포 서버의 시계가 해외 기준(UTC)일 수 있으므로 서울 시간대로 명시적으로 설정합니다.
kst = pytz.timezone("Asia/Seoul")
yesterday = datetime.datetime.now(kst) - datetime.timedelta(days=1)

# API 요청에 필요한 YYYYMMDD 형식 문자열
target_dt = yesterday.strftime("%Y%m%d")
# 화면에 보여 줄 날짜 형식
formatted_date = yesterday.strftime("%Y년 %m월 %d일")

st.caption(f"📅 **조회 날짜:** {formatted_date} (한국 시간 기준)")

# 4. KOBIS API 호출 함수 (1시간 데이터 기억/캐싱)
# 똑같은 날짜로 다시 요청하면 API를 부르지 않고 캐시된 데이터를 사용합니다.
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

# 데이터 요청 실행
data = fetch_box_office_data(api_key, target_dt)

# 5. 예외 및 오류 처리 (한국어 안내)
# (1) 네트워크 요청 자체가 실패했을 때
if data is None:
    st.error("⚠️ 박스오피스 데이터를 불러오지 못했습니다.")
    st.info(
        "**[확인할 사항]**\n"
        "1. 서버의 네트워크 연결 상태를 확인해 주세요.\n"
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

# (3) 응답 안에서 영화 목록 추출 및 빈 데이터 체크
box_office_result = data.get("boxOfficeResult", {})
movie_list = box_office_result.get("dailyBoxOfficeList", [])

if not movie_list:
    st.warning("⚠️ 어제자 영화 박스오피스 목록 데이터가 비어 있습니다.")
    st.info(
        "**[확인할 사항]**\n"
        "1. 아직 KOBIS 서버에서 어제자 관객수 집계가 완료되지 않았을 수 있습니다.\n"
        "2. 잠시 후 다시 접속하여 확인해 주세요."
    )
    st.stop()

# 6. 데이터 가공 (문자열 -> 숫자 변환)
df = pd.DataFrame(movie_list)

# 숫자로 변환할 컬럼 목록
numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]

for col in numeric_columns:
    if col in df.columns:
        # 문자열을 정수(int)형으로 변환 (오류 발생 시 0으로 대체)
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# 컬럼명 한국어로 매핑 및 필요한 항목만 추출
column_mapping = {
    "rank": "순위",
    "movieNm": "영화명",
    "openDt": "개봉일",
    "audiCnt": "관객수",
    "audiAcc": "누적관객",
    "scrnCnt": "스크린수"
}

df_display = df[list(column_mapping.keys())].rename(columns=column_mapping)

# 순위 기준으로 정렬
df_display = df_display.sort_values(by="순위", ascending=True)

# 7. 1위 영화 강조 지표 카드 세 장
top1_movie = df_display.iloc[0]

st.subheader("🏆 어제 1위 영화")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="영화 제목", value=top1_movie["영화명"])

with col2:
    st.metric(label="어제 관객수", value=f"{top1_movie['관객수']:,} 명")

with col3:
    st.metric(label="누적 관객수", value=f"{top1_movie['누적관객']:,} 명")

st.divider()

# 8. 관객수 상위 5편 막대그래프
st.subheader("📊 관객수 상위 5개 영화")
top5_df = df_display.head(5)

# 영화명을 기준(X축)으로 어제 관객수(Y축)를 시각화
st.bar_chart(
    data=top5_df,
    x="영화명",
    y="관객수",
    use_container_width=True
)

st.divider()

# 9. 전체 박스오피스 순위 표
st.subheader("📋 전체 순위표")

# 표 형식으로 출력하면서 숫자에 천 단위 쉼표(,) 및 단위 추가
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
