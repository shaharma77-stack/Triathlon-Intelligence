import streamlit as st
import pandas as pd
import requests
import io

# --- עיצוב המסך ---
st.set_page_config(page_title="Triathlon Intel", page_icon="🏆", layout="wide")
st.title("🏆 בוט מודיעין טריאתלון - גרסה מהירה")

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

# --- ממשק המשתמש ---
target_url = st.text_input("🔗 הדבק קישור לרשימת המשתתפים באתר האיגוד:")

if st.button("🚀 נתח יריבים במהירות"):
    if target_url:
        with st.spinner("שואב נתונים..."):
            try:
                # שאיבה מהירה וקלה ללא דפדפן
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                res = requests.get(target_url, headers=headers, timeout=15)
                tables = pd.read_html(io.StringIO(res.text))
                
                if tables:
                    # לוקח את הטבלה הגדולה ביותר בעמוד (רשימת המשתתפים)
                    df_live = max(tables, key=len)
                    
                    year_col = [col for col in df_live.columns if 'לידה' in col or 'שנת' in col]
                    if year_col:
                        y_col = year_col[0]
                        df_live[y_col] = pd.to_numeric(df_live[y_col], errors='coerce')
                        
                        # סינון 50-54
                        df_filtered = df_live[(df_live[y_col] >= 1972) & (df_live[y_col] <= 1976)]
                        st.success(f"נמצאו {len(df_filtered)} מתחרים בקטגוריית 50-54!")
                        
                        # ניסיון לטעון את קובץ ההיסטוריה (אם העלית אותו לגיטהאב)
                        try:
                            df_history = pd.read_csv("triathlon_results_raw.csv")
                            live_name_col = [col for col in df_filtered.columns if 'שם' in col][0]
                            history_name_col = [col for col in df_history.columns if 'שם' in col][0]
                            
                            df_merged = pd.merge(df_filtered, df_history, left_on=live_name_col, right_on=history_name_col, how='left')
                            df_merged.fillna('אין נתונים בעבר', inplace=True)
                            
                            for metric in ['swim', 'bike', 'run', 'תוצאה']:
                                if metric in df_merged.columns:
                                    df_merged[f'{metric}_td'] = df_merged[metric].apply(time_to_delta)
                                    df_merged[f'פער - {metric}'] = (df_merged[f'{metric}_td'] - my_times[metric]).apply(format_gap)
                            
                            display_cols = [live_name_col]
                            for m in ['bike', 'run', 'תוצאה']:
                                if m in df_merged.columns: display_cols.extend([m, f'פער - {m}'])
                                
                            st.dataframe(df_merged[display_cols], use_container_width=True)
                            
                        except FileNotFoundError:
                            st.warning("⚠️ לא נמצא קובץ היסטוריה (triathlon_results_raw.csv). מציג את רשימת הנרשמים בלבד:")
                            st.dataframe(df_filtered, use_container_width=True)
                            
                    else:
                        st.error("לא נמצאה עמודת שנת לידה בטבלה.")
                else:
                    st.error("לא נמצאו טבלאות נתונים בקישור זה.")
                    
            except Exception as e:
                st.error(f"שגיאת תקשורת מהירה: {e}")
    else:
        st.warning("אנא הדבק קישור לפני הלחיצה.")
