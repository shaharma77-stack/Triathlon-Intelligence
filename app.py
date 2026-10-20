import streamlit as st
import pandas as pd

# --- עיצוב המסך ---
st.set_page_config(page_title="Triathlon Intel", page_icon="🏆", layout="wide")
st.title("🏆 בוט מודיעין טריאתלון - גרסת פרימיום (קריאת קבצים)")

st.markdown("""
**איך זה עובד?**
1. היכנס לאתר האיגוד, סמן את טבלת המשתתפים או התוצאות, העתק והדבק לתוך קובץ אקסל (Excel).
2. העלה את הקבצים לכאן, והמערכת תעשה את שאר העבודה!
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
    live_file = st.file_uploader("העלה אקסל/CSV של המשתתפים", type=['csv', 'xlsx'], key="live")
with col2:
    st.subheader("2. תוצאות היסטוריות")
    history_file = st.file_uploader("העלה אקסל/CSV של תוצאות העבר", type=['csv', 'xlsx'], key="history")

if st.button("🚀 נתח יריבים והצג מפת פערים"):
    if live_file and history_file:
        try:
            # קריאת הקבצים
            df_live = pd.read_excel(live_file) if live_file.name.endswith('.xlsx') else pd.read_csv(live_file)
            df_history = pd.read_excel(history_file) if history_file.name.endswith('.xlsx') else pd.read_csv(history_file)
            
            # איתור שנת הלידה וסינון 50-54
            year_col = [col for col in df_live.columns if 'לידה' in col or 'שנת' in col]
            
            if year_col:
                y_col = year_col[0]
                df_live[y_col] = pd.to_numeric(df_live[y_col], errors='coerce')
                df_filtered = df_live[(df_live[y_col] >= 1972) & (df_live[y_col] <= 1976)]
                
                st.success(f"מעולה! זוהו {len(df_filtered)} מתחרים בקטגוריית 50-54.")
                
                # מציאת עמודות השם
                live_name_col = [col for col in df_filtered.columns if 'שם' in col][0]
                history_name_col = [col for col in df_history.columns if 'שם' in col][0]
                
                # הצלבה (מיזוג)
                df_merged = pd.merge(df_filtered, df_history, left_on=live_name_col, right_on=history_name_col, how='left')
                df_merged.fillna('אין נתונים בעבר', inplace=True)
                
                # חישוב פערים
                for metric in ['swim', 'bike', 'run', 'תוצאה']:
                    if metric in df_merged.columns:
                        df_merged[f'{metric}_td'] = df_merged[metric].apply(time_to_delta)
                        df_merged[f'פער - {metric}'] = (df_merged[f'{metric}_td'] - my_times[metric]).apply(format_gap)
                
                # עיצוב הטבלה להצגה
                display_cols = [live_name_col]
                for m in ['bike', 'run', 'תוצאה']:
                    if m in df_merged.columns: 
                        display_cols.extend([m, f'פער - {m}'])
                        
                st.dataframe(df_merged[display_cols], use_container_width=True)
                
            else:
                st.error("לא הצלחתי למצוא עמודה של 'שנת לידה' בקובץ המשתתפים. אנא ודא שהטבלה הועתקה כראוי עם הכותרות.")
                
        except Exception as e:
            st.error(f"שגיאה בניתוח הקבצים: {e}")
    else:
        st.warning("אנא העלה את שני הקבצים (משתתפים והיסטוריה) לפני הלחיצה על הכפתור.")
