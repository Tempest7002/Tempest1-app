from datetime import date
import sqlite3
import streamlit as st

# Page configuration
st.set_page_config(page_title="TEMPEST", page_icon="⚡", layout="wide")


# 1. DATABASE SETUP
def init_db():
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS food_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, food TEXT, protein REAL, carbs REAL, fat REAL, calories REAL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS workout_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, muscle_group TEXT, exercise TEXT, sets INT, reps INT, weight REAL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS macro_targets 
                 (id INTEGER PRIMARY KEY, cal_goal INT, p_goal INT, c_goal INT, f_goal INT)""")

    c.execute("SELECT COUNT(*) FROM macro_targets")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO macro_targets (id, cal_goal, p_goal, c_goal, f_goal) VALUES (1, 2500, 180, 250, 80)"
        )

    try:
        c.execute("ALTER TABLE workout_logs ADD COLUMN muscle_group TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


init_db()


# 2. HELPER FUNCTIONS & RANKING SYSTEM
def get_macro_targets():
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute(
        "SELECT cal_goal, p_goal, c_goal, f_goal FROM macro_targets WHERE id = 1"
    )
    row = c.fetchone()
    conn.close()
    return row or (2500, 180, 250, 80)


def update_macro_targets(cal, p, c, f):
    conn = sqlite3.connect("fitness.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE macro_targets SET cal_goal=?, p_goal=?, c_goal=?, f_goal=? WHERE id=1",
        (cal, p, c, f),
    )
    conn.commit()
    conn.close()


def log_food(food, protein, carbs, fat):
    calories = (protein * 4) + (carbs * 4) + (fat * 9)
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO food_logs (date, food, protein, carbs, fat, calories) VALUES (?, ?, ?, ?, ?, ?)",
        (str(date.today()), food, protein, carbs, fat, calories),
    )
    conn.commit()
    conn.close()


def log_workout(muscle_group, exercise, sets, reps, weight):
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO workout_logs (date, muscle_group, exercise, sets, reps, weight) VALUES (?, ?, ?, ?, ?, ?)",
        (str(date.today()), muscle_group, exercise, sets, reps, weight),
    )
    conn.commit()
    conn.close()


def get_todays_macros():
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute(
        "SELECT SUM(protein), SUM(carbs), SUM(fat), SUM(calories) FROM food_logs WHERE date = ?",
        (str(date.today()),),
    )
    row = c.fetchone()
    conn.close()
    return (row[0] or 0.0, row[1] or 0.0, row[2] or 0.0, row[3] or 0.0)


def get_todays_food_entries():
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, food, calories FROM food_logs WHERE date = ?",
        (str(date.today()),),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def delete_food_entry(entry_id):
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute("DELETE FROM food_logs WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


def get_todays_workout_entries():
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, muscle_group, exercise, sets, reps, weight FROM workout_logs WHERE date = ?",
        (str(date.today()),),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def delete_workout_entry(entry_id):
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute("DELETE FROM workout_logs WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


def get_muscle_xp():
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute(
        "SELECT muscle_group, SUM(sets * reps * weight) FROM workout_logs GROUP BY muscle_group"
    )
    rows = c.fetchall()
    conn.close()

    xp_data = {
        "CHEST": 0,
        "BACK": 0,
        "SHOULDERS": 0,
        "ARMS": 0,
        "LEGS": 0,
        "CORE": 0,
    }
    for row in rows:
        key = str(row[0]).upper() if row[0] else ""
        if key in xp_data:
            xp_data[key] = int(row[1] or 0)
    return xp_data


def get_tier_info(xp):
    if xp >= 10000:
        return "MYTHIC", "#a855f7", "rgba(168, 85, 247, 0.4)", 600000
    elif xp >= 150000:
        return "PLATINUM", "#06b6d4", "rgba(6, 182, 212, 0.4)", 300000
    elif xp >= 75000:
        return "GOLD", "#eab308", "rgba(234, 179, 8, 0.4)", 150000
    elif xp >= 37500:
        return "SILVER", "#94a3b8", "rgba(148, 163, 184, 0.3)", 75000
    else:
        return "BRONZE", "#cd7f32", "rgba(205, 127, 50, 0.3)", 37500

from datetime import date, timedelta

import sqlite3
import streamlit as st


def display_workout_history():
    """Fetches all logged workouts from fitness.db and groups them by date."""
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    # Fetch all entries sorted by date (newest first)
    c.execute(
        "SELECT date, muscle_group, exercise, sets, reps, weight FROM workout_logs ORDER BY date DESC, id DESC"
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        st.info("No workout history logged yet.")
        return

    # Group records by date
    history = {}
    for entry in rows:
        w_date, muscle, exercise, sets, reps, weight = entry
        if w_date not in history:
            history[w_date] = []
        history[w_date].append(
            {
                "muscle": muscle,
                "exercise": exercise,
                "sets": sets,
                "reps": reps,
                "weight": weight,
            }
        )

    # Render each date in a collapsible expander
    for w_date, entries in history.items():
        with st.expander(f"📅 **{w_date}** ({len(entries)} sets logged)"):
            for item in entries:
                total_vol = item["sets"] * item["reps"] * item["weight"]
                st.markdown(
                    f"* **{item['muscle']}** — {item['exercise']}: "
                    f"`{item['sets']} sets` × `{item['reps']} reps` @ `{item['weight']} lbs` "
                    f"*(+{total_vol:,} XP)*"
                )

st.subheader("📜 Workout History")
display_workout_history()


def get_current_streak():
    """Queries fitness.db to calculate consecutive workout days."""
    try:
        conn = sqlite3.connect("fitness.db")
        c = conn.cursor()
        c.execute("SELECT DISTINCT date FROM workout_logs ORDER BY date DESC")
        rows = c.fetchall()
        conn.close()

        if not rows or rows[0][0] is None:
            return 0

        workout_dates = [date.fromisoformat(str(r[0])) for r in rows if r[0]]
        today = date.today()

        if workout_dates[0] < today - timedelta(days=1):
            return 0

        streak = 0
        check_date = workout_dates[0]
        for w_date in workout_dates:
            if w_date == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        return streak
    except Exception:
        return 0
    
# 3. HIGH-DEFINITION VECTOR MUSCLE ICON GENERATOR
import base64
import io
from PIL import Image


def get_muscle_svg(muscle, color="#FF0055"):
    """Dynamically recolors muscle highlights and converts white background to transparent."""
    file_path = f"assets/{muscle.lower()}.png"
    try:
        img = Image.open(file_path).convert("RGBA")

        # Convert hex color string (e.g., "#cd7f32") to RGB tuple
        if color:
            hex_c = color.lstrip("#")
            target_rgb = tuple(int(hex_c[i : i + 2], 16) for i in (0, 2, 4))

        pixels = img.getdata()
        new_pixels = []

        for r, g, b, a in pixels:
            # 1. Make the white background transparent
            if r > 240 and g > 240 and b > 240:
                new_pixels.append((0, 0, 0, 0))

            # 2. Swap the red muscle highlights to match the rank color
            elif r > 180 and g < 80 and b < 100 and color:
                new_pixels.append((*target_rgb, a))

            # 3. Keep all other outlines and shading as-is
            else:
                new_pixels.append((r, g, b, a))

        img.putdata(new_pixels)

        # Encode modified image directly to Base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        encoded = base64.b64encode(buffered.getvalue()).decode()

        return f'<img src="data:image/png;base64,{encoded}" width="70" style="display: block; margin: auto;">'
    except Exception:
        return ""


# 4. DASHBOARD RENDER
p_tot, c_tot, f_tot, cal_tot = get_todays_macros()
cal_goal, p_goal, c_goal, f_goal = get_macro_targets()

cal_pct = min(cal_tot / cal_goal, 1.0) if cal_goal > 0 else 0.0
p_pct = min(p_tot / p_goal, 1.0) if p_goal > 0 else 0.0
f_pct = min(f_tot / f_goal, 1.0) if f_goal > 0 else 0.0

cal_dash = int(cal_pct * 283)
p_dash = int(p_pct * 283)
f_dash = int(f_pct * 283)

overall_pct = int(((cal_pct + p_pct + f_pct) / 3) * 100)

muscle_xp = get_muscle_xp()

cards_html = ""
for muscle, xp in muscle_xp.items():
    rank, color, glow, max_xp = get_tier_info(xp)
    bar_pct = min(int((xp / max_xp) * 100), 100)
    svg_icon = get_muscle_svg(muscle, color)

    cards_html += f"""
    <div style="background: #121215; border: 1px solid {color}; border-radius: 12px; padding: 14px 10px; text-align: center; box-shadow: 0 0 12px {glow}; font-family: system-ui, sans-serif;">
        <div style="display: flex; justify-content: center; align-items: center; height: 70px; margin-bottom: 2px;">
            {svg_icon}
        </div>
        <div style="color: {color}; font-weight: 800; font-size: 11px; letter-spacing: 0.5px; text-transform: uppercase;">{rank}</div>
        <div style="color: #ffffff; font-weight: 800; font-size: 14px; margin: 4px 0 6px 0; letter-spacing: 0.5px;">{muscle}</div>
        <div style="color: #71717a; font-size: 11px; margin-bottom: 8px;">XP &nbsp; {xp}/{max_xp}</div>
        <div style="background: #27272a; border-radius: 6px; height: 6px; width: 100%; overflow: hidden;">
            <div style="background: {color}; height: 100%; width: {bar_pct}%;"></div>
        </div>
    </div>
    """
current_streak = get_current_streak()

dashboard_html = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    body {{ font-family: 'Inter', sans-serif; background-color: #09090b; color: #ffffff; }}
</style>

<div style="background: #09090b; padding: 10px; font-family: 'Inter', sans-serif;">
    
    <!-- TOP HEADER -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="background: #84cc16; color: #000; font-weight: 900; padding: 4px 8px; border-radius: 6px; font-size: 18px;">⚡</div>
            <span style="font-size: 22px; font-weight: 900; letter-spacing: 1px; color: #ffffff;">TEMPEST</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: #18181b; border: 1px solid #27272a; padding: 6px 14px; border-radius: 20px; font-size: 12px; color: #a1a1aa;">
                📅 {date.today().strftime('%a, %b %d')}
            </div>
            <div style="background: #18181b; border: 1px solid #27272a; padding: 6px 14px; border-radius: 20px; font-size: 12px; color: #f97316; font-weight: 600;">
                🔥 {current_streak} day streak
            </div>
        </div>
    </div>

    <!-- MACRO RINGS -->
    <div style="background: #121215; border: 1px solid #27272a; border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center; margin-bottom: 20px;">
            
            <!-- CALORIES RING -->
            <div style="display: flex; flex-direction: column; align-items: center;">
                <div style="position: relative; width: 130px; height: 130px;">
                    <svg width="130" height="130" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#27272a" stroke-width="8" />
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#84cc16" stroke-width="8" 
                                stroke-dasharray="283" stroke-dashoffset="{283 - cal_dash}" stroke-linecap="round" 
                                transform="rotate(-90 50 50)" style="filter: drop-shadow(0 0 6px #84cc16);" />
                    </svg>
                    <div style="position: absolute; top:0; left:0; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                        <span style="font-size: 22px; font-weight: 800; color: #ffffff;">{int(cal_tot):,}</span>
                        <span style="font-size: 11px; color: #71717a;">kcal</span>
                    </div>
                </div>
                <span style="margin-top: 10px; font-weight: 700; font-size: 14px; color: #ffffff;">Calories</span>
                <span style="font-size: 12px; color: #71717a;">{cal_goal:,} kcal goal</span>
            </div>

            <!-- PROTEIN RING -->
            <div style="display: flex; flex-direction: column; align-items: center;">
                <div style="position: relative; width: 130px; height: 130px;">
                    <svg width="130" height="130" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#27272a" stroke-width="8" />
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#bef264" stroke-width="8" 
                                stroke-dasharray="283" stroke-dashoffset="{283 - p_dash}" stroke-linecap="round" 
                                transform="rotate(-90 50 50)" style="filter: drop-shadow(0 0 6px #bef264);" />
                    </svg>
                    <div style="position: absolute; top:0; left:0; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                        <span style="font-size: 22px; font-weight: 800; color: #ffffff;">{int(p_tot)}</span>
                        <span style="font-size: 11px; color: #71717a;">g</span>
                    </div>
                </div>
                <span style="margin-top: 10px; font-weight: 700; font-size: 14px; color: #ffffff;">Protein</span>
                <span style="font-size: 12px; color: #71717a;">{p_goal} g goal</span>
            </div>

            <!-- FAT RING -->
            <div style="display: flex; flex-direction: column; align-items: center;">
                <div style="position: relative; width: 130px; height: 130px;">
                    <svg width="130" height="130" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#27272a" stroke-width="8" />
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#f97316" stroke-width="8" 
                                stroke-dasharray="283" stroke-dashoffset="{283 - f_dash}" stroke-linecap="round" 
                                transform="rotate(-90 50 50)" style="filter: drop-shadow(0 0 6px #f97316);" />
                    </svg>
                    <div style="position: absolute; top:0; left:0; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                        <span style="font-size: 22px; font-weight: 800; color: #ffffff;">{int(f_tot)}</span>
                        <span style="font-size: 11px; color: #71717a;">g</span>
                    </div>
                </div>
                <span style="margin-top: 10px; font-weight: 700; font-size: 14px; color: #ffffff;">Fat</span>
                <span style="font-size: 12px; color: #71717a;">{f_goal} g goal</span>
            </div>

        </div>

        <!-- OVERALL PROGRESS BAR -->
        <div style="display: flex; align-items: center; gap: 16px; margin-top: 10px; padding-top: 16px; border-top: 1px solid #1f1f23;">
            <span style="font-size: 12px; font-weight: 600; color: #a1a1aa; white-space: nowrap;">Daily progress</span>
            <div style="flex-grow: 1; background: #27272a; height: 8px; border-radius: 10px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #84cc16, #bef264); height: 100%; width: {overall_pct}%; border-radius: 10px; box-shadow: 0 0 10px #84cc16;"></div>
            </div>
            <span style="font-size: 13px; font-weight: 800; color: #ffffff;">{overall_pct}%</span>
        </div>

    </div>

    <!-- MUSCLE RANKINGS SECTION -->
    <div style="margin-bottom: 12px; font-size: 12px; font-weight: 800; letter-spacing: 1px; color: #71717a; text-transform: uppercase;">
        Muscle Rankings
    </div>

    <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 24px;">
        {cards_html}
    </div>

</div>
"""

st.components.v1.html(dashboard_html, height=550, scrolling=False)

# 5. INPUT FORMS
st.divider()

tab1, tab2, tab3 = st.tabs(
    ["🥗 Log Food", "⚔️ Log Workout Set", "🎯 Adjust Goals"]
)

with tab1:
    st.header("Add Food")
    with st.form("food_form", clear_on_submit=True):
        food = st.text_input("Food Name")
        p = st.number_input("Protein (g)", min_value=0.0, step=1.0)
        c = st.number_input("Carbs (g)", min_value=0.0, step=1.0)
        f = st.number_input("Fat (g)", min_value=0.0, step=1.0)
        if st.form_submit_button("Log Meal"):
            if food:
                log_food(food, p, c, f)
                st.success(f"Logged {food}!")
                st.rerun()

    st.subheader("Remove Food")
    food_entries = get_todays_food_entries()
    if food_entries:
        f_options = {
            f"{item[1]} ({int(item[2])} kcal)": item[0] for item in food_entries
        }
        selected_f = st.selectbox(
            "Select entry to remove:", list(f_options.keys())
        )
        if st.button("🗑️ Delete Meal"):
            delete_food_entry(f_options[selected_f])
            st.rerun()

with tab2:
    st.header("Add Set (+XP)")
    with st.form("workout_form", clear_on_submit=True):
        muscle_group = st.selectbox(
            "Muscle Group",
            ["CHEST", "BACK", "SHOULDERS", "ARMS", "LEGS", "CORE"],
        )
        exercise = st.text_input("Exercise Name (e.g., Bench Press)")
        sets = st.number_input("Sets", min_value=1, step=1)
        reps = st.number_input("Reps", min_value=1, step=1)
        weight = st.number_input("Weight (lbs)", min_value=0.0, step=5.0)
        if st.form_submit_button("⚔️ Log Set & Gain XP"):
            if exercise:
                log_workout(muscle_group, exercise, sets, reps, weight)
                st.balloons()
                st.rerun()

    st.subheader("Remove Set")
    workout_entries = get_todays_workout_entries()
    if workout_entries:
        w_options = {
            f"[{item[1]}] {item[2]} - {item[3]}x{item[4]} @ {item[5]}lbs": item[
                0
            ]
            for item in workout_entries
        }
        selected_w = st.selectbox(
            "Select set to remove:", list(w_options.keys())
        )
        if st.button("🗑️ Delete Set"):
            delete_workout_entry(w_options[selected_w])
            st.rerun()

with tab3:
    st.header("Set Targets")
    with st.form("target_form"):
        new_cal = st.number_input("Calories (kcal)", value=cal_goal, step=50)
        new_p = st.number_input("Protein (g)", value=p_goal, step=5)
        new_c = st.number_input("Carbs (g)", value=c_goal, step=5)
        new_f = st.number_input("Fat (g)", value=f_goal, step=5)
        if st.form_submit_button("Save Goals"):
            update_macro_targets(new_cal, new_p, new_c, new_f)
            st.success("Goals updated!")
            st.rerun()