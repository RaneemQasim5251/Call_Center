# -*- coding: utf-8 -*-
import os, glob, io, base64, re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import timedelta


# ========== (إضافة جديدة) سكikit-leارن اختياري للتنبؤ ==========
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

# دالة للحصول على مسار الخط العربي
def get_arabic_font_path():
    """إرجاع مسار الخط العربي إذا كان موجوداً - يبحث في عدة مسارات"""
    # قائمة بالمسارات المحتملة للخط
    possible_paths = [
        os.path.join(ASSETS_DIR, "fonts", "NotoNaskhArabic-Regular.ttf"),
        os.path.join(APP_DIR, "assets", "fonts", "NotoNaskhArabic-Regular.ttf"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "NotoNaskhArabic-Regular.ttf"),
    ]
    
    # البحث في المسارات
    for font_path in possible_paths:
        try:
            if os.path.isfile(font_path):
                return os.path.abspath(font_path)
        except Exception:
            continue
    
    return None

arabic_font_path = get_arabic_font_path()

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
MONTH_ORDER = ["Aug", "Sep", "Oct", "Nov"]  # المعتمدة الآن
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

# دالة مساعدة لترجمة أسماء الأشهر
MONTH_AR = {"Aug": "أغسطس", "Sep": "سبتمبر", "Oct": "أكتوبر", "Nov": "نوفمبر"}
def month_to_ar(month: str) -> str:
    return MONTH_AR.get(month, month)

# --- توحيد قيم الشهر (Oct/October/أكتوبر… -> Oct) ---
MONTH_SYNONYMS = {
    "aug": "Aug", "aug.": "Aug", "august": "Aug", "أغسطس": "Aug", "اغسطس": "Aug",
    "sep": "Sep", "sep.": "Sep", "september": "Sep", "سبتمبر": "Sep",
    "oct": "Oct", "oct.": "Oct", "october": "Oct", "أكتوبر": "Oct", "اكتوبر": "Oct",
    "nov": "Nov", "nov.": "Nov", "november": "Nov", "نوفمبر": "Nov",
}
def normalize_month_value(val, dt):
    # معالجة القيم الفارغة أو NaN
    if pd.isna(val) or val is None:
        if pd.notna(dt):
            mnum = int(dt.month)
            canon = INV_MONTH_MAP.get(mnum)
            return canon if canon and canon in MONTH_ORDER else np.nan
        return np.nan
    
    # تحويل إلى نص وتنظيف
    s = str(val).strip()
    if not s or s.lower() in ['nan', 'none', '']:
        if pd.notna(dt):
            mnum = int(dt.month)
            canon = INV_MONTH_MAP.get(mnum)
            return canon if canon and canon in MONTH_ORDER else np.nan
        return np.nan
    
    # البحث في المرادفات (case-insensitive)
    s_lower = s.lower()
    if s_lower in MONTH_SYNONYMS:
        canon = MONTH_SYNONYMS[s_lower]
        return canon if canon in MONTH_ORDER else np.nan
    
    # محاولة المطابقة مع أول 3 أحرف
    if len(s) >= 3:
        s_3 = s[:3].title()
        if s_3 in MONTH_MAP:
            canon = s_3
            return canon if canon in MONTH_ORDER else np.nan
    
    # إذا فشل كل شيء ولكن التاريخ موجود، نستخدم التاريخ
    if pd.notna(dt):
        mnum = int(dt.month)
        canon = INV_MONTH_MAP.get(mnum)
        return canon if canon and canon in MONTH_ORDER else np.nan
    
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

def coerce_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """توحيد الأعمدة الزمنية بصيغة datetime لتفادي أخطاء Arrow."""
    if df is None or df.empty:
        return df
    df = df.copy()
    for col in ["التاريخ", "التاريخ/Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
# =============== بناء التاريخ من (الشهر + اليوم) ===============
def build_date_from_month_day(row: pd.Series):
    # محاولة قراءة التاريخ مباشرة إذا كان موجوداً بتنسيق تاريخ
    raw_date = row.get("التاريخ","")
    if pd.notna(raw_date) and raw_date != "":
        raw_str = str(raw_date).strip()
        if "/" in raw_str or "-" in raw_str:
            dt = pd.to_datetime(raw_str, dayfirst=True, errors="coerce")
            if pd.notna(dt):
                return dt
    
    # محاولة بناء التاريخ من الشهر واليوم
    month_val = row.get("الشهر","")
    day_val = row.get("التاريخ","")
    
    # معالجة الشهر
    month_str = ""
    if pd.notna(month_val) and month_val != "":
        month_str = str(month_val).strip()
    
    # إذا كان الشهر في MONTH_MAP مباشرة (مثل "Nov", "Oct")
    if month_str in MONTH_MAP:
        try:
            # محاولة استخراج اليوم من عمود التاريخ
            day_str = str(day_val).strip() if pd.notna(day_val) and day_val != "" else "1"
            # إزالة أي تنسيقات تاريخية
            if "/" in day_str:
                day_str = day_str.split("/")[0].strip()
            elif "-" in day_str:
                day_str = day_str.split("-")[0].strip()
            day = int(float(day_str)) if day_str and day_str.replace(".","").isdigit() else 1
            # التأكد من أن اليوم صحيح (1-31)
            day = max(1, min(31, day))
            return pd.Timestamp(year=2025, month=MONTH_MAP[month_str], day=day)
        except (ValueError, TypeError) as e:
            # إذا فشل، نرجع NaT
            return pd.NaT
    
    # محاولة استخدام normalize_month_value للشهر
    if month_str:
        month_lower = month_str.lower()
        if month_lower in MONTH_SYNONYMS:
            canon_month = MONTH_SYNONYMS[month_lower]
            if canon_month in MONTH_MAP:
                try:
                    day_str = str(day_val).strip() if pd.notna(day_val) and day_val != "" else "1"
                    if "/" in day_str:
                        day_str = day_str.split("/")[0].strip()
                    elif "-" in day_str:
                        day_str = day_str.split("-")[0].strip()
                    day = int(float(day_str)) if day_str and day_str.replace(".","").isdigit() else 1
                    day = max(1, min(31, day))
                    return pd.Timestamp(year=2025, month=MONTH_MAP[canon_month], day=day)
                except (ValueError, TypeError):
                    return pd.NaT
    
    return pd.NaT

# =============== أسابيع الأحد→السبت وترقيمها داخل الشهر ===============
def add_week_columns(d: pd.DataFrame) -> pd.DataFrame:
    """
    بناء أعمدة:
      - WeekStart, WeekEnd: بداية/نهاية الأسبوع (الأحد-السبت)
      - رقم الأسبوع: ترتيب الأسبوع داخل الشهر (1,2,3,...)
      - وسم الأسبوع: نص عربي "أكتوبر - الأسبوع 1 (01/10–07/10)"
    """
    if d.empty or "التاريخ" not in d.columns:
        d["رقم الأسبوع"] = np.nan
        d["وسم الأسبوع"] = ""
        return d

    d = d.copy()
    d["التاريخ"] = pd.to_datetime(d["التاريخ"], errors="coerce")
    d = d.dropna(subset=["التاريخ"])
    if d.empty:
        d["رقم الأسبوع"] = np.nan
        d["وسم الأسبوع"] = ""
        return d

    def week_sun_sat(dt):
        wd = dt.weekday()
        if wd == 6:
            start = dt
        else:
            start = dt - timedelta(days=wd + 1)
        end = start + timedelta(days=6)
        return start, end

    d[["WeekStart", "WeekEnd"]] = d["التاريخ"].apply(
        lambda x: pd.Series(week_sun_sat(x))
    )

    if "الشهر" in d.columns:
        def rank_weeks_in_month(g):
            if g.empty:
                return g
            
            unique = g[["WeekStart", "WeekEnd"]].drop_duplicates().sort_values("WeekStart")
            rank_map = {ws: i+1 for i, (ws, we) in enumerate(zip(unique["WeekStart"], unique["WeekEnd"]))}
            
            def label(ws, we):
                r = rank_map.get(ws, np.nan)
                # إصلاح: التحقق من NaN قبل التحويل
                if pd.isna(r):
                    week_num = "؟"
                else:
                    week_num = int(r)
                
                month_name_ar = MONTH_AR.get(g.name, g.name)
                return f"{month_name_ar} - الأسبوع {week_num} ({ws.strftime('%d/%m')}–{we.strftime('%d/%m')})"
            
            gg = g.copy()
            gg["رقم الأسبوع"] = gg["WeekStart"].map(rank_map).astype("Int64")
            gg["وسم الأسبوع"] = [label(ws, we) for ws, we in zip(gg["WeekStart"], gg["WeekEnd"])]
            return gg
        
        d = d.groupby("الشهر", group_keys=False).apply(rank_weeks_in_month, include_groups=False)
    else:
        d["رقم الأسبوع"] = np.nan
        d["وسم الأسبوع"] = ""
    
    return d

# =============== تحميل كل CSV مع معالجة الأخطاء ===============
@st.cache_data(show_spinner=True)
def load_all():
    """
    تحميل كل ملفات CSV من مجلد data/
    """
    datasets = {}
    
    # تحديد مجلد البيانات
    DATA_DIR = os.path.join(APP_DIR, "data")
    
    # التحقق من وجود المجلد
    if not os.path.exists(DATA_DIR):
        st.warning(f"مجلد البيانات غير موجود: {DATA_DIR}")
        return datasets
    
    # قراءة جميع ملفات CSV من مجلد data
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    
    if not csv_files:
        st.warning(f"لا توجد ملفات CSV في: {DATA_DIR}")
        return datasets
    
    for fname in csv_files:
        provider = fname.replace(".csv", "").strip()
        fpath = os.path.join(DATA_DIR, fname)
        
        try:
            df = pd.read_csv(fpath, encoding="utf-8-sig", engine="python", on_bad_lines="skip")
        except:
            try:
                df = pd.read_csv(fpath, encoding="latin1", engine="python", on_bad_lines="skip")
            except Exception as e:
                st.warning(f"فشل تحميل {fname}: {str(e)}")
                continue
        
        if df.empty:
            continue
        
        # نظافة أساسية
        df.dropna(how="all", inplace=True)
        df = normalize_columns(df)
        df = coerce_datetime_columns(df)
        
        # بناء عمود التاريخ إذا لم يكن موجوداً
        if "التاريخ" not in df.columns:
            if "الشهر" in df.columns and "اليوم" in df.columns:
                df["الشهر"] = df.apply(
                    lambda r: normalize_month_value(r.get("الشهر"), r.get("التاريخ")),
                    axis=1
                )
                df["التاريخ"] = df.apply(build_date_from_month_day, axis=1)
        else:
            df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce", format="mixed")
            if "الشهر" in df.columns:
                df["الشهر"] = df.apply(
                    lambda r: normalize_month_value(r.get("الشهر"), r.get("التاريخ")),
                    axis=1
                )
        
        # بناء أسابيع العمل
        df = add_week_columns(df)
        
        # مصدر الملف
        df["مقدم الخدمة (ملف)"] = provider
        
        datasets[provider] = df
    
    # دمج الكل
    if datasets:
        all_data = pd.concat(datasets.values(), ignore_index=True)
        datasets["__ALL__"] = all_data
    
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
        # عرض الأسماء بالعربية في القائمة
        month_options = ["الكل"] + [f"{month_to_ar(m)} ({m})" for m in months_av]
        month_choice_display = st.selectbox("اختر الشهر", month_options, index=0)
        # استخراج رمز الشهر من الاختيار
        if month_choice_display == "الكل":
            month_choice = "الكل"
        else:
            # استخراج رمز الشهر من النص (مثل "أغسطس (Aug)" -> "Aug")
            month_choice = month_choice_display.split("(")[-1].replace(")", "").strip() if "(" in month_choice_display else month_choice_display
        st.caption("💡 كل شهر له أسابيع منفصلة. يُفضل اختيار شهر أولاً ثم النقر على زر تطبيق المرشّحات ثم اختيار الأسبوع من قائمة اختر الأسبوع لتصفية الأسابيع.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="glass"><b>تصفية حسب الأسبوع</b>', unsafe_allow_html=True)
        # الأسبوع يظهر دائمًا: نجمع أسابيع نطاق df_scope ثم نقيّد إذا تم اختيار شهر
        week_options = ["الكل"]
        tmp = df_scope.copy()
        
        # إذا تم اختيار شهر، نعرض أسابيع هذا الشهر فقط
        if month_choice != "الكل":
            tmp = tmp[tmp["الشهر"] == month_choice]
            month_name_ar = month_to_ar(month_choice)
            help_text = f"📅 يتم عرض أسابيع شهر {month_name_ar} فقط. الأرقام (1، 2، 3...) تبدأ من جديد في كل شهر."
        else:
            help_text = "📅 ملاحظة: كل شهر له أسابيع منفصلة ومُرقمة بشكل مستقل. يُفضل اختيار شهر أولاً لتسهيل البحث."
        
        if "وسم الأسبوع" in tmp.columns and not tmp.empty:
            # ترتيب الأسابيع حسب التاريخ (تصاعدي) - التأكد من الترتيب الصحيح
            uniq = (
                tmp.dropna(subset=["WeekStart","WeekEnd", "وسم الأسبوع"])
                   .drop_duplicates(subset=["WeekStart"])
                   .sort_values("WeekStart", ascending=True)  # ترتيب تصاعدي حسب التاريخ
            )
            # إضافة الأسابيع مرتبة حسب التاريخ
            week_options += uniq["وسم الأسبوع"].tolist()
        
        week_choice = st.selectbox("اختر الأسبوع", week_options, index=0)
        st.caption(help_text)
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
    - إذا تم اختيار أسبوع: متوسط المكالمات اليومي (أحد–سبت).
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
        day_count = max(1, int((we - ws).days) + 1)  # أحد..سبت (أسبوع كامل)
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
    col_total, col_oct, col_nov, col_week = st.columns(4)

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

    # --- 3) شهر Nov (يحترم اختيار مقدّم الخدمة، لا يتأثر بمرشح الشهر/الأسبوع) ---
    with col_nov:
        df_nov_scope = df_scope[df_scope["الشهر"] == "Nov"].copy() if "الشهر" in df_scope.columns else pd.DataFrame()
        if not df_nov_scope.empty:
            ac_nov = df_nov_scope[agent_col].value_counts()
            if not ac_nov.empty:
                names_nov = ac_nov.index.map(provider_to_ar) if agent_col == "مقدم الخدمة (ملف)" else ac_nov.index
                fig_agents_nov = px.pie(
                    names=names_nov, values=ac_nov.values,
                    title="نسبة الاتصالات — شهر نوفمبر (بنفس نطاق مقدّم الخدمة)", hole=0.35
                )
                fig_agents_nov.update_traces(textposition="inside", textinfo="percent+label")
                fig_agents_nov.update_layout(template="plotly_dark", margin=dict(t=60,b=40,l=20,r=20))
                st.plotly_chart(fig_agents_nov, use_container_width=True)
            else:
                st.info("لا توجد بيانات لشهر Nov لنفس نطاق مقدّم الخدمة.")
        else:
            st.info("لا توجد سجلات لشهر Nov في هذا النطاق.")

    # --- 4) آخر أسبوع (أحدث WeekStart) ضمن نفس نطاق مقدّم الخدمة ---
    with col_week:
        if "WeekStart" in df_scope.columns and not df_scope.dropna(subset=["WeekStart"]).empty:
            latest_ws = pd.to_datetime(df_scope["WeekStart"]).max()
            df_last_week = df_scope[pd.to_datetime(df_scope["WeekStart"]) == latest_ws].copy()
            if not df_last_week.empty:
                ac_week = df_last_week[agent_col].value_counts()
                names_week = ac_week.index.map(provider_to_ar) if agent_col == "مقدم الخدمة (ملف)" else ac_week.index
                # عنوان واضح مع نطاق الأسبوع
                we = pd.to_datetime(df_last_week["WeekEnd"].iloc[0]) if "WeekEnd" in df_last_week.columns else latest_ws + pd.Timedelta(days=6)
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

    # نحافظ على ترتيب الأشهر كما في MONTH_ORDER الموجودة (Aug, Sep, Oct, Nov)
    month_totals = df_month_scope["الشهر"].value_counts().reindex(MONTH_ORDER).dropna()
    if len(month_totals) < 1:
        return None

    # x الفعلية = أسماء الأشهر الموجودة فعليًا بالترتيب
    x_labels_actual = month_totals.index.tolist()            # مثال: ['Aug','Sep','Oct','Nov']
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

# =============== خريطة (مدن/مناطق) ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### خريطة الاتصالات حسب المدينة/المنطقة")
CITY_LATLON = {
    "الرياض": (24.7136, 46.6753), "جدة": (21.4858, 39.1925), "مكة": (21.3891, 39.8579),
    "المدينة": (24.5247, 39.5692), "الدمام": (26.3927, 49.9777), "الخبر": (26.2794, 50.2083),
    "الطائف": (21.2703, 40.4158), "أبها": (18.2465, 42.5117), "حائل": (27.5114, 41.7208),
    "تبوك": (28.3838, 36.5662), "جازان": (16.8892, 42.5700)
}
REGION_LATLON = {
    "المنطقة الشرقية": (26.5, 49.8), "منطقة الرياض": (24.7, 46.7), "منطقة مكة": (21.4, 40.7),
    "منطقة المدينة": (24.6, 39.6), "منطقة القصيم": (26.3, 43.96), "منطقة تبوك": (28.4, 36.6),
    "منطقة حائل": (27.5, 41.7), "منطقة جازان": (16.9, 42.6), "منطقة نجران": (17.6, 44.4),
    "منطقة عسير": (18.2, 42.5), "منطقة الجوف": (29.97, 40.2), "الحدود الشمالية": (30.0, 41.0),
    "منطقة الباحة": (20.0, 41.45), "منطقة الطائف": (21.27, 40.42)
}
def build_map_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["label","lat","lon","count"])
    rows = []
    city_col = "المدينة" if "المدينة" in df.columns else ("المدينه" if "المدينه" in df.columns else None)
    if city_col:
        for name, n in df[city_col].value_counts().items():
            nm = str(name).strip()
            if nm in CITY_LATLON:
                lat, lon = CITY_LATLON[nm]
                rows.append({"label": nm, "lat": lat, "lon": lon, "count": int(n)})
    if not rows and "المنطقة" in df.columns:
        for name, n in df["المنطقة"].value_counts().items():
            nm = str(name).strip()
            if nm in REGION_LATLON:
                lat, lon = REGION_LATLON[nm]
                rows.append({"label": nm, "lat": lat, "lon": lon, "count": int(n)})
    return pd.DataFrame(rows)

map_df = build_map_df(filtered)
if not map_df.empty:
    try:
        # استخدام scatter_geo الذي يعمل بدون الحاجة لـ Mapbox token
        fig_map = px.scatter_geo(
            map_df, 
            lat="lat", 
            lon="lon", 
            size="count", 
            color="count",
            hover_name="label", 
            hover_data={"lat":False,"lon":False,"count":True},
            size_max=30,
            title="خريطة توزيع الاتصالات",
            projection="natural earth"
        )
        fig_map.update_geos(
            visible=True,
            resolution=50,
            showcountries=True,
            countrycolor="rgba(255,255,255,0.3)",
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.2)",
            showland=True,
            landcolor="rgba(30,30,30,0.5)",
            showocean=True,
            oceancolor="rgba(20,20,20,0.8)",
            bgcolor="rgba(0,0,0,0)"
        )
        fig_map.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60,b=40,l=10,r=10),
            template="plotly_dark",
            height=520,
            geo=dict(
                center=dict(lat=24, lon=45),  # مركز المملكة العربية السعودية
                projection_scale=5  # تكبير للتركيز على السعودية
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        # إذا فشل scatter_geo، نستخدم scatter_map إذا كان متاحاً
        try:
            if hasattr(px, 'scatter_map'):
                fig_map = px.scatter_map(
                    map_df, lat="lat", lon="lon", size="count", color="count",
                    hover_name="label", hover_data={"lat":False,"lon":False,"count":True},
                    size_max=45, zoom=4.2, height=520, title="خريطة توزيع الاتصالات"
                )
                fig_map.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=60,b=40,l=10,r=10),
                    template="plotly_dark"
                )
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning(f"❗ تعذّر رسم الخريطة: {e}")
        except Exception as e2:
            st.warning(f"❗ تعذّر رسم الخريطة: {e2}")
else:
    st.info("لا توجد إحداثيات مطابقة لأسماء المدن/المناطق ضمن المدى الحالي.")
st.markdown('</div>', unsafe_allow_html=True)

# =============== Word Cloud — الخدمه المطلوبه ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### ☁️ سحابة الكلمات الأكثر تكرارا ")

try:
    import matplotlib
    matplotlib.use("Agg")  # Backend غير تفاعلي لستريمليت كلاود
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud
    import arabic_reshaper
    from bidi.algorithm import get_display
    from io import BytesIO
    import base64
    from collections import Counter
    import re

    if "الخدمه المطلوبه" in filtered.columns and not filtered.empty:
        # اجمع نصوص العمود ونظّفها
        text_series = filtered["الخدمه المطلوبه"].dropna().astype(str)
        text_list = [t.strip() for t in text_series.tolist() if t.strip() and t.strip().lower() != "nan"]
        text_raw = " ".join(text_list)

        if len(text_raw) > 3:
            # تهيئة العربية (تشكيـل وربط الحروف + اتجاه العرض)
            reshaped = arabic_reshaper.reshape(text_raw)
            bidi_text = get_display(reshaped)

            # حددي خط عربي إن وُجد في assets (تم اكتشافه مسبقًا في arabic_font_path)
            wc_kwargs = dict(
                width=1200,
                height=550,
                background_color=None,  # شفاف
                mode="RGBA",
                max_words=200,
                prefer_horizontal=0.9,
                collocations=False,
                min_font_size=14
            )
            if arabic_font_path and os.path.isfile(arabic_font_path):
                wc_kwargs["font_path"] = arabic_font_path

            try:
                wc = WordCloud(**wc_kwargs).generate(bidi_text)
            except Exception:
                # محاولة مبسّطة ثانية إذا فشلت الأولى
                wc = WordCloud(width=1200, height=550, background_color="white", max_words=150).generate(text_raw)

            # ارسم واحفظ للصقّ بالصورة
            plt.ioff()
            fig, ax = plt.subplots(figsize=(14, 6), dpi=150, facecolor="none")
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            fig.patch.set_alpha(0.0)
            plt.tight_layout(pad=0)

            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, transparent=True)
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig); buf.close()

            st.markdown(
                f'<div style="text-align:center;"><img src="data:image/png;base64,{img_b64}" '
                f'style="max-width:100%;height:auto;border-radius:10px;" /></div>',
                unsafe_allow_html=True
            )
        else:
            st.info("لا توجد بيانات كافية في عمود **الخدمه المطلوبه** ضمن النطاق المحدد.")
    else:
        st.info("لا يتوفر عمود **الخدمه المطلوبه** في البيانات المصفاة.")

except ImportError:
    # بديل نصّي بسيط عند غياب الحزم
    if "الخدمه المطلوبه" in filtered.columns and not filtered.empty:
        all_text = " ".join(filtered["الخدمه المطلوبه"].dropna().astype(str).tolist())
        words = re.findall(r"\b\w+\b", all_text, re.UNICODE)
        common = Counter(words).most_common(20)
        if common:
            st.markdown("**أكثر الكلمات شيوعًا (بديل عن السحابة):**")
            st.markdown(" | ".join([f"**{w}** ({c})" for w, c in common]))
        else:
            st.info("لا توجد كلمات لعرضها.")
    else:
        st.info("لا يتوفر عمود **الخدمه المطلوبه** في البيانات المصفاة.")

except Exception as e:
    st.warning(f"تعذّر إنشاء سحابة الكلمات: {e}")
    # بديل احتياطي
    try:
        from collections import Counter
        import re
        if "الخدمه المطلوبه" in filtered.columns and not filtered.empty:
            all_text = " ".join(filtered["الخدمه المطلوبه"].dropna().astype(str).tolist())
            words = re.findall(r"\b\w+\b", all_text, re.UNICODE)
            common = Counter(words).most_common(20)
            if common:
                st.markdown("**أكثر الكلمات شيوعًا (بديل عن السحابة):**")
                st.markdown(" | ".join([f"**{w}** ({c})" for w, c in common]))
    except Exception:
        pass

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
        parts.append(f"نوع الخدمة الأكثر شيوعا: **{df['نوع الخدمة'].value_counts().idxmax()}**.")
    if "الشركة" in df.columns and not df["الشركة"].value_counts().empty:
        parts.append(f"الشركة الأبرز: **{df['الشركة'].value_counts().idxmax()}**.")
    return " ".join(parts)
st.write(quick_summary(filtered))
st.markdown('</div>', unsafe_allow_html=True)

