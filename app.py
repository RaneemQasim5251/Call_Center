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

# =============== Theme State Management ===============
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

if "figures" not in st.session_state:
    st.session_state["figures"] = {}
figures = st.session_state["figures"]

# =============== Design System Variables ===============
DESIGN_TOKENS = {
    "dark": {
        "primary": "#4A90E2",
        "secondary": "#7B68EE",
        "accent": "#FF6B9D",
        "success": "#4ECDC4",
        "warning": "#FFD93D",
        "bg_primary": "rgba(15, 18, 25, 0.95)",
        "bg_secondary": "rgba(25, 30, 40, 0.85)",
        "glass_bg": "linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))",
        "glass_border": "rgba(255,255,255,0.18)",
        "text_primary": "#ECF2FF",
        "text_secondary": "#B8C5D6",
        "shadow": "0 8px 32px rgba(0, 0, 0, 0.4)",
        "glow": "0 0 20px rgba(74, 144, 226, 0.3)",
        "button_bg": "linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.1))",
        "button_bg_hover": "linear-gradient(135deg, rgba(255,255,255,0.25), rgba(255,255,255,0.15))",
        "button_text": "#0a0e27",
        "button_border": "1px solid rgba(255,255,255,0.18)",
    },
    "light": {
        "primary": "#2E5BFF",
        "secondary": "#6C5CE7",
        "accent": "#FF6B9D",
        "success": "#00D9A5",
        "warning": "#FFB800",
        "bg_primary": "rgba(255, 255, 255, 0.98)",
        "bg_secondary": "rgba(250, 251, 255, 0.95)",
        "glass_bg": "linear-gradient(135deg, rgba(255,255,255,0.98), rgba(250,251,255,0.95))",
        "glass_border": "rgba(100,120,200,0.3)",
        "text_primary": "#0A0E27",
        "text_secondary": "#1A1F36",
        "shadow": "0 4px 20px rgba(0, 0, 0, 0.1)",
        "glow": "0 0 20px rgba(46, 91, 255, 0.25)",
        "button_bg": "linear-gradient(135deg, #1a1f36, #0a0e27)",
        "button_bg_hover": "linear-gradient(135deg, #0f1419, #050810)",
        "button_text": "#ffffff",
        "button_border": "none",
    }
}

current_theme = DESIGN_TOKENS[st.session_state["theme_mode"]]

# =============== Enhanced CSS with Theme Support ===============
ENHANCED_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

:root {{
    --primary: {current_theme["primary"]};
    --secondary: {current_theme["secondary"]};
    --accent: {current_theme["accent"]};
    --success: {current_theme["success"]};
    --warning: {current_theme["warning"]};
    --bg-primary: {current_theme["bg_primary"]};
    --bg-secondary: {current_theme["bg_secondary"]};
    --glass-bg: {current_theme["glass_bg"]};
    --glass-border: {current_theme["glass_border"]};
    --text-primary: {current_theme["text_primary"]};
    --text-secondary: {current_theme["text_secondary"]};
    --shadow: {current_theme["shadow"]};
    --glow: {current_theme["glow"]};
    --button-bg: {current_theme["button_bg"]};
    --button-bg-hover: {current_theme["button_bg_hover"]};
    --button-text: {current_theme["button_text"]};
    --button-border: {current_theme["button_border"]};
    --border-radius: 20px;
    --spacing-unit: 1rem;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

html, body, [data-testid="stAppViewContainer"], .block-container {{ 
    direction: rtl;
    font-family: 'Cairo', sans-serif;
}}

[data-testid="stAppViewContainer"] {{
    background: {"radial-gradient(1200px 800px at 0% 0%, rgba(40,45,60,0.55) 0%, rgba(15,18,25,0.95) 60%), radial-gradient(1000px 700px at 100% 0%, rgba(30,35,50,0.55) 0%, rgba(15,18,25,0.95) 60%)" if st.session_state["theme_mode"] == "dark" else "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"};
    backdrop-filter: blur(20px);
    transition: var(--transition);
}}

.block-container {{ 
    padding-top: 3rem;
    max-width: 1400px;
    animation: fadeIn 0.6s ease-out;
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes slideIn {{
    from {{ transform: translateX(-20px); opacity: 0; }}
    to {{ transform: translateX(0); opacity: 1; }}
}}

@keyframes pulse {{
    0%, 100% {{ transform: scale(1); }}
    50% {{ transform: scale(1.05); }}
}}

.glass {{
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    box-shadow: var(--shadow);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border-radius: var(--border-radius);
    padding: calc(var(--spacing-unit) * 1.5);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}}

.glass::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent));
    opacity: 0;
    transition: var(--transition);
}}

.glass:hover {{
    transform: translateY(-2px);
    box-shadow: var(--glow), var(--shadow);
    border-color: var(--primary);
}}

.glass:hover::before {{
    opacity: 1;
}}

h1, h2, h3, h4, h5 {{ 
    color: var(--text-primary) !important;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: calc(var(--spacing-unit) * 0.75);
}}

body, p, div, label, span {{ 
    color: var(--text-secondary) !important;
}}

.header-flex {{ 
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-unit);
    margin-bottom: calc(var(--spacing-unit) * 0.75);
    animation: slideIn 0.8s ease-out;
}}

.header-left {{ 
    display: flex;
    gap: calc(var(--spacing-unit) * 0.75);
    align-items: center;
    flex-direction: row-reverse;
}}

.logo-box {{
    width: 90px;
    height: 90px;
    border-radius: var(--border-radius);
    overflow: hidden;
    background: {"var(--glass-bg)" if st.session_state["theme_mode"] == "light" else "#ffffff"};
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.1);
    border: {"2px solid var(--glass-border)" if st.session_state["theme_mode"] == "light" else "2px solid rgba(0,0,0,0.1)"};
    transition: var(--transition);
}}

.logo-box:hover {{
    transform: scale(1.05) rotate(2deg);
    box-shadow: var(--glow);
}}

.logo-box img {{ 
    width: 100%;
    height: 100%;
    object-fit: contain;
}}

.kpi {{
    position: relative;
    border-radius: var(--border-radius);
    padding: calc(var(--spacing-unit) * 1.5);
    text-align: center;
    min-height: 170px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    box-shadow: var(--shadow);
    backdrop-filter: blur(20px);
    transition: var(--transition);
    overflow: hidden;
}}

.kpi::after {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
    opacity: 0;
    transition: var(--transition);
}}

.kpi:hover {{
    transform: translateY(-5px);
    box-shadow: var(--glow), var(--shadow);
    border-color: var(--primary);
}}

.kpi:hover::after {{
    opacity: 0.1;
}}

.kpi .title {{ 
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-bottom: calc(var(--spacing-unit) * 0.5);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.kpi .value {{ 
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.2;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.badge {{
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 50px;
    font-size: 0.85rem;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    color: var(--text-secondary);
    font-weight: 600;
    transition: var(--transition);
}}

.badge:hover {{
    background: var(--primary);
    color: white;
    transform: scale(1.05);
}}



hr {{ 
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
    margin: calc(var(--spacing-unit) * 1.5) 0;
}}

/* Streamlit-specific overrides */
.stSelectbox, .stTextInput {{
    background: transparent !important;
}}

.stSelectbox > div > div, .stTextInput > div > div {{
    background: {"#ffffff" if st.session_state["theme_mode"] == "light" else "var(--bg-secondary)"} !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    transition: var(--transition) !important;
    color: {"#0a0e27" if st.session_state["theme_mode"] == "light" else "var(--text-primary)"} !important;
}}

.stSelectbox > div > div:hover, .stTextInput > div > div:hover {{
    border-color: var(--primary) !important;
    box-shadow: var(--glow) !important;
}}

/* Dropdown menu items */
.stSelectbox [data-baseweb="select"] > div {{
    background: {"#ffffff" if st.session_state["theme_mode"] == "light" else "var(--bg-secondary)"} !important;
    color: {"#0a0e27" if st.session_state["theme_mode"] == "light" else "var(--text-primary)"} !important;
}}

/* Dropdown options list */
[role="listbox"] {{
    background: {"#ffffff" if st.session_state["theme_mode"] == "light" else "var(--bg-secondary)"} !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
}}

[role="option"] {{
    background: {"#ffffff" if st.session_state["theme_mode"] == "light" else "var(--bg-secondary)"} !important;
    color: {"#0a0e27" if st.session_state["theme_mode"] == "light" else "var(--text-primary)"} !important;
}}

[role="option"]:hover {{
    background: {"#f0f0f0" if st.session_state["theme_mode"] == "light" else "rgba(255,255,255,0.1)"} !important;
    color: {"#0a0e27" if st.session_state["theme_mode"] == "light" else "var(--text-primary)"} !important;
}}

[role="option"][aria-selected="true"] {{
    background: {f"var(--primary)" if st.session_state["theme_mode"] == "light" else "var(--primary)"} !important;
    color: #ffffff !important;
}}

.stButton > button, button[kind="primary"], button[kind="secondary"], .stFormSubmitButton > button {{
    background: {"#000000" if st.session_state["theme_mode"] == "light" else "rgba(255,255,255,0.2)"} !important;
    color: {"#FFFFFF" if st.session_state["theme_mode"] == "light" else "#000000"} !important;
    border: {"none" if st.session_state["theme_mode"] == "light" else "2px solid rgba(255,255,255,0.3)"} !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    transition: var(--transition) !important;
    box-shadow: var(--shadow) !important;
}}

.stButton > button *, button[kind="primary"] *, button[kind="secondary"] *, .stFormSubmitButton > button * {{
    color: {"#FFFFFF" if st.session_state["theme_mode"] == "light" else "#000000"} !important;
}}

.stButton > button:hover, button[kind="primary"]:hover, button[kind="secondary"]:hover, .stFormSubmitButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: var(--glow), var(--shadow) !important;
    background: {"#1a1a1a" if st.session_state["theme_mode"] == "light" else "rgba(255,255,255,0.3)"} !important;
}}

/* Chart containers */
.js-plotly-plot {{
    border-radius: var(--border-radius);
    overflow: hidden;
}}

/* Dataframe styling */
.dataframe {{
    border-radius: var(--border-radius) !important;
    overflow: hidden !important;
}}

/* Loading animation */
.stSpinner > div {{
    border-color: var(--primary) transparent transparent transparent !important;
}}

/* Scrollbar styling */
::-webkit-scrollbar {{
    width: 10px;
    height: 10px;
}}

::-webkit-scrollbar-track {{
    background: var(--bg-secondary);
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb {{
    background: var(--primary);
    border-radius: 10px;
    transition: var(--transition);
}}

::-webkit-scrollbar-thumb:hover {{
    background: var(--secondary);
}}
</style>
"""

st.markdown(ENHANCED_CSS, unsafe_allow_html=True)

# =============== Theme Toggle Function ===============
def toggle_theme():
    st.session_state["theme_mode"] = "light" if st.session_state["theme_mode"] == "dark" else "dark"
    st.rerun()

if logo_bytes:
    b64 = base64.b64encode(logo_bytes).decode("utf-8")
    logo_img_html = f'<div class="logo-box"><img src="data:image/png;base64,{b64}" alt="logo"/></div>'
else:
    logo_img_html = '<div class="logo-box"><span style="font-size:26px;">📞</span></div>'

# أيقونات الثيم - يعرض الوضع الذي سيتحول إليه عند الضغط
theme_icon = "🌙" if st.session_state["theme_mode"] == "light" else "☀️"
theme_text = "الليلي" if st.session_state["theme_mode"] == "light" else "النهاري"

st.markdown(
    f"""
    <div class="glass header-flex">
      <div class="header-left">
        <div>
          <h2 style="margin:0;">تقرير قسم خدمة العملاء 2025</h2>
          <div style="color:var(--text-secondary);margin-top:4px;font-size:.95rem;">عرض تفاعلي للمؤشرات والرسوم والخريطة</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:1rem;">
        <div id="theme-toggle-placeholder"></div>
        {logo_img_html}
      </div>
    </div>
    """,
    unsafe_allow_html=True
)



# =============== إعداد الشهور وترجَمات الأسماء ===============
MONTH_ORDER = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]  # المعتمدة
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
MONTH_AR = {
    "Jul": "يوليو", "Aug": "أغسطس", "Sep": "سبتمبر", 
    "Oct": "أكتوبر", "Nov": "نوفمبر", "Dec": "ديسمبر"
}
def month_to_ar(month: str) -> str:
    return MONTH_AR.get(month, month)

# --- توحيد قيم الشهر (Oct/October/أكتوبر… -> Oct) ---
MONTH_SYNONYMS = {
    "jul": "Jul", "jul.": "Jul", "july": "Jul", "يوليو": "Jul",
    "aug": "Aug", "aug.": "Aug", "august": "Aug", "أغسطس": "Aug", "اغسطس": "Aug",
    "sep": "Sep", "sep.": "Sep", "september": "Sep", "سبتمبر": "Sep",
    "oct": "Oct", "oct.": "Oct", "october": "Oct", "أكتوبر": "Oct", "اكتوبر": "Oct",
    "nov": "Nov", "nov.": "Nov", "november": "Nov", "نوفمبر": "Nov",
    "dec": "Dec", "dec.": "Dec", "december": "Dec", "ديسمبر": "Dec",
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
    
    # ✅ أولاً: فحص إذا كانت القيمة موجودة مباشرة في MONTH_ORDER
    if s in MONTH_ORDER:
        return s
    
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

# =============== تنظيف وتوحيد البيانات المرفوعة ===============
def clean_and_standardize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    تنظيف وتوحيد البيانات المرفوعة:
    1. تنظيف المسافات الزائدة
    2. توحيد أسماء الأعمدة
    3. معالجة صيغ التواريخ المختلفة
    4. حل الأعمدة المفقودة أو المكررة
    """
    if df is None or df.empty:
        return df
    
    # 1. تنظيف المسافات من أسماء الأعمدة
    df = df.rename(columns=lambda c: str(c).strip())
    
    # 2. توحيد أسماء الأعمدة بطريقة مرنة
    column_mapping = {
        # الاسم
        "name": "اسم العميل",
        "اسم": "اسم العميل",
        "customer_name": "اسم العميل",
        "العميل": "اسم العميل",
        
        # رقم الجوال
        "phone": "رقم الجوال",
        "mobile": "رقم الجوال",
        "phone_number": "رقم الجوال",
        "الهاتف": "رقم الجوال",
        "جوال": "رقم الجوال",
        
        # المنطقة
        "region": "المنطقة",
        "area": "المنطقة",
        
        # المدينة
        "city": "المدينة",
        "town": "المدينة",
        
        # التاريخ
        "date": "التاريخ",
        "التاريخ_date": "التاريخ",
        
        # الشهر
        "month": "الشهر",
        "الشهر_month": "الشهر",
    }
    
    # تطبيق التعيين بطريقة حساسة للحالة
    new_columns = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in column_mapping:
            new_columns[col] = column_mapping[col_lower]
        elif col in column_mapping:
            new_columns[col] = column_mapping[col]
        else:
            new_columns[col] = col
    
    df = df.rename(columns=new_columns)
    
    # 3. تنظيف البيانات النصية
    text_cols = ['اسم العميل', 'رقم الجوال', 'المنطقة', 'المدينة', 'الشركة', 
                 'نوع الخدمة', 'الخدمه المطلوبه', 'المسؤول', 'الملاحظات']
    for col in text_cols:
        if col in df.columns:
            # تنظيف المسافات والقيم الفارغة
            df[col] = df[col].astype(str).str.strip()
            # استبدال "nan" و "None" بـ فارغ
            df[col] = df[col].replace(['nan', 'None', 'none', ''], None)
    
    # 4. معالجة التواريخ بصيغ مختلفة
    if 'التاريخ' in df.columns:
        df['التاريخ'] = df['التاريخ'].apply(parse_flexible_date)
    
    # 5. توحيد الأشهر
    if 'الشهر' in df.columns:
        df['الشهر'] = df['الشهر'].astype(str).apply(normalize_month_string)
    
    return df

# =============== معالج مرن لصيغ التواريخ ===============
def parse_flexible_date(date_val):
    """معالج مرن للتواريخ بصيغ مختلفة"""
    if pd.isna(date_val) or str(date_val).strip() in ['', 'nan', 'None']:
        return pd.NaT
    
    date_str = str(date_val).strip()
    
    # قائمة صيغ التواريخ المحتملة
    date_formats = [
        '%Y-%m-%d',      # 2025-01-07
        '%d-%m-%Y',      # 07-01-2025
        '%m-%d-%Y',      # 01-07-2025
        '%Y/%m/%d',      # 2025/01/07
        '%d/%m/%Y',      # 07/01/2025
        '%m/%d/%Y',      # 01/07/2025
        '%d.%m.%Y',      # 07.01.2025
        '%Y.%m.%d',      # 2025.01.07
        '%d-%b-%Y',      # 07-Jan-2025
        '%d/%b/%Y',      # 07/Jan/2025
    ]
    
    # محاولة كل صيغة
    for fmt in date_formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
    
    # محاولة استخدام to_datetime مع dayfirst=True (آخر محاولة)
    try:
        return pd.to_datetime(date_str, dayfirst=True, errors='coerce')
    except:
        return pd.NaT

# =============== توحيد اسم الشهر ===============
def normalize_month_string(month_val):
    """توحيد أسماء الأشهر من صيغ مختلفة"""
    if pd.isna(month_val) or str(month_val).strip() in ['', 'nan', 'None']:
        return None
    
    month_str = str(month_val).strip().lower()
    
    # معاملة خاصة للأرقام
    if month_str.isdigit():
        try:
            month_num = int(month_str)
            if 1 <= month_num <= 12:
                return list(MONTH_MAP.keys())[month_num - 1]
        except:
            pass
    
    # البحث في المعاجم الموجودة
    if month_str in MONTH_SYNONYMS:
        return MONTH_SYNONYMS[month_str]
    elif month_str in MONTH_MAP:
        return month_str
    
    # محاولة إيجاد مطابقة جزئية
    for synonym, canonical in MONTH_SYNONYMS.items():
        if month_str in synonym or synonym in month_str:
            return canonical
    
    return month_str  # إرجاع القيمة الأصلية إذا لم نجد مطابقة

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
    d["WeekEnd"]   = d["WeekStart"] + pd.to_timedelta(6, unit="D")  # السبت (أسبوع كامل)

    d["ISO_Year"]  = d["WeekStart"].dt.isocalendar().year
    d["ISO_Week"]  = d["WeekStart"].dt.isocalendar().week

    if "الشهر" in d.columns:
        # نستخدم التاريخ الفعلي (WeekStart) كـ identifier موحّد بدلاً من ترقيم منفصل لكل مقدم خدمة
        # هذا يضمن أن نفس الأسبوع له نفس الوسم في جميع الملفات
        def label_week(ws, we, month):
            if pd.isna(ws) or pd.isna(we):
                return ""
            month_name_ar = MONTH_AR.get(month, month)
            # نستخدم التاريخ الفعلي للأسبوع كـ identifier
            return f"{month_name_ar} - الأسبوع ({ws.strftime('%d/%m')}–{we.strftime('%d/%m')})"
        
        d["وسم الأسبوع"] = [
            label_week(ws, we, m) 
            for ws, we, m in zip(d["WeekStart"], d["WeekEnd"], d["الشهر"])
        ]
        
        # رقم الأسبوع يُحسب بناءً على ترتيب WeekStart داخل كل شهر
        # لكن الوسم يعتمد على التاريخ الفعلي فقط
        def rank_weeks_in_month(g):
            mnum = MONTH_MAP.get(g.name, None)
            if not mnum:
                gg = g.copy()
                gg["رقم الأسبوع"] = np.nan
                return gg
            
            # جمع كل الأسابيع الفريدة في هذا الشهر (بناءً على WeekStart)
            weeks = (
                g.dropna(subset=["WeekStart"])
                [["WeekStart"]]
                .drop_duplicates()
                .sort_values("WeekStart")
                .reset_index(drop=True)
            )
            weeks["rank"] = range(1, len(weeks) + 1)
            rank_map = {ws: int(r) for ws, r in zip(weeks["WeekStart"], weeks["rank"])}
            
            gg = g.copy()
            gg["رقم الأسبوع"] = gg["WeekStart"].map(rank_map).astype("float")
            return gg
        
        d = d.groupby("الشهر", group_keys=False).apply(rank_weeks_in_month)
    else:
        d["رقم الأسبوع"] = np.nan
        d["وسم الأسبوع"] = ""

    return d

# =============== تحميل كل CSV مع معالجة الأخطاء ===============
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
                
                # التحقق إذا كان الملف يحتوي على header صحيح
                # إذا كانت أسماء الأعمدة كلها أرقام أو فارغة، فالملف لا يحتوي على header
                first_row_values = df.iloc[0].values if not df.empty else []
                col_names = df.columns.tolist()
                
                # إذا كانت أسماء الأعمدة كلها أرقام (0, 1, 2, ...) أو كانت القيمة الأولى تبدو كبيانات وليست header
                is_header_missing = (
                    all(str(c).isdigit() for c in col_names) or
                    (len(col_names) > 0 and len(df) > 0 and 
                     any(str(first_row_values[i]).strip() not in col_names[i] for i in range(min(len(col_names), len(first_row_values))))
                     and col_names[0] not in ["اسم العميل", "اسم العميل ", "name", "Name"])
                )
                
                # إذا لم يكن هناك header صحيح، نقرأ الملف بدون header ونحدد الأعمدة يدوياً
                if is_header_missing and len(df.columns) >= 10:
                    # نقرأ الملف بدون header
                    df = pd.read_csv(
                        path,
                        encoding="utf-8-sig",
                        engine="python",
                        on_bad_lines="skip",
                        sep=",",
                        quotechar='"',
                        skipinitialspace=True,
                        header=None
                    )
                    # نحدد أسماء الأعمدة بناءً على البنية المعروفة
                    expected_cols = ["اسم العميل", "رقم الجوال", "المنطقة", "المدينة", "الشركة", 
                                   "مقدم الخدمة", "نوع الخدمة", "الخدمه المطلوبه", "المسؤول", 
                                   "الملاحظات", "الشهر", "التاريخ"]
                    # نستخدم أسماء الأعمدة المتوقعة حسب عدد الأعمدة الفعلية
                    if len(df.columns) >= len(expected_cols):
                        df.columns = expected_cols[:len(df.columns)]
                    elif len(df.columns) == 12:
                        df.columns = expected_cols
                    else:
                        # إذا كان عدد الأعمدة مختلف، نستخدم الأسماء الأساسية
                        df.columns = expected_cols[:len(df.columns)] + [f"عمود_{i}" for i in range(len(expected_cols), len(df.columns))]
                
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

        # تنظيف وتوحيد عمود اسم العميل: حذف المسافات الزائدة والحفاظ على الأسماء الفعلية
        if "اسم العميل" in df.columns:
            df["اسم العميل"] = df["اسم العميل"].astype(str).str.strip()

        # تاريخ موحّد
        df["التاريخ/Date"] = pd.to_datetime(df.apply(build_date_from_month_day, axis=1), errors="coerce")

        # --- الشهر: توحيد قوي قبل الحصر ---
        if "الشهر" not in df.columns:
            # إذا لم يوجد عمود الشهر، نحاول استخراجه من التاريخ
            df["الشهر"] = df["التاريخ/Date"].dt.month.map(INV_MONTH_MAP).where(
                df["التاريخ/Date"].dt.month.map(INV_MONTH_MAP).isin(MONTH_ORDER), np.nan
            )
        else:
            # تطبيق التوحيد مع التاريخ (معالجة صحيحة للقيم NaN)
            month_series = df["الشهر"].copy()
            date_series = df["التاريخ/Date"]
            df["الشهر"] = [
                normalize_month_value(
                    month_series.iloc[i] if pd.notna(month_series.iloc[i]) else None,
                    date_series.iloc[i] if pd.notna(date_series.iloc[i]) else pd.NaT
                )
                for i in range(len(df))
            ]
            # التأكد من أن القيم في MONTH_ORDER فقط
            df["الشهر"] = df["الشهر"].where(df["الشهر"].isin(MONTH_ORDER), np.nan)

        # توحيد النصوص (باستثناء الشهر الذي تم توحيده بالفعل)
        text_cols = ["اسم العميل","رقم الجوال","المنطقة","المدينة","الشركة","نوع الخدمة","الخدمه المطلوبه"]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        # الشهر: التأكد من أنه نص (لكن نحافظ على NaN كقيمة NaN وليس نص "nan")
        # لا نحتاج لتحويله لأن normalize_month_value يعطينا القيمة الصحيحة بالفعل

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

# =============== زر الثيم مكان زر التحديث ===============
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if st.button(f"{theme_icon} {theme_text}", key="theme_toggle", use_container_width=True, help="تبديل بين الوضع النهاري والليلي"):
        toggle_theme()

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
    # نتأكد من تنظيف القيم للمقارنة الصحيحة
    filtered = filtered[filtered["الشهر"].astype(str).str.strip() == month_choice]
if week_choice != "الكل" and "وسم الأسبوع" in filtered.columns:
    filtered = filtered[filtered["وسم الأسبوع"].astype(str).str.strip() == week_choice.strip()]

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

# =============== الرسوم البيانية مع دعم الثيم ===============
plotly_template = "plotly_dark" if st.session_state["theme_mode"] == "dark" else "plotly_white"

# دالة لتوليد لوحة ألوان متناسقة مع الثيم
def get_theme_colors():
    """إرجاع قائمة ألوان متناسقة مع الثيم الحالي"""
    if st.session_state["theme_mode"] == "dark":
        return [
            "#4A90E2",  # primary
            "#7B68EE",  # secondary
            "#FF6B9D",  # accent
            "#4ECDC4",  # success
            "#FFD93D",  # warning
            "#9B59B6",  # purple
            "#3498DB",  # blue
            "#E74C3C",  # red
            "#F39C12",  # orange
            "#1ABC9C",  # turquoise
        ]
    else:
        return [
            "#2E5BFF",  # primary
            "#6C5CE7",  # secondary
            "#FF6B9D",  # accent
            "#00D9A5",  # success
            "#FFB800",  # warning
            "#8E44AD",  # purple
            "#3498DB",  # blue
            "#E74C3C",  # red
            "#F39C12",  # orange
            "#16A085",  # turquoise
        ]

theme_colors = get_theme_colors()

st.markdown('<div class="glass">', unsafe_allow_html=True)
st.markdown("### 📊 الرسوم البيانية")
c1, c2 = st.columns(2)
with c1:
    if "المنطقة" in filtered.columns and not filtered.empty:
        reg_counts = filtered["المنطقة"].value_counts().reset_index()
        reg_counts.columns = ["المنطقة","العدد"]
        fig_reg = px.bar(reg_counts, x="المنطقة", y="العدد", title="توزيع الاتصالات حسب المنطقة", text="العدد", color_discrete_sequence=theme_colors)
        fig_reg.update_traces(textposition="outside")
        fig_reg.update_layout(template=plotly_template, margin=dict(t=60,b=40,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_reg, use_container_width=True)
    else:
        st.info("لا تتوفر بيانات مناطق ضمن النطاق المحدد.")
with c2:
    if "نوع الخدمة" in filtered.columns and not filtered.empty:
        tcounts = filtered["نوع الخدمة"].value_counts()
        fig_type = px.pie(names=tcounts.index, values=tcounts.values, title="نسبة أنواع الاتصالات", hole=0.4, color_discrete_sequence=theme_colors)
        fig_type.update_traces(textposition="inside", textinfo="percent+label")
        fig_type.update_layout(template=plotly_template, margin=dict(t=60,b=40,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_type, use_container_width=True)
    else:
        st.info("لا تتوفر بيانات لأنواع الاتصالات ضمن النطاق المحدد.")
if "الشركة" in filtered.columns and not filtered.empty:
    comp_counts = filtered["الشركة"].value_counts().reset_index()
    comp_counts.columns = ["الشركة","العدد"]
    fig_comp = px.bar(comp_counts, x="الشركة", y="العدد", title="عدد الاتصالات حسب الشركة", text="العدد", color_discrete_sequence=theme_colors)
    fig_comp.update_traces(textposition="outside")
    fig_comp.update_layout(template=plotly_template, margin=dict(t=60,b=40,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_comp, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# =============== توزيع الاتصالات حسب مقدّم الخدمة (4 رسوم دائرية) ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### 👥 نسبة الاتصالات حسب مقدّم الخدمة")

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
                    title="إجمالي نسبة الاتصالات (حسب التصفية الحالية)", hole=0.4,
                    color_discrete_sequence=theme_colors
                )
                fig_agents_total.update_traces(textposition="inside", textinfo="percent+label")
                fig_agents_total.update_layout(template=plotly_template, margin=dict(t=60,b=40,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_agents_total, use_container_width=True)
            else:
                st.info("لا تتوفر بيانات لمقدّمي الخدمة ضمن التصفية الحالية.")
        else:
            st.info("لا توجد بيانات بعد تطبيق التصفية الحالية.")

    # --- 2) شهر Oct ---
    with col_oct:
        df_oct_scope = df_scope[df_scope["الشهر"].astype(str).str.strip() == "Oct"].copy() if "الشهر" in df_scope.columns else pd.DataFrame()
        if not df_oct_scope.empty:
            ac_oct = df_oct_scope[agent_col].value_counts()
            if not ac_oct.empty:
                names_oct = ac_oct.index.map(provider_to_ar) if agent_col == "مقدم الخدمة (ملف)" else ac_oct.index
                fig_agents_oct = px.pie(
                    names=names_oct, values=ac_oct.values,
                    title="نسبة الاتصالات — شهر أكتوبر", hole=0.4,
                    color_discrete_sequence=theme_colors
                )
                fig_agents_oct.update_traces(textposition="inside", textinfo="percent+label")
                fig_agents_oct.update_layout(template=plotly_template, margin=dict(t=60,b=40,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_agents_oct, use_container_width=True)
            else:
                st.info("لا توجد بيانات لشهر Oct لنفس نطاق مقدّم الخدمة.")
        else:
            st.info("لا توجد سجلات لشهر Oct في هذا النطاق.")

    # --- 3) شهر Nov ---
    with col_nov:
        df_nov_scope = df_scope[df_scope["الشهر"].astype(str).str.strip() == "Nov"].copy() if "الشهر" in df_scope.columns else pd.DataFrame()
        if not df_nov_scope.empty:
            ac_nov = df_nov_scope[agent_col].value_counts()
            if not ac_nov.empty:
                names_nov = ac_nov.index.map(provider_to_ar) if agent_col == "مقدم الخدمة (ملف)" else ac_nov.index
                fig_agents_nov = px.pie(
                    names=names_nov, values=ac_nov.values,
                    title="نسبة الاتصالات — شهر نوفمبر", hole=0.4,
                    color_discrete_sequence=theme_colors
                )
                fig_agents_nov.update_traces(textposition="inside", textinfo="percent+label")
                fig_agents_nov.update_layout(template=plotly_template, margin=dict(t=60,b=40,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_agents_nov, use_container_width=True)
            else:
                st.info("لا توجد بيانات لشهر Nov لنفس نطاق مقدّم الخدمة.")
        else:
            st.info("لا توجد سجلات لشهر Nov في هذا النطاق.")

    # --- 4) آخر أسبوع ---
    with col_week:
        if "WeekStart" in df_scope.columns and not df_scope.dropna(subset=["WeekStart"]).empty:
            latest_ws = pd.to_datetime(df_scope["WeekStart"]).max()
            df_last_week = df_scope[pd.to_datetime(df_scope["WeekStart"]) == latest_ws].copy()
            if not df_last_week.empty:
                ac_week = df_last_week[agent_col].value_counts()
                names_week = ac_week.index.map(provider_to_ar) if agent_col == "مقدم الخدمة (ملف)" else ac_week.index
                we = pd.to_datetime(df_last_week["WeekEnd"].iloc[0]) if "WeekEnd" in df_last_week.columns else latest_ws + pd.Timedelta(days=6)
                week_title = f"نسبة الاتصالات — آخر أسبوع ({latest_ws.strftime('%b %d')}–{we.strftime('%b %d')})"
                fig_agents_week = px.pie(
                    names=names_week, values=ac_week.values,
                    title=week_title, hole=0.4,
                    color_discrete_sequence=theme_colors
                )
                fig_agents_week.update_traces(textposition="inside", textinfo="percent+label")
                fig_agents_week.update_layout(template=plotly_template, margin=dict(t=60,b=40,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
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
        line=dict(width=3, color=theme_colors[0]), marker=dict(size=8, color=theme_colors[0])
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
            line=dict(dash="dot", width=2, color=theme_colors[1])
        ))
        # نقطة التنبؤ على **Nov** (أو الشهر التالي الفعلي)
        fig.add_trace(go.Scatter(
            x=[next_label], y=[pred], mode="markers+text", name="توقع الشهر القادم",
            marker=dict(size=12, symbol="diamond", color=theme_colors[2]),
            text=[f"{int(round(pred))}"], textposition="top center"
        ))
        # عمود النطاق التقريبي على نفس التصنيف (Nov)
        ci_color = f"rgba({int(theme_colors[3][1:3], 16)},{int(theme_colors[3][3:5], 16)},{int(theme_colors[3][5:7], 16)},0.3)"
        fig.add_trace(go.Scatter(
            x=[next_label, next_label], y=[ci_low, ci_high], mode="lines", name="نطاق تقريبي",
            line=dict(color=ci_color, width=8)
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
                marker=dict(size=12, symbol="diamond", color=theme_colors[2]),
                text=[str(pred)], textposition="top center"
            ))
            fig.update_layout(
                xaxis=dict(categoryorder="array", categoryarray=x_labels_actual + [next_label])
            )

    fig.update_layout(
        title="منحنى الإجمالي الشهري + التوقع القادم",
        template=plotly_template, 
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, b=40, l=20, r=20),
        yaxis_title="عدد الاتصالات", 
        xaxis_title="الشهر",
        showlegend=True,
        hovermode='x unified'
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
    if df.empty:
        return pd.DataFrame(columns=["label","lat","lon","count"])

    rows = []

    # استخدمي "المدينة" (بعد التوحيد)، وإن ما وجدت ارجعي للاسم القديم احتياطًا
    city_col = "المدينة" if "المدينة" in df.columns else ("المدينه " if "المدينه " in df.columns else None)
    if city_col:
        vc = df[city_col].astype(str).str.strip().value_counts()
        for name, n in vc.items():
            if name in CITY_LATLON:
                lat, lon = CITY_LATLON[name]
                rows.append({"label": name, "lat": lat, "lon": lon, "count": int(n)})

    # لو ما فيه مدن مطابقة، جربي على مستوى "المنطقة"
    if not rows and "المنطقة" in df.columns:
        vc = df["المنطقة"].astype(str).str.strip().value_counts()
        for name, n in vc.items():
            if name in REGION_LATLON:
                lat, lon = REGION_LATLON[name]
                rows.append({"label": name, "lat": lat, "lon": lon, "count": int(n)})

    return pd.DataFrame(rows)

# ابنِ الداتا ثم ارسم ثم خزّن
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
            hover_data={"lat": False, "lon": False, "count": True},
            size_max=30,
            title="خريطة توزيع الاتصالات",
            projection="natural earth",
        )
        map_bgcolor = "rgba(20,20,20,0.8)" if st.session_state["theme_mode"] == "dark" else "rgba(240,240,240,0.8)"
        land_color = "rgba(30,30,30,0.5)" if st.session_state["theme_mode"] == "dark" else "rgba(220,220,220,0.5)"
        
        fig_map.update_geos(
            visible=True,
            resolution=50,
            showcountries=True,
            countrycolor="rgba(255,255,255,0.3)",
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.2)",
            showland=True,
            landcolor=land_color,
            showocean=True,
            oceancolor=map_bgcolor,
            bgcolor="rgba(0,0,0,0)",
        )
        fig_map.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=40, l=10, r=10),
            height=520,
            geo=dict(center=dict(lat=24, lon=45), projection_scale=5),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        # محاولة بديلة بدون Mapbox token
        try:
            if hasattr(px, "scatter_map"):
                fig_map = px.scatter_map(
                    map_df,
                    lat="lat",
                    lon="lon",
                    size="count",
                    color="count",
                    hover_name="label",
                    hover_data={"lat": False, "lon": False, "count": True},
                    size_max=45,
                    zoom=4.2,
                    height=520,
                    title="خريطة توزيع الاتصالات",
                )
                fig_map.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=60, b=40, l=10, r=10),
                    template="plotly_dark",
                )
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning(f"❗ تعذّر رسم الخريطة: {e}")
        except Exception as e2:
            st.warning(f"❗ تعذّر رسم الخريطة: {e2}")
else:
    st.info("لا تتوفر بيانات كافية لعرض الخريطة.")

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

            wc_bg = None if st.session_state["theme_mode"] == "dark" else "white"
            
            # إنشاء دالة لتلوين الكلمات بألوان الثيم
            from matplotlib.colors import LinearSegmentedColormap
            
            if st.session_state["theme_mode"] == "dark":
                # ألوان الوضع الليلي
                theme_cmap_colors = [
                    '#4A90E2',  # primary
                    '#7B68EE',  # secondary
                    '#FF6B9D',  # accent
                    '#4ECDC4',  # success
                    '#FFD93D',  # warning
                ]
            else:
                # ألوان الوضع النهاري
                theme_cmap_colors = [
                    '#2E5BFF',  # primary
                    '#6C5CE7',  # secondary
                    '#FF6B9D',  # accent
                    '#00D9A5',  # success
                    '#FFB800',  # warning
                ]
            
            # دالة لإرجاع لون عشوائي من ألوان الثيم
            import random
            def theme_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
                return random.choice(theme_cmap_colors)
            
            wc_kwargs = dict(
                width=1200,
                height=550,
                background_color=wc_bg,
                mode="RGBA",
                max_words=200,
                prefer_horizontal=0.9,
                collocations=False,
                min_font_size=14,
                color_func=theme_color_func
            )
            if arabic_font_path and os.path.isfile(arabic_font_path):
                wc_kwargs["font_path"] = arabic_font_path

            try:
                wc = WordCloud(**wc_kwargs).generate(bidi_text)
            except Exception:
                wc = WordCloud(width=1200, height=550, background_color=wc_bg, max_words=150).generate(text_raw)

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
                f'style="max-width:100%;height:auto;border-radius:12px;box-shadow:{current_theme["shadow"]}" /></div>',
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
# تحديد أعمدة العرض بترتيب واضح: اسم العميل ورقم الجوال في الأول
cols_priority = ['اسم العميل', 'رقم الجوال']  # الأعمدة الأولويات
cols_secondary = ['الشهر','التاريخ','التاريخ/Date','وسم الأسبوع','رقم الأسبوع',
                  'المنطقة','المدينة','الشركة','نوع الخدمة','الخدمه المطلوبه','مقدم الخدمة (ملف)']
cols_base = cols_priority + cols_secondary

# اختيار الأعمدة الموجودة فقط، مع الحفاظ على الترتيب
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
    
    # التأكد من أن جميع البيانات محفوظة بدون تعديل أو حذف
    # عرض اسم العميل كما هو مسجل (سواء كان اسم حقيقي أو "عميل")
    display_df = table_df[show_cols].reset_index(drop=True).copy()
    
    # تنسيق الأعمدة لضمان الوضوح
    st.dataframe(display_df, use_container_width=True, height=460)
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

# =============== تحميل وتنزيل Excel ===============
st.markdown('<div class="glass" style="margin-top:1rem;">', unsafe_allow_html=True)
st.markdown("### 📥📤 إدارة البيانات (تحميل وتنزيل)")

excel_col1, excel_col2 = st.columns(2)

# ====== تنزيل البيانات الحالية كـ Excel ======
with excel_col1:
    st.markdown("**📥 تحميل البيانات الحالية**")
    
    # إنشاء ملف Excel مع البيانات المصفاة أو الكاملة
    export_df = filtered.copy() if not filtered.empty else df_scope.copy()
    
    # تحديد الأعمدة المراد تصديرها
    export_cols = ['اسم العميل', 'رقم الجوال', 'المنطقة', 'المدينة', 'الشركة', 
                   'نوع الخدمة', 'الخدمه المطلوبه', 'المسؤول', 'الملاحظات', 
                   'الشهر', 'التاريخ']
    export_cols = [c for c in export_cols if c in export_df.columns]
    export_df_clean = export_df[export_cols].copy()
    
    # تحويل التاريخ إلى صيغة نصية للعرض
    if 'التاريخ' in export_df_clean.columns:
        export_df_clean['التاريخ'] = pd.to_datetime(export_df_clean['التاريخ'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # إنشاء ملف Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df_clean.to_excel(writer, sheet_name='البيانات', index=False)
        
        # تنسيق العمود الأول (تحديد العرض)
        workbook = writer.book
        worksheet = writer.sheets['البيانات']
        
        # تعريب الخطوط والتنسيق
        from openpyxl.styles import Font, PatternFill, Alignment
        
        # تنسيق الرأس
        header_fill = PatternFill(start_color="4A90E2", end_color="4A90E2", fill_type="solid")
        header_font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
        
        for col_num, col_title in enumerate(export_cols, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # تحديد عرض الأعمدة
        for col_num, col_title in enumerate(export_cols, 1):
            max_length = len(str(col_title))
            adjusted_width = min(max_length + 2, 30)
            worksheet.column_dimensions[chr(64 + col_num)].width = adjusted_width
    
    output.seek(0)
    
    # زر التحميل
    st.download_button(
        label="📥 تحميل ملف Excel",
        data=output.getvalue(),
        file_name=f"call_center_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    st.caption(f"📊 عدد الصفوف: {len(export_df_clean)}")

# ====== رفع البيانات من Excel ======
with excel_col2:
    st.markdown("**📤 رفع بيانات جديدة**")
    
    # اختيار اسم المستخدم (مقدم الخدمة)
    user_names = providers + ["مستخدم جديد"]
    selected_user = st.selectbox(
        "اختر اسمك (مقدم الخدمة)",
        user_names,
        help="اختر اسمك من القائمة أو أضف اسم جديد"
    )
    
    # إذا اختار مستخدم جديد، اطلب الاسم يدويًا
    custom_user_name = None
    if selected_user == "مستخدم جديد":
        custom_user_name = st.text_input(
            "أدخل اسمك (الاسم الذي سيُحفظ به الملف)",
            placeholder="مثال: أحمد",
            help="هذا الاسم سيُستخدم لحفظ البيانات"
        )
        if custom_user_name:
            selected_user = custom_user_name.strip()
    
    # رفع الملف
    uploaded_file = st.file_uploader(
        "اختر ملف Excel للرفع",
        type=['xlsx', 'xls'],
        help="يجب أن يحتوي الملف على نفس تنسيق الأعمدة"
    )
    
    if uploaded_file is not None and selected_user:
        try:
            # قراءة الملف المرفوع
            uploaded_df = pd.read_excel(uploaded_file, sheet_name='البيانات')
            
            st.success(f"✅ تم قراءة الملف بنجاح! عدد الصفوف: {len(uploaded_df)}")
            
            # تنظيف وتوحيد البيانات (الخطوة الحاسمة)
            uploaded_df = clean_and_standardize_data(uploaded_df)
            
            # توحيد أسماء الأعمدة (إضافي للتأكد)
            uploaded_df = normalize_columns(uploaded_df)
            
            # تنسيق التاريخ (إذا لم يتم في clean_and_standardize_data)
            if "التاريخ" in uploaded_df.columns:
                # تطبيق معالجة مرنة للتواريخ
                uploaded_df["التاريخ/Date"] = uploaded_df["التاريخ"].apply(parse_flexible_date)
            elif "التاريخ/Date" not in uploaded_df.columns:
                uploaded_df["التاريخ/Date"] = pd.NaT
            
            # إضافة معلومات مقدم الخدمة
            uploaded_df["مقدم الخدمة (ملف)"] = selected_user
            
            # إضافة أعمدة الأسبوع
            uploaded_df = add_week_columns(uploaded_df)
            
            # عرض معاينة البيانات المنظفة
            st.write("**معاينة البيانات بعد التنظيف:**")
            preview_cols = [c for c in ['اسم العميل', 'رقم الجوال', 'المدينة', 'نوع الخدمة', 'التاريخ'] 
                          if c in uploaded_df.columns]
            if not preview_cols:
                preview_cols = list(uploaded_df.columns[:5])
            st.dataframe(uploaded_df[preview_cols].head(5), use_container_width=True)
            
            # عرض إحصائيات التنظيف
            with st.expander("📊 تفاصيل التنظيف والتوحيد"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("عدد الصفوف", len(uploaded_df))
                with col2:
                    st.metric("عدد الأعمدة", len(uploaded_df.columns))
                with col3:
                    missing = uploaded_df.isnull().sum().sum()
                    st.metric("قيم فارغة", missing)
                
                st.write("**الأعمدة المكتشفة:**")
                st.write(", ".join(uploaded_df.columns.tolist()))
            
            # زر الحفظ والتحديث
            if st.button("💾 حفظ وتحديث البيانات", use_container_width=True, type="primary"):
                # المسار المطلوب لحفظ الملف
                data_folder = "data"
                os.makedirs(data_folder, exist_ok=True)
                
                file_path = os.path.join(data_folder, f"{selected_user}.csv")
                
                # إذا كان الملف موجود، ندمج البيانات القديمة مع الجديدة
                if os.path.exists(file_path):
                    existing_df = pd.read_csv(file_path, encoding="utf-8-sig")
                    existing_df = normalize_columns(existing_df)
                    
                    # دمج البيانات (الإضافة والحفاظ على البيانات القديمة)
                    combined_df = pd.concat([existing_df, uploaded_df], ignore_index=True, sort=False)
                    
                    st.info(f"📊 تم دمج البيانات: {len(existing_df)} صف قديم + {len(uploaded_df)} صف جديد = {len(combined_df)} صف إجمالي")
                else:
                    combined_df = uploaded_df
                    st.info(f"📊 تم إنشاء ملف جديد مع {len(uploaded_df)} صف")
                
                # حفظ البيانات المدمجة
                combined_df.to_csv(file_path, index=False, encoding="utf-8-sig")
                
                st.success(f"✅ تم حفظ البيانات بنجاح في {file_path}!")
                st.info("⚠️ يُرجى تحديث الصفحة (Refresh) لرؤية البيانات الجديدة في لوحة التحكم")
                
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء معالجة الملف")
            st.error(f"التفاصيل: {str(e)}")
            
            st.warning("""
            **نصائح للحل:**
            1. ✓ تأكد من أن الملف بصيغة Excel (.xlsx أو .xls)
            2. ✓ تأكد من وجود ورقة باسم 'البيانات'
            3. ✓ يمكن أن تكون أسماء الأعمدة مختلفة (سيتم توحيدها تلقائياً)
            4. ✓ التواريخ يمكن بأي صيغة (ستُعالج تلقائياً)
            5. ✓ المسافات والمحتويات الفارغة ستُنظف تلقائياً
            """)
    elif uploaded_file is not None and not selected_user:
        st.warning("⚠️ يرجى اختيار اسمك أولاً قبل رفع الملف")

st.markdown('</div>', unsafe_allow_html=True)

# =============== تذييل مع معلومات إضافية ===============
st.markdown('<div class="glass" style="margin-top:1.5rem; text-align:center;">', unsafe_allow_html=True)
st.markdown(f"""
<div style="padding: 1rem;">
    <p style="color: {current_theme['text_secondary']}; font-size: 0.9rem; margin: 0;">
        📊 لوحة تحكم مركز الاتصالات • 2025
    </p>
    <p style="color: {current_theme['text_secondary']}; font-size: 0.8rem; margin-top: 0.5rem;">
        تم التحديث: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

