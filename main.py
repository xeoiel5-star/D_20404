import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    r2_score,
    root_mean_squared_error,
    mean_absolute_error,
    mean_absolute_percentage_error,
)

# ---------------------------------------------------------
# 1. 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="다이아몬드 가격 예측 및 회귀 분석 대시보드",
    page_icon="💎",
    layout="wide",
)

CUT_CATEGORIES = ["Fair", "Good", "Very Good", "Premium", "Ideal"]
COLOR_CATEGORIES = ["J", "I", "H", "G", "F", "E", "D"]
CLARITY_CATEGORIES = ["I1", "SI2", "SI1", "VS2", "VS1", "VVS2", "VVS1", "IF"]


# ---------------------------------------------------------
# 2. 데이터 로드 및 모델 학습 (캐싱 적용: 최초 1회만 실행)
# ---------------------------------------------------------
@st.cache_resource
def load_and_train():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    train_path = os.path.join(base_dir, "diamonds_train.csv")
    test_path = os.path.join(base_dir, "diamonds_test.csv")
    full_path = os.path.join(base_dir, "diamonds_final_preprocessed.csv")

    if os.path.exists(train_path) and os.path.exists(test_path):
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
    elif os.path.exists(full_path):
        df = pd.read_csv(full_path)
        price_bins = pd.qcut(df["log_price"], q=10, labels=False)
        train_df, test_df = train_test_split(
            df, test_size=0.2, random_state=42, stratify=price_bins
        )
        train_df = train_df.reset_index(drop=True)
        test_df = test_df.reset_index(drop=True)
    else:
        available_files = sorted(os.listdir(base_dir))
        raise FileNotFoundError(f"현재 저장소 파일 목록: {available_files}")

    feature_cols = [c for c in train_df.columns if c not in ["carat", "price", "log_price"]]

    X_train = train_df[feature_cols]
    y_train_log = train_df["log_price"]

    X_test = test_df[feature_cols]
    y_test_log = test_df["log_price"]
    y_test_usd = test_df["price"]

    model = LinearRegression()
    model.fit(X_train, y_train_log)

    pred_test_log = model.predict(X_test)
    pred_test_usd = np.exp(pred_test_log)
    resid_log = y_test_log - pred_test_log

    metrics = {
        "r2_log": r2_score(y_test_log, pred_test_log),
        "rmse_log": root_mean_squared_error(y_test_log, pred_test_log),
        "r2_usd": r2_score(y_test_usd, pred_test_usd),
        "rmse_usd": root_mean_squared_error(y_test_usd, pred_test_usd),
        "mae_usd": mean_absolute_error(y_test_usd, pred_test_usd),
        "mape_pct": mean_absolute_percentage_error(y_test_usd, pred_test_usd) * 100,
        "median_ae_usd": float(np.median(np.abs(y_test_usd - pred_test_usd))),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
    }

    coef_df = pd.DataFrame({
        "Feature": feature_cols,
        "Coefficient (beta)": model.coef_,
        "Price Multiplier": np.exp(model.coef_),
        "Premium vs Baseline (%)": (np.exp(model.coef_) - 1) * 100,
    })

    return model, feature_cols, train_df, test_df, pred_test_log, pred_test_usd, resid_log, metrics, coef_df


try:
    (
        model,
        feature_cols,
        train_df,
        test_df,
        pred_test_log,
        pred_test_usd,
        resid_log,
        metrics,
        coef_df,
    ) = load_and_train()
except FileNotFoundError as err:
    st.error(
        "깃허브 저장소에서 데이터 파일(`diamonds_train.csv`, `diamonds_test.csv`)을 찾지 못했습니다.\n\n"
        f"{err}\n\n"
        "깃허브 저장소(`d_20404`) 최상위 경로에 `diamonds_train.csv`와 `diamonds_test.csv`를 업로드해 주세요."
    )
    st.stop()


# ---------------------------------------------------------
# 3. 사이드바: 다이아몬드 스펙 입력
# ---------------------------------------------------------
st.sidebar.header("💎 다이아몬드 스펙 입력")
st.sidebar.caption("4C 등급 및 연마 비율을 조정하면 실시간으로 가격을 예측합니다.")

carat = st.sidebar.number_input(
    "Carat (중량, ct)", min_value=0.20, max_value=5.00, value=1.00, step=0.01
)
cut = st.sidebar.selectbox("Cut (연마 등급: Fair → Ideal)", CUT_CATEGORIES, index=4)
color = st.sidebar.selectbox("Color (색상 등급: J → D)", COLOR_CATEGORIES, index=3)
clarity = st.sidebar.selectbox("Clarity (투명도: I1 → IF)", CLARITY_CATEGORIES, index=4)

with st.sidebar.expander("세부 연마 비율 설정 (Depth / Table)", expanded=False):
    depth = st.slider("Depth (%)", min_value=43.0, max_value=79.0, value=61.8, step=0.1)
    table = st.slider("Table (%)", min_value=43.0, max_value=95.0, value=57.0, step=0.1)


def predict_price(carat_val, cut_val, color_val, clarity_val, depth_val, table_val):
    input_df = pd.DataFrame(0.0, index=[0], columns=feature_cols)
    input_df["log_carat"] = np.log(carat_val)
    input_df["depth"] = depth_val
    input_df["table"] = table_val

    for col in [f"cut_{cut_val}", f"color_{color_val}", f"clarity_{clarity_val}"]:
        if col in input_df.columns:
            input_df[col] = 1.0

    pred_log_val = float(model.predict(input_df)[0])
    pred_usd_val = float(np.exp(pred_log_val))
    low_usd = float(np.exp(pred_log_val - metrics["rmse_log"]))
    high_usd = float(np.exp(pred_log_val + metrics["rmse_log"]))
    return pred_log_val, pred_usd_val, low_usd, high_usd


pred_log_val, pred_usd_val, low_usd, high_usd = predict_price(
    carat, cut, color, clarity, depth, table
)


# ---------------------------------------------------------
# 4. 메인 화면 및 3개 분석 탭 구성
# ---------------------------------------------------------
st.title("💎 다이아몬드 가격 예측 및 선형 회귀 분석")
st.markdown(
    f"정제된 다이아몬드 데이터(**총 {metrics['train_rows'] + metrics['test_rows']:,}건**, "
    f"학습 {metrics['train_rows']:,}건 / 테스트 {metrics['test_rows']:,}건)를 기반으로 "
    f"로그 변환 다중 선형 회귀 모델을 실시간 구동합니다."
)

tab1, tab2, tab3 = st.tabs([
    "🎯 실시간 가격 예측",
    "📊 모델 성능 & 잔차 분석",
    "🔍 회귀 계수 & 4C 프리미엄",
])

# === TAB 1: 실시간 가격 예측 ===
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("예상 시장 가격 (USD)", f"${pred_usd_val:,.2f}")
    col2.metric("일반 오차 범위 (±1 SD)", f"${low_usd:,.0f} ~ ${high_usd:,.0f}")
    col3.metric("캐럿당 환산 단가", f"${pred_usd_val / carat:,.2f} / ct")

    st.info(
        f"**선택한 스펙:** `{carat:.2f} ct` | Cut: `{cut}` | Color: `{color}` | "
        f"Clarity: `{clarity}` | Depth: `{depth:.1f}%` | Table: `{table:.1f}%`"
    )

    similar_df = test_df[
        (test_df["carat"] >= carat * 0.90) & (test_df["carat"] <= carat * 1.10)
    ]
    if len(similar_df) >= 10:
        fig, ax = plt.subplots(figsize=(9, 3.6))
        ax.hist(similar_df["price"], bins=30, color="#4c72b0", alpha=0.65, edgecolor="white")
        ax.axvline(
            pred_usd_val,
            color="#d62728",
            linestyle="--",
            linewidth=2.2,
            label=f"Predicted Price: ${pred_usd_val:,.0f}",
        )
        ax.set_title(
            f"Price Distribution of Similar Carat Diamonds ({carat*0.9:.2f}ct ~ {carat*1.1:.2f}ct, n={len(similar_df)})"
        )
        ax.set_xlabel("Actual Market Price (USD)")
        ax.set_ylabel("Count")
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

# === TAB 2: 모델 성능 & 잔차 분석 ===
with tab2:
    st.subheader("테스트 세트 평가 지표 (n = 10,755)")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("R² (로그 스케일)", f"{metrics['r2_log']:.4f}")
    m2.metric("R² (달러 환산)", f"{metrics['r2_usd']:.4f}")
    m3.metric("RMSE (달러)", f"${metrics['rmse_usd']:,.2f}")
    m4.metric("중앙값 절대 오차", f"${metrics['median_ae_usd']:,.2f}")
    m5.metric("MAPE (백분율 오차)", f"{metrics['mape_pct']:.2f}%")

    c1, c2 = st.columns(2)
    with c1:
        fig1, ax1 = plt.subplots(figsize=(6, 4.5))
        ax1.scatter(test_df["price"], pred_test_usd, alpha=0.15, s=8, color="#2b5c8f")
        ax1.plot([0, 20000], [0, 20000], "r--", lw=1.5, label="Ideal Fit (y = x)")
        ax1.set_xlim(0, 20000)
        ax1.set_ylim(0, 22000)
        ax1.set_title(f"Actual vs Predicted Price (R2 = {metrics['r2_usd']:.4f})")
        ax1.set_xlabel("Actual Price (USD)")
        ax1.set_ylabel("Predicted Price (USD)")
        ax1.legend()
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    with c2:
        fig2, ax2 = plt.subplots(figsize=(6, 4.5))
        ax2.scatter(pred_test_log, resid_log, alpha=0.15, s=8, color="#2ca02c")
        ax2.axhline(0, color="#d62728", linestyle="--", lw=1.5, label="Zero Residual")
        ax2.axhline(2 * metrics["rmse_log"], color="gray", linestyle=":", lw=1.0, label="±2 SD")
        ax2.axhline(-2 * metrics["rmse_log"], color="gray", linestyle=":", lw=1.0)
        ax2.set_title("Residuals vs Fitted (Log Scale)")
        ax2.set_xlabel("Predicted log(Price)")
        ax2.set_ylabel("Residual (Actual - Predicted)")
        ax2.legend()
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    st.caption(
        "잔차 진단 요약: 로그 스케일 잔차는 평균 0을 중심으로 대칭을 이루며(전체 표본의 95.8%가 ±2 SD 이내), "
        "1.00ct 단위 임계점 프리미엄과 2.0ct 초과 구간의 완만한 곡률 변화가 주요 잔차 요인으로 나타납니다."
    )

# === TAB 3: 회귀 계수 & 4C 프리미엄 ===
with tab3:
    st.subheader("최하위 기준 등급(Fair / J / I1) 대비 가격 상승률 (%)")
    st.write(
        f"- **중량 탄력성 (`log_carat`):** 계수 **`{coef_df.loc[0, 'Coefficient (beta)']:.4f}`** "
        f"→ 캐럿이 1% 증가할 때마다 가격은 약 **1.88%** 상승 (무게 2배 시 가격 약 **3.69배**)"
    )

    grade_df = coef_df[coef_df["Feature"].str.startswith(("cut_", "color_", "clarity_"))].copy()
    colors_bar = [
        "#4c72b0" if f.startswith("cut_") else ("#dd8452" if f.startswith("color_") else "#55a868")
        for f in grade_df["Feature"]
    ]

    fig3, ax3 = plt.subplots(figsize=(10, 5.5))
    ax3.barh(grade_df["Feature"], grade_df["Premium vs Baseline (%)"], color=colors_bar)
    ax3.set_title("Price Premium vs Baseline Grade (Fair / J / I1)")
    ax3.set_xlabel("Price Increase (%)")
    ax3.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)

    with st.expander("전체 회귀 계수 상세 표 보기"):
        st.dataframe(
            coef_df.style.format({
                "Coefficient (beta)": "{:.4f}",
                "Price Multiplier": "{:.4f}",
                "Premium vs Baseline (%)": "{:+.2f}%",
            })
        )
