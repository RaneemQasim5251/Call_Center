# -*- coding: utf-8 -*-
import os, glob, io, base64, re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ========== (إضافة جديدة) سكikit-learn اختياري للتنبؤ ==========
_SK_OK = True
try:
    from sklearn.linear_model import LinearRegression
except Exception:
    _SK_OK = False
# ============================================================

# =============== إعداد عام + شعار ===============
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(APP_DIR, "assets")
LOGO_DIR = ASSETS_DIR
LOGO_FILE_CANDIDATES = ["Aljeri-logo.png.png","logo.jpg","logo.jpeg","logo.svg"]

def read_logo_bytes():
    if os.path.isdir(LOGO_DIR):
        for name in LOGO_FILE_CANDIDATES:
            p = os.path.join(LOGO_DIR, name)
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    return f.read()
    if os.path.isfile(LOGO_DIR):
        with open(LOGO_DIR, "rb") as f:
            return f.read()
    return None

logo_bytes = read_logo_bytes()

st.set_page_config(page_title="تقرير قسم خدمة العملاء 2025", page_icon="📞", layout="wide")

DARK_GLASS_CSS = """
<style>
html, body, [data-testid="stAppViewContainer"], .block-container { direction: rtl; }
[data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 800px at 0% 0%, rgba(40,45,60,0.55) 0%, rgba(15,18,25,0.95) 60%),
              radial-gradient(1000px 700px at 100% 0%, rgba(30,35,50,0.55) 0%, rgba(15,18,25,0.95) 60%);
  backdrop-filter: blur(18px);
}
.block-container { padding-top: 1.2rem; max-width: 1400px; }
.glass {
  background: linear-gradient(180deg, rgba(255,255,255,0.09), rgba(255,255,255,0.03));
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  backdrop-filter: blur(18px);
  border-radius: 18px; padding: 1.1rem 1.2rem;
}
h1, h2, h3, h4, h5 { color: #ECF2FF !important; letter-spacing: .3px; }
body, p, div, label, span { color: #E3E9F5 !important; }
.header-flex { display:flex; align-items:center; justify-content:space-between; padding:.8rem 1rem; margin-bottom:.6rem; }
.header-left { display:flex; gap:.75rem; align-items:center; flex-direction:row-reverse; }
.logo-box {
  width: 84px; height: 84px; border-radius: 18px; overflow:hidden;
  background:linear-gradient(145deg,#0b1222,#0f172a);
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 12px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06);
}
.logo-box img { width:100%; height:100%; object-fit:contain; }
.kpi {
  position: relative; border-radius: 18px; padding: 1rem; text-align: center; min-height: 150px;
  display:flex; flex-direction:column; justify-content:center;
  background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
  border: 1px solid rgba(255,255,255,0.14);
  box-shadow: 0 18px 40px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05);
}
.kpi .title { color:#9FB3C8; font-size:.95rem; margin-bottom:.35rem; }
.kpi .value { font-size:2rem; font-weight:800; color:#F5FAFF; line-height:1.15; }
.badge {
  display:inline-block; padding:.25rem .55rem; border-radius:999px; font-size:.85rem;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.16); color: #cfe4ff;
}
hr { border:none; height:1px; background:rgba(255,255,255,0.12); margin:12px 0; }
</style>
"""
st.markdown(DARK_GLASS_CSS, unsafe_allow_html=True)

if logo_bytes:
    b64 = base64.b64encode(logo_bytes).decode("utf-8")
    logo_img_html = f'<div class="logo-box"><img src="data:image/png;base64,{b64}" alt="logo"/></div>'
else:
    logo_img_html = '<div class="logo-box"><span style="font-size:26px;">📞</span></div>'

st.markdown(
    f"""
    <div class="glass header-flex">
      <div class="header-left">
        <div>
          <h2 style="margin:0;">تقرير قسم خدمة العملاء 2025</h2>
          <div style="color:#9FB3C8;margin-top:-4px;font-size:.95rem;">عرض تفاعلي للمؤشرات والرسوم والخريطة</div>
        </div>
      </div>
      {logo_img_html}
    </div>
    """,
    unsafe_allow_html=True
)

# =============== إعداد الشهور وترجَمات الأسماء ===============
MONTH_ORDER = ["Aug", "Sep", "Oct"]  # المعتمدة الآن
MONTH_INDEX = {m:i for i,m in enumerate(MONTH_ORDER)}
MONTH_MAP = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
INV_MONTH_MAP = {v:k for k,v in MONTH_MAP.items()}

PROVIDER_AR = {
    "Aljauhara": "الجوهرة",
    "Reem": "ريم",
    "Ahad": "عهد",
    "Shouq": "شوق",
    "Abdulmageed": "عبدالمجيد",
    "Abdulkareem": "عبدالكريم",
}
def provider_to_ar(name: str) -> str:
    return PROVIDER_AR.get(name, name)

def ar_to_provider(ar_name: str) -> str:
    rev = {v:k for k,v in PROVIDER_AR.items()}
    return rev.get(ar_name, ar_name)

# --- توحيد قيم الشهر (Oct/October/أكتوبر… -> Oct) ---
MONTH_SYNONYMS = {
    "aug": "Aug", "aug.": "Aug", "august": "Aug", "أغسطس": "Aug", "اغسطس": "Aug",
    "sep": "Sep", "sep.": "Sep", "september": "Sep", "سبتمبر": "Sep",
    "oct": "Oct", "oct.": "Oct", "october": "Oct", "أكتوبر": "Oct", "اكتوبر": "Oct",
}
def normalize_month_value(val, dt):
    s = (str(val).strip() if val is not None else "").lower()
    if s in MONTH_SYNONYMS:
        canon = MONTH_SYNONYMS[s]
        return canon if canon in MONTH_ORDER else np.nan
    if pd.notna(dt):
        mnum = int(dt.month); canon = INV_MONTH_MAP.get(mnum)
        return canon if canon in MONTH_ORDER else np.nan
    if len(s) >= 3 and s[:3].title() in MONTH_MAP:
        canon = s[:3].title()
        return canon if canon in MONTH_ORDER else np.nan
    return np.nan

# =============== توحيد الأعمدة ===============
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.rename(columns=lambda c: str(c).strip())
    mapping = {
        "التاريخ ": "التاريخ",
        "Date": "التاريخ", "date": "التاريخ",
        "المنطقه": "المنطقة",
        "المدينه ": "المدينة", "المدينه": "المدينة",
        "الخدمة المطلوبة": "الخدمه المطلوبه",
        "نوع الخدمه": "نوع الخدمة",
        "اسم العميل ": "اسم العميل",
        "رقم الجوال ": "رقم الجوال",
    }
    df = df.rename(columns={c: mapping.get(c, c) for c in df.columns})
    return df

# =============== بناء التاريخ من (الشهر + اليوم) ===============
def build_date_from_month_day(row: pd.Series):
    m = str(row.get("الشهر","")).strip()
    raw = str(row.get("التاريخ","")).strip()
    if raw and ("/" in raw or "-" in raw):
        dt = pd.to_datetime(raw, dayfirst=True, errors="coerce")
        if pd.notna(dt): return dt
    if m in MONTH_MAP:
        try:
            day = int(float(raw)) if raw else 1
            return pd.Timestamp(year=2025, month=MONTH_MAP[m], day=day)
        except Exception:
            return pd.NaT
    return pd.NaT

# =============== أسابيع الأحد→الخميس وترقيمها داخل الشهر ===============
def add_week_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "التاريخ/Date" not in df.columns:
        df["ISO_Year"]=np.nan; df["ISO_Week"]=np.nan
        df["WeekStart"]=pd.NaT; df["WeekEnd"]=pd.NaT
        df["رقم الأسبوع"]=np.nan; df["وسم الأسبوع"]=""
        return df

    d = df.copy()
    wd = d["التاريخ/Date"].dt.weekday              # Monday=0..Sunday=6
    start_offset = (wd + 1) % 7                     # للأحد
    d["WeekStart"] = d["التاريخ/Date"] - pd.to_timedelta(start_offset, unit="D")
    d["WeekEnd"]   = d["WeekStart"] + pd.to_timedelta(4, unit="D")  # الخميس

    d["ISO_Year"]  = d["WeekStart"].dt.isocalendar().year
    d["ISO_Week"]  = d["WeekStart"].dt.isocalendar().week

    if "الشهر" in d.columns:
        def rank_weeks_in_month(g):
            mnum = MONTH_MAP.get(g.name, None)
            if not mnum:
                gg=g.copy(); gg["رقم الأسبوع"]=np.nan; gg["وسم الأسبوع"]=""
                return gg

            year = 2025
            month_start = pd.Timestamp(year=year, month=mnum, day=1)
            next_month = mnum + 1 if mnum < 12 else 1
            next_year  = year + 1 if mnum == 12 else year
            month_end  = pd.Timestamp(year=next_year, month=next_month, day=1) - pd.Timedelta(days=1)

            weeks = (
                g.dropna(subset=["WeekStart","WeekEnd"])
                 .loc[
                  ((g["WeekStart"]>=month_start)&(g["WeekStart"]<=month_end)) |
                  ((g["WeekEnd"]  >=month_start)&(g["WeekEnd"]  <=month_end))
                 , ["WeekStart","WeekEnd"]]
                 .drop_duplicates()
                 .sort_values("WeekStart")
                 .reset_index(drop=True)
            )
            weeks["rank"] = range(1, len(weeks)+1)
            rank_map = {ws:int(r) for ws,r in zip(weeks["WeekStart"], weeks["rank"])}

            def label(ws,we):
                if pd.isna(ws) or pd.isna(we): return ""
                r = rank_map.get(ws, np.nan)
                return f"الأسبوع {r} ({ws.strftime('%b %d')}–{we.strftime('%b %d')})"

            gg = g.copy()
            gg["رقم الأسبوع"] = gg["WeekStart"].map(rank_map).astype("float")
            gg["وسم الأسبوع"] = [label(ws,we) for ws,we in zip(gg["WeekStart"], gg["WeekEnd"])]
            return gg

        d = d.groupby("الشهر", group_keys=False).apply(rank_weeks_in_month)
    else:
        d["رقم الأسبوع"]=np.nan; d["وسم الأسبوع"]=""

    return d

# =============== تحميل كل CSV مع معالجة الأخطاء ===============
@st.cache_data(show_spinner=True)
def load_all(folder="data"):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    datasets = {}
    for path in files:
        provider = os.path.splitext(os.path.basename(path))[0].strip()

        df = None
        err_msg = None
        for attempt in range(2):
            try:
                df = pd.read_csv(
                    path,
                    encoding="utf-8-sig",
                    engine="python",
                    on_bad_lines="skip",
                    sep=",",
                    quotechar='"',
                    skipinitialspace=True
                )
                break
            except Exception as e:
                err_msg = str(e)

        if df is None:
            st.error(f"تعذّر قراءة {os.path.basename(path)} — {err_msg}")
            continue

        if df.empty:
            st.warning(f"الملف {os.path.basename(path)} فارغ بعد التنظيف.")
            continue

        # نظافة أساسية
        df.dropna(how="all", inplace=True)
        df = normalize_columns(df)

        # تاريخ موحّد
        df["التاريخ/Date"] = pd.to_datetime(df.apply(build_date_from_month_day, axis=1), errors="coerce")

        # --- الشهر: توحيد قوي قبل الحصر ---
        orig_month_col = df["الشهر"] if "الشهر" in df.columns else pd.Series([None]*len(df))
        df["الشهر"] = [normalize_month_value(m, dt) for m, dt in zip(orig_month_col, df["التاريخ/Date"])]
        df["الشهر"] = df["الشهر"].where(df["الشهر"].isin(MONTH_ORDER), np.nan)

        # توحيد النصوص
        for col in ["اسم العميل","رقم الجوال","المنطقة","المدينة","الشركة","نوع الخدمة","الخدمه المطلوبه","الشهر"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # بناء أسابيع العمل
        df = add_week_columns(df)

        # مصدر الملف
        df["مقدم الخدمة (ملف)"] = provider
        datasets[provider] = df

        if err_msg is not None:
            st.warning(f"تم تخطّي أسطر تالفة في {os.path.basename(path)} للحفاظ على عمل التطبيق.")

    if datasets:
        all_df = pd.concat(list(datasets.values()), ignore_index=True, sort=False)
        datasets["__ALL__"] = all_df

    return datasets

datasets = load_all()
if not datasets:
    st.error("لا يوجد أي CSV داخل data/. أضيفي الملفات ثم أعيدي التحميل.")
    st.stop()

# =============== المرشّحات ===============
providers = [k for k in datasets.keys() if k != "__ALL__"]
providers_ar = ["الكل"] + [provider_to_ar(p) for p in providers]

with st.form("main_filters"):
    c1, c2, c3 = st.columns([1.2, 1.2, 1.2])

    with c1:
        st.markdown('<div class="glass"><b>مقدّم الخدمة</b>', unsafe_allow_html=True)
        provider_choice_ar = st.selectbox("اختر", providers_ar, index=0)
        st.markdown('</div>', unsafe_allow_html=True)

    # نطاق البيانات حسب مقدم الخدمة
    if provider_choice_ar == "الكل":
        provider_key = "__ALL__"
        df_scope = datasets["__ALL__"].copy()
    else:
        provider_key = ar_to_provider(provider_choice_ar)
        df_scope = datasets.get(provider_key, pd.DataFrame()).copy()

    with c2:
        st.markdown('<div class="glass"><b>تصفية حسب الشهر</b>', unsafe_allow_html=True)
        months_av = []
        if "الشهر" in df_scope.columns:
            months_av = [m for m in MONTH_ORDER if m in df_scope["الشهر"].dropna().unique().tolist()]
        month_choice = st.selectbox("اختر الشهر", ["الكل"] + months_av, index=0)
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="glass"><b>تصفية حسب الأسبوع داخل الشهر</b>', unsafe_allow_html=True)
        # الأسبوع يظهر دائمًا: نجمع أسابيع نطاق df_scope ثم نقيّد إذا تم اختيار شهر
        week_options = ["الكل"]
        tmp = df_scope.copy()
        if month_choice != "الكل":
            tmp = tmp[tmp["الشهر"] == month_choice]
        if "وسم الأسبوع" in tmp.columns and not tmp.empty:
            uniq = (
                tmp.dropna(subset=["WeekStart","WeekEnd"])
                   .drop_duplicates(subset=["WeekStart"])
                   .sort_values(["WeekStart"])
            )
            week_options += uniq["وسم الأسبوع"].tolist()
        week_choice = st.selectbox("اختر الأسبوع", week_options, index=0)
        st.markdown('</div>', unsafe_allow_html=True)

    st.form_submit_button("تطبيق المرشّحات ✅")

# =============== تطبيق التصفية ===============
filtered = df_scope.copy()
if month_choice != "الكل":
    filtered = filtered[filtered["الشهر"] == month_choice]
if week_choice != "الكل" and "وسم الأسبوع" in filtered.columns:
    filtered = filtered[filtered["وسم الأسبوع"] == week_choice]

# =============== KPI + المتوسطات الديناميكية ===============
total_calls = int(len(filtered))

def top_month_in_scope(df):
    if df.empty or "الشهر" not in df.columns: return None, 0
    s = df["الشهر"].value_counts().sort_values(ascending=False)
    return (s.index[0], int(s.iloc[0])) if len(s) else (None, 0)

def average_for_selection(df: pd.DataFrame, month_choice: str, week_choice: str):
    """
    - إذا تم اختيار أسبوع: متوسط المكالمات اليومي (أحد–خميس).
    - إذا تم اختيار شهر فقط: متوسط المكالمات الأسبوعي داخل هذا الشهر.
    - إذا لم يُحدَّد شهر/أسبوع: متوسط المكالمات الشهري على النطاق الحالي.
    """
    if df.empty: return 0.0, "—"

    if week_choice != "الكل":
        if "WeekStart" not in df.columns or "WeekEnd" not in df.columns:
            return 0.0, "—"
        wdf = df[df["وسم الأسبوع"] == week_choice].copy()
        if wdf.empty:
            return 0.0, "—"
        ws = pd.to_datetime(wdf["WeekStart"].iloc[0])
        we = pd.to_datetime(wdf["WeekEnd"].iloc[0])
        day_count = max(1, min(int((we - ws).days) + 1, 5))  # أحد..خميس
        avg_per_day = len(wdf) / day_count
        return float(avg_per_day), f"متوسط المكالمات اليومي — {ws.strftime('%b %d')}–{we.strftime('%b %d')}"

    if month_choice != "الكل":
        if "WeekStart" not in df.columns:
            return 0.0, "—"
        mdf = df[df["الشهر"] == month_choice]
        if mdf.empty:
            return 0.0, "—"
        week_sizes = mdf.groupby("WeekStart").size()
        if len(week_sizes) == 0:
            return 0.0, "—"
        return float(week_sizes.mean()), f"متوسط المكالمات الأسبوعي — شهر {month_choice}"

    if "الشهر" in df.columns:
        month_sizes = df.groupby("الشهر").size()
        if len(month_sizes)==0: return 0.0, "—"
        return float(month_sizes.mean()), "متوسط المكالمات الشهري — النطاق الحالي"

    return 0.0, "—"

k1,k2,k3 = st.columns(3)
with k1:
    scope_title = "جميع الملفات" if provider_key=="__ALL__" else f"الملف: {provider_to_ar(provider_key)}"
    st.markdown(f"""<div class="kpi">
        <div class="title">إجمالي الاتصالات — {scope_title}</div>
        <div class="value">{total_calls}</div>
    </div>""", unsafe_allow_html=True)

m_name, m_val = top_month_in_scope(filtered if provider_key=="__ALL__" else datasets[provider_key])
with k2:
    st.markdown(f"""<div class="kpi">
        <div class="title">أعلى شهر ضمن النطاق</div>
        <div class="value">{m_name or '—'}</div>
        <div class="badge">عدد: {m_val}</div>
    </div>""", unsafe_allow_html=True)

avg_val, avg_label = average_for_selection(filtered, month_choice, week_choice)
with k3:
    st.markdown(f"""<div class="kpi">
        <div class="title">المتوسط (حسب التصفية)</div>
        <div class="value">{round(avg_val,2)}</div>
        <div class="badge">{avg_label}</div>
    </div>""", unsafe_allow_html=True)

# =============== (إضافة جديدة) KPI لتوقّع الشهر القادم ===============
def calc_forecast(df_month_scope: pd.DataFrame):
    """
    يبني إجمالي شهري من df_month_scope (قبل ترشيح الأسبوع)،
    ثم يطبّق LinearRegression إن توفرت، أو تقدير بسيط إن لم تتوفر.
    """
    if df_month_scope is None or df_month_scope.empty or "الشهر" not in df_month_scope.columns:
        return None, None, None

    month_totals = df_month_scope["الشهر"].value_counts().reindex(MONTH_ORDER).dropna()
    if len(month_totals) < 1:
        return None, None, None

    x = np.array([MONTH_INDEX[m] for m in month_totals.index]).reshape(-1,1)
    y = month_totals.values.astype(float)

    # نموذج خطي مع نطاق تقريبي
    if _SK_OK and len(y) >= 2:
        model = LinearRegression().fit(x, y)
        next_x_val = x[-1][0] + 1
        pred = float(model.predict(np.array([[next_x_val]]) )[0])
        resid = y - model.predict(x)
        sigma = float(np.std(resid)) if len(resid) > 1 else 0.0
        ci_low = max(0.0, pred - 1.96*sigma)
        ci_high = pred + 1.96*sigma
        return int(round(pred)), int(round(ci_low)), int(round(ci_high))

    # تقدير مبسّط
    if len(y) >= 2:
        growth = y[-1] - y[-2]
        pred = int(round(y[-1] + growth))
        return pred, None, None

    return None, None, None

# نحسب التنبؤ على نطاق مقدّم الخدمة المختار (بدون تقييد الأسبوع؛ مع بقاء تقييد الشهر = الكل لكي يكون شهري شامل)
df_for_forecast = df_scope.copy()
pred_next, pred_ci_low, pred_ci_high = calc_forecast(df_for_forecast)

# بطاقة KPI للتنبؤ (سطر مستقل مباشرة بعد الـKPI الحالية)
c_pred = st.columns(1)[0]
with c_pred:
    if pred_next is not None:
        ci_html = f'<div class="badge" style="margin-top:.35rem;">نطاق تقريبي: {pred_ci_low} – {pred_ci_high}</div>' if (pred_ci_low is not None and pred_ci_high is not None) else ""
        st.markdown(f"""<div class="kpi" style="margin-top:.5rem;">
            <div class="title">توقّع الشهر القادم (حسب نطاق مقدّم الخدمة المختار)</div>
            <div class="value">{pred_next}</div>
            {ci_html}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="kpi" style="margin-top:.5rem;">
            <div class="title">توقّع الشهر القادم</div>
            <div class="value">—</div>
            <div class="badge" style="margin-top:.35rem;">البيانات غير كافية</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# =============== الرسوم ===============
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.markdown("### الرسوم")
c1, c2 = st.columns(2)
with c1:
    if "المنطقة" in filtered.columns and not filtered.empty:
        reg_counts = filtered["المنطقة"].value_counts().reset_index()
        reg_counts.columns = ["المنطقة","العدد"]
        fig_reg = px.bar(reg_counts, x="المنطقة", y="العدد", title="توزيع الاتصالات حسب المنطقة", text="العدد")
        fig_reg.update_traces(textposition="outside")
        fig_reg.update_layout(template="plotly_dark", margin=dict(t=60,b=40,l=20,r=20))
        st.plotly_chart(fig_reg, use_container_width=True)
    else:
        st.info("لا تتوفر بيانات مناطق ضمن النطاق المحدد.")
with c2:
    if "نوع الخدمة" in filtered.columns and not filtered.empty:
        tcounts = filtered["نوع الخدمة"].value_counts()
        fig_type = px.pie(names=tcounts.index, values=tcounts.values, title="نسبة أنواع الاتصالات", hole=0.35)
        fig_type.update_traces(textposition="inside", textinfo="percent+label")
        fig_type.update_layout(template="plotly_dark", margin=dict(t=60,b=40,l=20,r=20))
        st.plotly_chart(fig_type, use_container_width=True)
    else:
        st.info("لا تتوفر بيانات لأنواع الاتصالات ضمن النطاق المحدد.")
if "الشركة" in filtered.columns and not filtered.empty:
    comp_counts = filtered["الشركة"].value_counts().reset_index()
    comp_counts.columns = ["الشركة","العدد"]
    fig_comp = px.bar(comp_counts, x="الشركة", y="العدد", title="عدد الاتصالات حسب الشركة", text="العدد")
    fig_comp.update_traces(textposition="outside")
    fig_comp.update_layout(template="plotly_dark", margin=dict(t=60,b=40,l=20,r=20))
    st.plotly_chart(fig_comp, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# =============== توزيع الاتصالات حسب مقدّم الخدمة (3 Pies) ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### نسبة الاتصالات حسب مقدّم الخدمة")

agent_col = "مقدم الخدمة (ملف)" if "مقدم الخدمة (ملف)" in df_scope.columns else ("مقدم الخدمة" if "مقدم الخدمة" in df_scope.columns else None)

if agent_col:
    col_total, col_oct, col_week = st.columns(3)

    # --- 1) الإجمالي (حسب التصفية الحالية) ---
    with col_total:
        if not filtered.empty:
            ac_total = filtered[agent_col].value_counts()
            if not ac_total.empty:
                names_total = ac_total.index.map(provider_to_ar) if agent_col == "مقدم الخدمة (ملف)" else ac_total.index
                fig_agents_total = px.pie(
                    names=names_total, values=ac_total.values,
                    title="إجمالي نسبة الاتصالات (حسب التصفية الحالية)", hole=0.35
                )
                fig_agents_total.update_traces(textposition="inside", textinfo="percent+label")
                fig_agents_total.update_layout(template="plotly_dark", margin=dict(t=60,b=40,l=20,r=20))
                st.plotly_chart(fig_agents_total, use_container_width=True)
            else:
                st.info("لا تتوفر بيانات لمقدّمي الخدمة ضمن التصفية الحالية.")
        else:
            st.info("لا توجد بيانات بعد تطبيق التصفية الحالية.")

    # --- 2) شهر Oct (يحترم اختيار مقدّم الخدمة، لا يتأثر بمرشح الشهر/الأسبوع) ---
    with col_oct:
        df_oct_scope = df_scope[df_scope["الشهر"] == "Oct"].copy() if "الشهر" in df_scope.columns else pd.DataFrame()
        if not df_oct_scope.empty:
            ac_oct = df_oct_scope[agent_col].value_counts()
            if not ac_oct.empty:
                names_oct = ac_oct.index.map(provider_to_ar) if agent_col == "مقدم الخدمة (ملف)" else ac_oct.index
                fig_agents_oct = px.pie(
                    names=names_oct, values=ac_oct.values,
                    title="نسبة الاتصالات — شهر أكتوبر (بنفس نطاق مقدّم الخدمة)", hole=0.35
                )
                fig_agents_oct.update_traces(textposition="inside", textinfo="percent+label")
                fig_agents_oct.update_layout(template="plotly_dark", margin=dict(t=60,b=40,l=20,r=20))
                st.plotly_chart(fig_agents_oct, use_container_width=True)
            else:
                st.info("لا توجد بيانات لشهر Oct لنفس نطاق مقدّم الخدمة.")
        else:
            st.info("لا توجد سجلات لشهر Oct في هذا النطاق.")

    # --- 3) آخر أسبوع (أحدث WeekStart) ضمن نفس نطاق مقدّم الخدمة ---
    with col_week:
        if "WeekStart" in df_scope.columns and not df_scope.dropna(subset=["WeekStart"]).empty:
            latest_ws = pd.to_datetime(df_scope["WeekStart"]).max()
            df_last_week = df_scope[pd.to_datetime(df_scope["WeekStart"]) == latest_ws].copy()
            if not df_last_week.empty:
                ac_week = df_last_week[agent_col].value_counts()
                names_week = ac_week.index.map(provider_to_ar) if agent_col == "مقدم الخدمة (ملف)" else ac_week.index
                # عنوان واضح مع نطاق الأسبوع
                we = pd.to_datetime(df_last_week["WeekEnd"].iloc[0]) if "WeekEnd" in df_last_week.columns else latest_ws + pd.Timedelta(days=4)
                week_title = f"نسبة الاتصالات — آخر أسبوع ({latest_ws.strftime('%b %d')}–{we.strftime('%b %d')})"
                fig_agents_week = px.pie(
                    names=names_week, values=ac_week.values,
                    title=week_title, hole=0.35
                )
                fig_agents_week.update_traces(textposition="inside", textinfo="percent+label")
                fig_agents_week.update_layout(template="plotly_dark", margin=dict(t=60,b=40,l=20,r=20))
                st.plotly_chart(fig_agents_week, use_container_width=True)
            else:
                st.info("لا توجد بيانات في آخر أسبوع داخل هذا النطاق.")
        else:
            st.info("لا يتوفر عمود WeekStart/WeekEnd لاستخراج آخر أسبوع.")
else:
    st.info("لا يوجد عمود لمقدّمي الخدمة في البيانات الحالية.")
st.markdown('</div>', unsafe_allow_html=True)

# =============== (إضافة جديدة) Visual: التنبؤ بالاتصالات للشهر القادم ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### التنبؤ بالاتصالات للشهر القادم")
MONTHS_12 = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def next_month_label(curr: str) -> str:
    if curr not in MONTHS_12:
        return curr
    i = MONTHS_12.index(curr)
    return MONTHS_12[(i + 1) % 12]

def forecast_figure(df_month_scope: pd.DataFrame):
    if df_month_scope is None or df_month_scope.empty or "الشهر" not in df_month_scope.columns:
        return None

    # نحافظ على ترتيب الأشهر كما في MONTH_ORDER الموجودة (Aug, Sep, Oct)
    month_totals = df_month_scope["الشهر"].value_counts().reindex(MONTH_ORDER).dropna()
    if len(month_totals) < 1:
        return None

    # x الفعلية = أسماء الأشهر الموجودة فعليًا بالترتيب
    x_labels_actual = month_totals.index.tolist()            # مثال: ['Aug','Sep','Oct']
    x_idx = np.arange(len(x_labels_actual)).reshape(-1, 1)   # 0,1,2 …
    y_val = month_totals.values.astype(float)

    # اسم الشهر القادم الحقيقي (بدون modulo)
    next_label = next_month_label(x_labels_actual[-1])

    fig = go.Figure()

    # المنحنى الفعلي
    fig.add_trace(go.Scatter(
        x=x_labels_actual, y=y_val, mode="lines+markers", name="فعلي",
        line=dict(width=3), marker=dict(size=8)
    ))

    # نموذج خطي + نقطة التنبؤ + النطاق التقريبي
    if _SK_OK and len(y_val) >= 2:
        from sklearn.linear_model import LinearRegression
        model = LinearRegression().fit(x_idx, y_val)
        next_x_numeric = np.array([[len(x_labels_actual)]])  # التالي بعد آخر نقطة فعلية
        pred = float(model.predict(next_x_numeric)[0])

        resid = y_val - model.predict(x_idx)
        sigma = float(np.std(resid)) if len(resid) > 1 else 0.0
        ci_low = max(0.0, pred - 1.96 * sigma)
        ci_high = pred + 1.96 * sigma

        # خط الاتجاه: من أول شهر فعلي إلى الشهر المتوقع
        line_x_full_num = np.arange(0, len(x_labels_actual) + 1)
        line_x_full_lbl = x_labels_actual + [next_label]
        line_y_full = model.predict(line_x_full_num.reshape(-1, 1))

        fig.add_trace(go.Scatter(
            x=line_x_full_lbl, y=line_y_full, mode="lines", name="اتجاه",
            line=dict(dash="dot", width=2)
        ))
        # نقطة التنبؤ على **Nov** (أو الشهر التالي الفعلي)
        fig.add_trace(go.Scatter(
            x=[next_label], y=[pred], mode="markers+text", name="توقع الشهر القادم",
            marker=dict(size=12, symbol="diamond"),
            text=[f"{int(round(pred))}"], textposition="top center"
        ))
        # عمود النطاق التقريبي على نفس التصنيف (Nov)
        fig.add_trace(go.Scatter(
            x=[next_label, next_label], y=[ci_low, ci_high], mode="lines", name="نطاق تقريبي",
            line=dict(color="rgba(164,220,255,.6)", width=8)
        ))
        # نثبت ترتيب المحور السيني لعرض Nov بعد Oct
        fig.update_layout(
            xaxis=dict(categoryorder="array", categoryarray=line_x_full_lbl)
        )
    else:
        # بدون Sklearn: نعرض الفعلي فقط + نقطة تقدير مبسّطة إن توفرت شهران
        if len(y_val) >= 2:
            growth = y_val[-1] - y_val[-2]
            pred = int(round(y_val[-1] + growth))
            fig.add_trace(go.Scatter(
                x=[next_label], y=[pred], mode="markers+text", name="توقع مبسّط",
                marker=dict(size=12, symbol="diamond"),
                text=[str(pred)], textposition="top center"
            ))
            fig.update_layout(
                xaxis=dict(categoryorder="array", categoryarray=x_labels_actual + [next_label])
            )

    fig.update_layout(
        title="منحنى الإجمالي الشهري + التوقع القادم",
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, b=40, l=20, r=20),
        yaxis_title="عدد الاتصالات", xaxis_title="الشهر"
    )
    return fig


fig_pred = forecast_figure(df_for_forecast)
if fig_pred is not None:
    st.plotly_chart(fig_pred, use_container_width=True)
else:
    st.info("البيانات غير كافية لعرض منحنى التنبؤ.")

st.markdown('</div>', unsafe_allow_html=True)

# ───────────────────────── Map (static lat/lon) ─────────────────────────
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### خريطة الاتصالات حسب المدينة/المنطقة")

CITY_LATLON = {
    "الرياض": (24.7136, 46.6753),
    "جدة": (21.4858, 39.1925),
    "مكة": (21.3891, 39.8579),
    "المدينة": (24.5247, 39.5692),
    "الدمام": (26.3927, 49.9777),
    "الخبر": (26.2794, 50.2083),
    "الطائف": (21.2703, 40.4158),
    "أبها": (18.2465, 42.5117),
    "حائل": (27.5114, 41.7208),
    "تبوك": (28.3838, 36.5662),
    "جازان": (16.8892, 42.5700),
}
REGION_LATLON = {
    "المنطقة الشرقية": (26.5, 49.8),
    "منطقة الرياض": (24.7, 46.7),
    "منطقة مكة": (21.4, 40.7),
    "منطقة المدينة": (24.6, 39.6),
    "منطقة القصيم": (26.3, 43.96),
    "منطقة تبوك": (28.4, 36.6),
    "منطقة حائل": (27.5, 41.7),
    "منطقة جازان": (16.9, 42.6),
    "منطقة نجران": (17.6, 44.4),
    "منطقة عسير": (18.2, 42.5),
    "منطقة الجوف": (29.97, 40.2),
    "الحدود الشمالية": (30.0, 41.0),
    "منطقة الباحة": (20.0, 41.45),
    "منطقة الطائف": (21.27, 40.42),
}

def build_map_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["label","lat","lon","count"])
    rows = []
    if "المدينه " in df.columns:
        for name, n in df["المدينه "].value_counts().items():
            name = str(name).strip()
            if name in CITY_LATLON:
                lat, lon = CITY_LATLON[name]
                rows.append({"label": name, "lat": lat, "lon": lon, "count": int(n)})
    if not rows and "المنطقة" in df.columns:
        for name, n in df["المنطقة"].value_counts().items():
            name = str(name).strip()
            if name in REGION_LATLON:
                lat, lon = REGION_LATLON[name]
                rows.append({"label": name, "lat": lat, "lon": lon, "count": int(n)})
    return pd.DataFrame(rows)

map_df = build_map_df(filtered)
if not map_df.empty:
    fig_map = px.scatter_mapbox(
        map_df, lat="lat", lon="lon",
        size="count", color="count",
        hover_name="label", hover_data={"lat":False,"lon":False,"count":True},
        size_max=45, zoom=4.2, height=520,
        title="خريطة توزيع الاتصالات"
    )
    fig_map.update_layout(
        mapbox_style="carto-darkmatter",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60,b=20,l=10,r=10),
        template="plotly_dark"
    )
    st.plotly_chart(fig_map, use_container_width=True)
    figures["الخريطة"] = fig_map
else:
    st.info("لا تتوفر بيانات كافية لعرض الخريطة.")

st.markdown('</div>', unsafe_allow_html=True)

# =============== Word Cloud — الخدمه المطلوبه ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### ☁️ سحابة الكلمات — الخدمه المطلوبه")
st.info("Word cloud is not available in this environment.")
st.markdown('</div>', unsafe_allow_html=True)

# =============== جدول التفاصيل + البحث ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### السجل التفصيلي")
cols_base = ['الشهر','التاريخ','التاريخ/Date','وسم الأسبوع','رقم الأسبوع',
             'اسم العميل','المنطقة','المدينة','الشركة','نوع الخدمة','الخدمه المطلوبه','مقدم الخدمة (ملف)']
show_cols = [c for c in cols_base if c in filtered.columns]
q = st.text_input("ابحث داخل الجدول (الاسم/الشركة/المدينة/النوع/الخدمة...)", "")
table_df = filtered.copy()
if q.strip() and show_cols:
    ql = q.strip().lower()
    mask = np.zeros(len(table_df), dtype=bool)
    for c in show_cols:
        s = table_df[c].astype(str).str.lower()
        mask |= s.str.contains(ql, na=False)
    table_df = table_df[mask]
if show_cols:
    # ترجمة اسم الملف للعرض
    if "مقدم الخدمة (ملف)" in table_df.columns:
        table_df["مقدم الخدمة (ملف)"] = table_df["مقدم الخدمة (ملف)"].map(provider_to_ar)
    st.dataframe(table_df[show_cols].reset_index(drop=True), use_container_width=True, height=460)
st.markdown('</div>', unsafe_allow_html=True)

# =============== ملخص ذكي مختصر ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### 🤖 ملخّص ذكي")
def quick_summary(df: pd.DataFrame) -> str:
    if df.empty: return "لا تتوفر بيانات ضمن النطاق المحدد."
    parts = [f"إجمالي الاتصالات: **{len(df)}**."]
    if "المنطقة" in df.columns and not df["المنطقة"].value_counts().empty:
        parts.append(f"الأكثر نشاطًا: **{df['المنطقة'].value_counts().idxmax()}**.")
    if "نوع الخدمة" in df.columns and not df["نوع الخدمة"].value_counts().empty:
        parts.append(f"أشيع نوع: **{df['نوع الخدمة'].value_counts().idxmax()}**.")
    if "الشركة" in df.columns and not df["الشركة"].value_counts().empty:
        parts.append(f"الشركة الأبرز: **{df['الشركة'].value_counts().idxmax()}**.")
    return " ".join(parts)
st.write(quick_summary(filtered))
st.markdown('</div>', unsafe_allow_html=True)
