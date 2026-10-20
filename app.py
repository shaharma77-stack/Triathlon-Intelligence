import streamlit as st
import pandas as pd

# --- עיצוב המסך ---
st.set_page_config(page_title="Triathlon Intel", page_icon="🏆", layout="wide")
st.title("🏆 בוט מודיעין טריאתלון - גרסת פרימיום חכמה")

st.markdown("""
**איך זה עובד?**
1. העלה קובץ משתתפים (אם יש שנת לידה המערכת תסנן 50-54 אוטומטית, ואם אין - המערכת תניח שסיננת מראש).
2. העלה קבצי היסטוריה (כבר מסוננים מראש כפי שהכנת).
""")

# --- הזמנים שלך (אשדוד 2026) ---
my_times = {
    'swim': pd.to_timedelta('00:19:20'),
    'bike': pd.to_timedelta('00:34:54'),
    'run':  pd.to_timedelta('00:23:55'),
    'תוצאה': pd.to_timedelta('01:26:27')
}

def time_to_delta(t_str):
    try:
        if pd.isna(t_str) or t_str == 'אין נתונים בעבר': return pd.NaT
        return pd.to_timedelta(t_str)
    except:
        return pd.NaT

def format_gap(td):
    if pd.isna(td): return ""
    secs = int(td.total_seconds())
    sign = "🟢 מוביל ב-" if secs > 0 else "🔴 פיגור "
    mins, s = divmod(abs(secs), 60)
    return f"{sign}{mins:02d}:{s:02d}"

# --- אזור העלאת הקבצים ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. רשימת משתתפים (התחרות הקרובה)")
    live_file = st.file_uploader("העלה קובץ משתתפים (אחד)", type=['csv', 'xlsx'], key="live")
with col2:
    st.subheader("2. תוצאות היסטוריות")
    history_files = st.file_uploader("העלה קבצי תוצאות עבר (אפשר להעלות כמה יחד)", type=['csv', 'xlsx'], key="history", accept_multiple_files=True)

if st.button("🚀 נתח יריבים והצג מפת פערים"):
    if live_file and history_files:
        try:
            # קריאת קובץ המשתתפים
            df_live = pd.read_excel(live_file) if live_file.name.endswith('.xlsx') else pd.read_csv(live_file)
            
            # קריאה וחיבור של כל קבצי ההיסטוריה
            history_dfs = []
            for h_file in history_files:
                df_h = pd.read_excel(h_file) if h_file.name.endswith('.xlsx') else pd.read_csv(h_file)
                history_dfs.append(df_h)
            df_history = pd.concat(history_dfs, ignore_index=True)
            
            # סינון שנת לידה בקובץ המשתתפים (אם קיים)
            year_col = [col for col in df_live.columns if 'לידה' in col or 'שנת' in col]
            
            if year_col:
                y_col = year_col[0]
                df_live[y_col] = pd.to_numeric(df_live[y_col], errors='coerce')
                df_filtered = df_live[(df_live[y_col] >= 1972) & (df_live[y_col] <= 1976)]
                st.success(f"מעולה! סוננו {len(df_filtered)} מתחרים בקטגוריית 50-54 מתוך קובץ המשתתפים.")
            else:
                df_filtered = df_live.copy()
                st.info(f"לא זוהתה עמודת שנת לידה בקובץ המשתתפים. המערכת מניחה שהקובץ סונן מראש ומנתחת את כל {len(df_filtered)} המשתתפים בו.")
                
            # מציאת עמודות השם בצורה בטוחה
            live_name_candidates = [col for col in df_filtered.columns if 'שם' in str(col) or 'name' in str(col).lower() or 'משתתף' in str(col) or 'מתחרה' in str(col)]
            history_name_candidates = [col for col in df_history.columns if 'שם' in str(col) or 'name' in str(col).lower() or 'משתתף' in str(col) or 'מתחרה' in str(col)]
            
            if not live_name_candidates:
                st.error(f"❌ שגיאה: לא מצאתי עמודת 'שם' בקובץ המשתתפים. עמודות שזוהו: {', '.join(map(str, df_filtered.columns))}")
                st.stop()
                
            if not history_name_candidates:
                st.error(f"❌ שגיאה: לא מצאתי עמודת 'שם' בקבצי ההיסטוריה. עמודות שזוהו: {', '.join(map(str, df_history.columns))}")
                st.stop()
                
            live_name_col = live_name_candidates[0]
            history_name_col = history_name_candidates[0]
            
            df_history_unique = df_history.drop_duplicates(subset=[history_name_col])
            
            # הצלבה (מיזוג)
            df_merged = pd.merge(df_filtered, df_history_unique, left_on=live_name_col, right_on=history_name_col, how='left')
            
            # התיקון לשגיאת ה-float64: המרת הטבלה לסוג "אובייקט" לפני הכנסת הטקסט
            df_merged = df_merged.astype(object).fillna('אין נתונים בעבר')
            
            # חישוב פערים
            for metric in ['swim', 'bike', 'run', 'תוצאה']:
                if metric in df_merged.columns:
                    df_merged[f'{metric}_td'] = df_merged[metric].apply(time_to_delta)
                    df_merged[f'פער - {metric}'] = (df_merged[f'{metric}_td'] - my_times[metric]).apply(format_gap)
            
            # עיצוב הטבלה להצגה
            display_cols = [live_name_col]
            for m in ['swim', 'bike', 'run', 'תוצאה']:
                if m in df_merged.columns: 
                    display_cols.extend([m, f'פער - {m}'])
                    
            st.dataframe(df_merged[display_cols], use_container_width=True)
            
        except Exception as e:
            st.error(f"שגיאה בניתוח הקבצים: {e}")
    else:
        st.warning("אנא העלה קובץ משתתפים ולפחות קובץ היסטוריה אחד לפני הלחיצה.")
