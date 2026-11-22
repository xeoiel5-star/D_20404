import streamlit as st
import pandas as pd
import numpy as np
import joblib

# 1. 모델 및 메타데이터 로드
@st.cache_resource
def load_model():
    return joblib.load('diamond_price_model.joblib')

artifact = load_model()
model = artifact['model']
feature_cols = artifact['feature_cols']

# 2. 웹앱 화면 구성
st.title("💎 다이아몬드 가격 예측기")
st.write("다이아몬드의 4C 및 연마 비율을 입력하면 머신러닝 모델이 적정 가격(USD)을 예측합니다.")

st.sidebar.header("다이아몬드 스펙 입력")
# 수치형 데이터 입력
carat = st.sidebar.number_input("Carat (중량)", min_value=0.2, max_value=5.0, value=1.0, step=0.01)
depth = st.sidebar.slider("Depth (%)", min_value=43.0, max_value=79.0, value=61.8, step=0.1)
table = st.sidebar.slider("Table (%)", min_value=43.0, max_value=95.0, value=57.0, step=0.1)

# 범주형 데이터 입력
cut = st.sidebar.selectbox("Cut (연마 등급)", artifact['cut_categories'])
color = st.sidebar.selectbox("Color (색상)", artifact['color_categories'])
clarity = st.sidebar.selectbox("Clarity (투명도)", artifact['clarity_categories'])

# 3. 예측 실행
if st.sidebar.button("가격 예측하기"):
    # 입력용 빈 데이터프레임 생성 (모든 값을 0으로 초기화)
    input_data = pd.DataFrame(0.0, index=[0], columns=feature_cols)
    
    # 수치형 변수 맵핑 (로그 변환 포함)
    input_data['log_carat'] = np.log(carat)
    input_data['depth'] = depth
    input_data['table'] = table
    
    # 범주형 변수 맵핑 (One-Hot Encoding 방식)
    if f'cut_{cut}' in feature_cols:
        input_data[f'cut_{cut}'] = 1.0
    if f'color_{color}' in feature_cols:
        input_data[f'color_{color}'] = 1.0
    if f'clarity_{clarity}' in feature_cols:
        input_data[f'clarity_{clarity}'] = 1.0
        
    # 모델 예측 및 지수 변환(달러 환산)
    pred_log = model.predict(input_data)[0]
    pred_usd = np.exp(pred_log)
    
    st.success(f"### 🎯 예상 가격: **${pred_usd:,.2f}**")
    st.info(f"💡 모델 평가 성능: R² {artifact['metrics']['r2_usd']:.3f} / 평균 오차 {artifact['metrics']['mape_pct']:.1f}%")
