import streamlit as st
import json
import os
import datetime
import re
import google.generativeai as genai
from PIL import Image

# ================= 🚨 页面配置 =================
st.set_page_config(page_title="🍏 AI 减脂与营养监督", layout="wide", initial_sidebar_state="expanded")

# ================= 访问权限控制 =================
def check_password():
    VALID_PASSWORD = "240909"
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔒 私人内测，请输入邀请码</h2>", unsafe_allow_html=True)
        pwd = st.text_input("邀请码", type="password", key="pwd_input")
        if st.button("🔑 进入系统"):
            if pwd == VALID_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("邀请码错误！")
        return False
    return True

if not check_password():
    st.stop()

# ================= 自定义 CSS 美化 =================
st.markdown("""
<style>
 div.stApp {
     background: url("https://raw.githubusercontent.com/openclaw/openclaw/main/docs/static/dog.png") no-repeat center center fixed !important;
     background-color: #f7f9fc !important;
     background-size: cover !important;
 }
 .stApp > header { background-color: transparent !important; }
 .stApp .main .block-container {
     background: rgba(255, 255, 255, 0.90) !important;
     border-radius: 20px !important;
     padding: 3rem 2rem !important;
     box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15) !important;
     backdrop-filter: blur(15px) !important;
     -webkit-backdrop-filter: blur(15px) !important;
     border: 1px solid rgba(255, 255, 255, 0.4) !important;
     max-width: 1200px !important;
     margin-top: 2rem !important;
 }
 section[data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.95) !important; }
 div[data-testid="stMetricValue"] { color: #10b981; font-weight: bold; }
 .stButton > button {
     background: linear-gradient(135deg, #10b981 0%, #059669 100%);
     color: white; border: none; border-radius: 8px;
     padding: 0.6rem 1rem; font-weight: 600; width: 100%;
     transition: all 0.3s ease;
 }
 .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 10px -3px rgba(16,185,129,0.3); color: white;}
 .info-box {
     background-color: #e0f2fe; color: #0369a1; padding: 12px 16px;
     border-radius: 8px; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px;
     border-left: 4px solid #0ea5e9;
 }
 .period-box {
     background-color: #fce7f3; color: #be185d; padding: 12px 16px;
     border-radius: 8px; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px;
     border-left: 4px solid #f43f5e;
 }
</style>
""", unsafe_allow_html=True)

# ================= API Key 配置 =================
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key and os.path.exists(".env"):
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GOOGLE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except Exception:
        pass

st.title("✨ AI 减脂与营养全能监督员")
st.markdown("<p style='text-align: center; color: #6b7280; font-size: 1.1rem; margin-top: -15px; margin-bottom: 20px;'>深度营养监测 | 智能热量账本 | 生理期关怀</p>", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/avocado.png", width=60)
    st.header("⚙️ 系统设置")
    input_key = st.text_input("配置 Google API Key", type="password", value=api_key if api_key else "")
    if input_key and input_key != api_key:
        api_key = input_key
        try:
            with open(".env", "w") as f: 
                f.write(f'GOOGLE_API_KEY="{api_key}"\n')
            st.success("API Key 已保存！")
        except Exception:
            st.warning("环境变量只读，本次有效。")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.1-pro-preview') 
else:
    st.warning("👈 请先在左侧输入您的 GOOGLE_API_KEY 来激活 AI 引擎。")
    st.stop()

# ================= 🚨 数据持久化 =================
USERS_FILE = "users.json"
RECORDS_FILE = "records.json"

def load_data(path):
    if not os.path.exists(path): return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except Exception:
        return {}

def save_data(data, path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.sidebar.error(f"保存数据失败: {e}")

users = load_data(USERS_FILE)
records = load_data(RECORDS_FILE)

# ================= 核心计算公式 =================
def calculate_metrics(gender, weight, height, age, activity, goal):
    # 基础代谢 BMR (Mifflin-St Jeor)
    bmr = int(10*weight + 6.25*height - 5*age + (5 if gender=="男" else -161))
    activity_multiplier = {"几乎不运动": 1.2, "轻度活动": 1.375, "中度活动": 1.55}.get(activity, 1.2)
    tdee = int(bmr * activity_multiplier)
    
    # 根据目标计算热量缺口
    target = tdee
    if goal == "减脂": target -= 400
    elif goal == "增肌": target += 300
    
    # 宏量营养素推荐 (蛋白质/碳水/脂肪)
    if goal == "减脂":
        protein = int(weight * 1.8)
        fat = int(weight * 0.8)
    elif goal == "增肌":
        protein = int(weight * 2.0)
        fat = int(weight * 1.0)
    else: # 营养监测维持
        protein = int(weight * 1.2)
        fat = int(weight * 1.0)
        
    carbs = int((target - (protein * 4) - (fat * 9)) / 4)
    if carbs < 0: carbs = 0
    
    return bmr, tdee, target, {"protein": protein, "carbs": carbs, "fat": fat}

# ================= 侧边栏：用户档案 =================
with st.sidebar:
    st.markdown("---")
    st.header("👤 档案与目标")
    user_names = list(users.keys())
    selected_user = st.selectbox("当前使用者", user_names + ["➕ 新建身体档案..."], index=0 if user_names else len(user_names))

    if selected_user == "➕ 新建身体档案...":
        with st.form("new_user_form"):
            new_name = st.text_input("如何称呼您？")
            gender = st.selectbox("性别", ["男", "女"])
            goal = st.selectbox("主要目标", ["减脂", "营养监测/维持健康", "增肌"])
            height = st.number_input("身高 (cm)", 100, 250, 170)
            age = st.number_input("年龄", 10, 100, 25)
            weight = st.number_input("体重 (kg)", 30.0, 200.0, 65.0, step=0.1)
            activity = st.selectbox("日常活动量", ["几乎不运动", "轻度活动", "中度活动"])
            
            if st.form_submit_button("💾 生成专属方案") and new_name:
                bmr, tdee, target, macros = calculate_metrics(gender, weight, height, age, activity, goal)
                users[new_name] = {
                    "gender": gender, "age": age, "height": height, "weight": weight, "activity": activity, 
                    "goal": goal, "bmr": bmr, "tdee": tdee, "target": target, "macros": macros
                }
                save_data(users, USERS_FILE)
                st.rerun()
    else:
        # 兼容老数据结构
        u_data = users[selected_user]
        u_goal = u_data.get("goal", "减脂")
        u_bmr = u_data.get("bmr", int(10*u_data['weight'] + 6.25*u_data['height'] - 5*u_data['age'] + (5 if u_data['gender']=="男" else -161)))
        macros = u_data.get("macros", {"protein": int(u_data['weight']*1.5), "carbs": 150, "fat": int(u_data['weight']*1.0)})
        
        st.info(f"🦸 **{selected_user}** | 🎯 {u_goal}\n\n"
                f"📏 {u_data['height']}cm | ⚖️ {u_data['weight']}kg\n\n"
                f"🫀 基础代谢 (BMR): {u_bmr} kcal\n"
                f"🔥 维持热量 (TDEE): {u_data.get('tdee', 0)} kcal\n"
                f"🍽️ 今日限额: **{u_data.get('target', 0)}** kcal")

if not users:
    st.info("👋 欢迎！请先在左侧建立身体档案。")
    st.stop()

if selected_user and selected_user != "➕ 新建身体档案...":
    u_data = users[selected_user]
    
    # ================= 🚨 每周一更新体重提醒 =================
    if datetime.date.today().weekday() == 0:
        st.warning("📅 **今天是周一！** 新的一周，为了让 AI 监控更精准，请记录一下最新体重吧！")
        with st.expander("⚖️ 更新本周体重", expanded=False):
            new_weight = st.number_input("最新空腹体重 (kg)", value=float(u_data['weight']), step=0.1)
            if st.button("更新并重算计划"):
                bmr, tdee, target, macros = calculate_metrics(u_data['gender'], new_weight, u_data['height'], u_data['age'], u_data['activity'], u_data.get('goal', '减脂'))
                users[selected_user].update({"weight": new_weight, "bmr": bmr, "tdee": tdee, "target": target, "macros": macros})
                save_data(users, USERS_FILE)
                st.success("计划已更新！")
                st.rerun()

    # ================= 女生专属生理期选项 =================
    is_period = False
    if u_data['gender'] == '女':
        is_period = st.checkbox("🌸 我当前正处于生理期 (将自动调整推荐与关怀)")

    today_str = str(datetime.date.today())
    if selected_user not in records: records[selected_user] = {}
    if today_str not in records[selected_user]:
        records[selected_user][today_str] = {"breakfast": None, "lunch": None, "dinner": None, "snacks": None, "exercise": None, "daily_nutrition_analysis": None}
    
    # 兼容老记录（没有 snacks 字段）
    if "snacks" not in records[selected_user][today_str]: records[selected_user][today_str]["snacks"] = None
    
    daily = records[selected_user][today_str]
    target = u_data['target']
    
    # 生理期热量补偿
    if is_period: target += 150 

    # 统计摄入与宏量营养
    consumed = sum([daily[k].get('calories', 0) for k in ['breakfast', 'lunch', 'dinner', 'snacks'] if daily[k]])
    p_sum = sum([daily[k].get('protein', 0) for k in ['breakfast', 'lunch', 'dinner', 'snacks'] if daily[k]])
    c_sum = sum([daily[k].get('carbs', 0) for k in ['breakfast', 'lunch', 'dinner', 'snacks'] if daily[k]])
    f_sum = sum([daily[k].get('fat', 0) for k in ['breakfast', 'lunch', 'dinner', 'snacks'] if daily[k]])
    
    burned = daily['exercise'].get('burned_calories', 0) if daily['exercise'] else 0
    remaining = target - consumed + burned
    
    # ================= 数据大盘 =================
    st.markdown("### 📊 今日全景监控")
    
    if is_period:
        st.markdown("""
        <div class="period-box">
        🌸 <b>生理期温馨提示：</b> 已自动为您增加 150 大卡的温暖预算。特殊时期不要严苛节食，AI 在点评时也会着重关注您的补铁与营养需求，请放心记录！
        </div>
        """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"🎯 预算 ({u_data.get('goal', '减脂')})", f"{target} kcal")
    c2.metric("🍔 摄入 (饮食)", f"{consumed} kcal", delta_color="inverse")
    c3.metric("🏃 消耗 (运动)", f"{burned} kcal")
    c4.metric("⚖️ 结余 (剩余可吃)", f"{remaining} kcal", delta_color="normal" if remaining >= 0 else "inverse")
    st.progress(min(max(consumed / (target + burned + 0.001), 0.0), 1.0))
    
    # 宏量营养素进度
    target_macros = u_data.get('macros', {"protein": 80, "carbs": 150, "fat": 40})
    st.markdown("**🥗 核心营养素达标监控**")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.caption(f"🍗 蛋白质 ({p_sum}/{target_macros['protein']}g)")
        st.progress(min(p_sum/(target_macros['protein']+0.01), 1.0))
    with m2:
        st.caption(f"🍚 碳水 ({c_sum}/{target_macros['carbs']}g)")
        st.progress(min(c_sum/(target_macros['carbs']+0.01), 1.0))
    with m3:
        st.caption(f"🥑 脂肪 ({f_sum}/{target_macros['fat']}g)")
        st.progress(min(f_sum/(target_macros['fat']+0.01), 1.0))

    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        with st.container():
            st.markdown("### 📸 记录饮食与运动")
            tab1, tab2 = st.tabs(["🍽️ 记饮食", "🏃 记运动"])
            
           
...(truncated)...
