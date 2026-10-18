import streamlit as st
import pandas as pd
import asyncio
import os

# פונקציה שמתקינה את הדפדפן הנסתר בשרת באופן אוטומטי
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")
    os.system("playwright install-deps")

install_playwright()
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# --- הגדרות עיצוב למסך ---
st.set_page_config(page_title="Triathlon Intel Bot", page_icon="🏊‍♂️", layout="wide")
st.title("🏆 בוט מודיעין טריאתלון - קטגוריית 50-54")
st.markdown("הזן קישור לרשימת משתתפים של תחרות, והמערכת תנתח את סיכויי הפודיום שלך אל מול היריבים.")

# --- הזמנים שלך (אשדוד 2026) ---
my_times = {
    'swim': pd.to_timedelta('00:19:20'),
    'bike': pd.to_timedelta('00:34:54'),
    'run':  pd.to_timedelta('00:23:55'),
    'תוצאה': pd.to_timedelta('01:26:27')
}

# --- פונקציית השאיבה ---
async def fetch_participants(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("table", timeout=15000)
        html = await page.content()
        await browser.close()
        
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        if table:
            return pd.read_html(str(table))[0]
        return None

# --- פונקציית עזר לחישוב זמנים ---
def time_to_delta(t_str):
    try:
        if pd.isna(t_str) or t_str == 'אין נתונים בעבר': return pd.NaT
        return pd.to_timedelta(t_str)
    except:
        return pd.NaT

def format_gap(td):
    if pd.isna(td): return ""
    secs = int(td.total_seconds())
    sign = "🟢 מוביל ב-" if secs > 0 else "🔴 בפיגור של "
    mins, s = divmod(abs(secs), 60)
    return f"{sign}{mins:02d}:{s:02d}"

# --- ממשק המשתמש ---
target_url = st.text_input("🔗 הדבק כאן את הקישור לרשימת המשתתפים (איגוד הטריאתלון):")

if st.button("🚀 נתח יריבים וסיכויי פודיום"):
    if target_url:
        with st.spinner("סורק את אתר האיגוד ומנתח נתונים..."):
            try:
                # שאיבת הנתונים
                df_live = asyncio.run(fetch_participants(target_url))
                
                if df_live is not None:
                    # סינון גילאי 50-54
                    year_col = [col for col in df_live.columns if 'לידה' in col or 'שנת' in col][0]
                    df_live[year_col] = pd.to_numeric(df_live[year_col], errors='coerce')
                    df_filtered = df_live[(df_live[year_col] >= 1972) & (df_live[year_col] <= 1976)]
                    
                    st.success(f"נמצאו {len(df_filtered)} מתחרים בקטגוריית 50-54!")
                    
                    # (לצורך ההדגמה באפליקציה: נטען את נתוני אשדוד כהיסטוריה בסיסית. 
                    # בעתיד נחבר למסד נתונים מלא)
                    df_history = pd.read_csv("https://raw.githubusercontent.com/username/repo/main/triathlon_results_raw.csv") # דורש קובץ זמין ברשת
                    
                    live_name_col = [col for col in df_filtered.columns if 'שם' in col][0]
                    history_name_col = [col for col in df_history.columns if 'שם' in col][0]
                    
                    # הצלבה
                    df_merged = pd.merge(df_filtered, df_history, left_on=live_name_col, right_on=history_name_col, how='left')
                    df_merged.fillna('אין נתונים בעבר', inplace=True)
                    
                    # חישוב פערים
                    for metric in ['swim', 'bike', 'run', 'תוצאה']:
                        if metric in df_merged.columns:
                            df_merged[f'{metric}_td'] = df_merged[metric].apply(time_to_delta)
                            df_merged[f'פער - {metric}'] = (df_merged[f'{metric}_td'] - my_times[metric]).apply(format_gap)
                    
                    # תצוגה
                    display_cols = [live_name_col, 'bike', 'פער - bike', 'run', 'פער - run', 'תוצאה', 'פער - תוצאה']
                    st.dataframe(df_merged[display_cols], use_container_width=True)
                    
                else:
                    st.error("לא הצלחתי למצוא טבלה בקישור הזה.")
            except Exception as e:
                st.error(f"אירעה שגיאה: {e}")
    else:
        st.warning("אנא הדבק קישור לפני הלחיצה על הכפתור.")
