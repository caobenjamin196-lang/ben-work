import streamlit as st
import json
import os
import datetime
import re
import base64
import google.generativeai as genai
from PIL import Image

# 兼容不同的 Python 版本来处理时区
try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz 

# =================  页面配置 =================
st.set_page_config(page_title="🍏 AI 减脂与营养监督", layout="wide", initial_sidebar_state="expanded")

# ================= 访问权限控制 =================
def check_password():
    VALID_PASSWORD = "240909"
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; margin-top: 50px; font-weight: 800;'>🔒 私人内测，请输入邀请码</h2>", unsafe_allow_html=True)
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

# ================= 读取图片/视频并转为 Base64 =================
def get_base64_media(filename):
    # 1. 优先尝试在当前代码所在目录寻找
    local_path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    # 2. 如果当前目录没有，尝试去 Mac 桌面找 (针对本地调试)
    mac_path = os.path.expanduser(f"~/Desktop/{filename}")
    if os.path.exists(mac_path):
        with open(mac_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
            
    return ""

# 加载边角装饰图片及加载动画素材
dog_gif_b64 = get_base64_media("dog.gif")
dog1_jpg_b64 = get_base64_media("dog 1.jpeg")
dog3_mp4_b64 = get_base64_media("dog 3.mp4")

# ================= 自定义沉浸式加载动画组件 (全屏虚化+动图边缘融合) =================
def show_custom_loader(message):
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f'''
        <style>
            /* 隐藏顶部白边和默认 header */
            header {{ z-index: 0 !important; }}
        </style>
        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
                    background: rgba(255, 255, 255, 0.55); 
                    backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); 
                    z-index: 99999; display: flex; flex-direction: column; justify-content: center; align-items: center; margin:0; padding:0;">
            
            <div style="position: relative; width: 260px; height: 260px; display: flex; justify-content: center; align-items: center;">
                <video autoplay loop muted playsinline width="220" 
                       style="border-radius: 50%; 
                              mask-image: radial-gradient(circle, rgba(0,0,0,1) 45%, rgba(0,0,0,0) 70%); 
                              -webkit-mask-image: -webkit-radial-gradient(circle, rgba(0,0,0,1) 45%, rgba(0,0,0,0) 70%);">
                    <source src="data:video/mp4;base64,{dog3_mp4_b64}" type="video/mp4">
                </video>
            </div>
            
            <h3 style="color: #047857; margin-top: -10px; font-weight: 900; text-align: center; font-size: 1.6rem; 
                       text-shadow: 0 2px 8px rgba(255,255,255,0.9), 0 0 15px rgba(255,255,255,0.8); z-index: 100000;">
                {message}
            </h3>
        </div>
        ''', unsafe_allow_html=True)
    return placeholder

# ================= 动态背景与边缘虚化遮罩注入 =================
def inject_dynamic_bg(weekday_index):
    # 7天轮换的素材列表 (0=周一, 6=周日)
    bg_filenames = ["dog 4.jpg", "dog 5.jpg", "dog 5.gif", "dog 6.gif", "dog 8.gif", "dog 9.gif", "dog 10.gif"]
    safe_index = weekday_index % 7 
    current_bg_filename = bg_filenames[safe_index]
    current_bg_b64 = get_base64_media(current_bg_filename)
    
    if current_bg_b64:
        bg_mime_type = "image/gif" if current_bg_filename.endswith(".gif") else "image/jpeg"
        st.markdown(f'''
        <style>
            div.stApp {{ background: transparent !important; }}
            .dynamic-bg {{
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background-image: url("data:{bg_mime_type};base64,{current_bg_b64}");
                background-size: cover; background-position: center; background-repeat: no-repeat;
                opacity: 0.85; z-index: -2;
            }}
            /* 边缘虚化遮罩：消除拼接感，让四周柔和融入底色 */
            .bg-vignette {{
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: radial-gradient(circle, rgba(247,249,252,0) 20%, rgba(247,249,252,0.95) 100%);
                z-index: -1; pointer-events: none;
            }}
        </style>
        <div class="dynamic-bg"></div>
        <div class="bg-vignette"></div>
        ''', unsafe_allow_html=True)

# ================= 全局 CSS 美化 (圆润可爱字体、加粗加深、透明度提升) =================
st.markdown("""
<style>
    /* 引入圆润可爱的字体集 */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&family=Varela+Round&display=swap');
    
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Nunito', 'Varela Round', 'PingFang SC', 'Microsoft YaHei', sans-serif !important;
        color: #1f2937 !important; /* 字体整体加深 */
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-weight: 900 !important;
        color: #111827 !important; /* 标题颜色更深更粗 */
        letter-spacing: 0.5px;
    }

    p, span, label, div, .stMarkdown {
        font-weight: 700; /* 全局基础字体适度加粗 */
    }

    strong {
        font-weight: 900 !important;
        color: #065f46 !important; /* 强调文字使用更深的墨绿色 */
    }

    .stApp > header { background-color: transparent !important; }
    
    .stApp .main .block-container {
        /* 提升背景的不透明度至 0.93，确保在复杂背景下字迹依然清晰 */
        background: rgba(255, 255, 255, 0.93) !important;
        border-radius: 28px !important; /* 增加圆角弧度，变得更可爱 */
        padding: 3rem 2rem !important;
        box-shadow: 0 10px 40px 0 rgba(31, 38, 135, 0.22) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border: 2px solid rgba(255, 255, 255, 0.7) !important;
        max-width: 1200px !important;
        margin-top: 2rem !important;
        z-index: 10;
        position: relative;
    }
    
    section[data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.96) !important; z-index: 100;}
    div[data-testid="stMetricValue"] { color: #059669; font-weight: 900 !important; font-size: 2.3rem !important;}
    div[data-testid="stMetricLabel"] { font-weight: 800 !important; color: #4b5563 !important; }
    
    /* 按钮更加饱满、圆润 */
    .stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white !important; 
        border: none; 
        border-radius: 20px !important; /* 极致圆润的按钮 */
        padding: 0.6rem 1rem; 
        font-weight: 800 !important; 
        font-size: 1.05rem !important;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px -1px rgba(16,185,129,0.35);
    }
    .stButton > button:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 10px 20px -3px rgba(16,185,129,0.45); color: white !important;}
    
    .info-box {
        background-color: #f0f9ff; color: #0369a1; padding: 18px;
        border-radius: 18px; font-size: 1.05rem; line-height: 1.6; margin-bottom: 20px;
        border-left: 8px solid #0ea5e9;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .period-box {
        background-color: #fff1f2; color: #be185d; padding: 18px;
        border-radius: 18px; font-size: 1.05rem; line-height: 1.6; margin-bottom: 20px;
        border-left: 8px solid #f43f5e;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .bg-pet-left {
        position: fixed; bottom: 10px; left: 10px; width: 350px; 
        opacity: 0.25; z-index: 0; pointer-events: none;
    }
    .bg-pet-right {
        position: fixed; bottom: 10px; right: 10px; width: 350px; 
        opacity: 0.25; z-index: 0; pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# 注入边角装饰图
if dog_gif_b64:
    st.markdown(f'<img src="data:image/gif;base64,{dog_gif_b64}" class="bg-pet-left">', unsafe_allow_html=True)
if dog1_jpg_b64:
    st.markdown(f'<img src="data:image/jpeg;base64,{dog1_jpg_b64}" class="bg-pet-right">', unsafe_allow_html=True)

# ================= API Key 配置 =================
try:
    api_key = st.secrets.get("GOOGLE_API_KEY", None)
except Exception:
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
st.markdown("<p style='text-align: center; color: #6b7280; font-size: 1.15rem; font-weight: 700; margin-top: -15px; margin-bottom: 20px;'>深度营养监测 | 智能热量账本 | 生理期关怀</p>", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/avocado.png", width=60)
    st.header("⚙️ 系统设置")
    input_key = st.text_input("配置 Google API Key", type="password", value=api_key if api_key else "")
    if input_key and input_key != api_key:
        api_key = input_key
        try:
            with open(".env", "w") as f: 
                f.write(f'GOOGLE_API_KEY="{api_key}"\n')
            st.success("API Key 已保存至本地 .env！")
        except Exception:
            st.warning("环境变量只读，本次有效。")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("👈 请先在左侧输入您的 GOOGLE_API_KEY 来激活 AI 引擎。")
    st.stop()

# ================= 🚨 智能模型调度引擎 =================
def safe_generate_content(contents_or_prompt):
    primary_model_name = 'gemini-3.1-pro-preview'
    fallback_model_name = 'gemini-2.5-flash'
    try:
        primary_model = genai.GenerativeModel(primary_model_name)
        response = primary_model.generate_content(contents_or_prompt)
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "Quota exceeded" in error_msg:
            st.toast("⚠️ 3.1 Pro 限流，已自动无缝切换至 2.5 Flash 引擎！", icon="🚀")
            try:
                fallback_model = genai.GenerativeModel(fallback_model_name)
                response = fallback_model.generate_content(contents_or_prompt)
                return response.text
            except Exception as e2:
                raise Exception(f"备用模型也异常: {e2}")
        else:
            raise e

# ================= 数据持久化 =================
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

# ================= 时区与日期计算 =================
def get_user_timezone_date(username):
    tz_str = "America/Montevideo" if username.lower() == "ben" else "Asia/Shanghai"
    try:
        try:
            tz = ZoneInfo(tz_str)
        except NameError:
            import pytz
            tz = pytz.timezone(tz_str)
        user_now = datetime.datetime.now(tz)
    except Exception:
        user_now = datetime.datetime.now()
    
    return user_now.strftime("%Y-%m-%d"), user_now.weekday(), user_now.date()

# ================= 核心计算公式 =================
def calculate_metrics(gender, weight, height, age, activity, goal):
    bmr = int(10*weight + 6.25*height - 5*age + (5 if gender=="男" else -161))
    activity_multiplier = {"几乎不运动": 1.2, "轻度活动": 1.375, "中度活动": 1.55}.get(activity, 1.2)
    tdee = int(bmr * activity_multiplier)
    
    target = tdee
    if goal == "减脂": target -= 400
    elif goal == "增肌": target += 300
    
    if goal == "减脂":
        protein = int(weight * 1.8)
        fat = int(weight * 0.8)
    elif goal == "增肌":
        protein = int(weight * 2.0)
        fat = int(weight * 1.0)
    else: 
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
        # 如果未选定用户，以系统当前时间注入背景
        inject_dynamic_bg(datetime.datetime.now().weekday())
        
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
                    "goal": goal, "bmr": bmr, "tdee": tdee, "target": target, "macros": macros,
                    "period": {"is_active": False, "last_start": None, "last_end": None, "cycle_length": 28} # 初始化生理期数据
                }
                save_data(users, USERS_FILE)
                st.rerun()
    else:
        u_data = users[selected_user]
        u_goal = u_data.get("goal", "减脂")
        u_bmr = u_data.get("bmr", int(10*u_data['weight'] + 6.25*u_data['height'] - 5*u_data['age'] + (5 if u_data['gender']=="男" else -161)))
        macros = u_data.get("macros", {"protein": int(u_data['weight']*1.5), "carbs": 150, "fat": int(u_data['weight']*1.0)})
        
        st.info(f"🦸 **{selected_user}** | 🎯 {u_goal}\n\n"
                f"📏 {u_data['height']}cm | ⚖️ {u_data['weight']}kg\n\n"
                f"🫀 基础代谢 (BMR): {u_bmr} kcal\n"
                f"🔥 维持热量 (TDEE): {u_data.get('tdee', 0)} kcal\n"
                f"🍽️ 今日限额: **{u_data.get('target', 0)}** kcal")

    # ================= 管理员专属：修改与删除用户 =================
    st.markdown("---")
    with st.expander("🛠️ 档案管理 (仅管理员)"):
        st.caption("输入授权码即可修改或彻底删除档案。")
        admin_auth = st.text_input("管理员授权码", type="password", key="admin_auth")
        if admin_auth == "240909": 
            st.success("✅ 权限已验证")
            target_to_edit = st.selectbox("选择要管理的档案", list(users.keys()), key="target_to_edit")
            
            if target_to_edit:
                t_data = users[target_to_edit]
                
                g_opts = ["男", "女"]
                g_val = t_data.get('gender', '男')
                g_idx = g_opts.index(g_val) if g_val in g_opts else 0
                
                goal_opts = ["减脂", "营养监测/维持健康", "增肌"]
                goal_val = t_data.get('goal', '减脂')
                goal_idx = goal_opts.index(goal_val) if goal_val in goal_opts else 0
                
                act_opts = ["几乎不运动", "轻度活动", "中度活动"]
                act_val = t_data.get('activity', '几乎不运动')
                act_idx = act_opts.index(act_val) if act_val in act_opts else 0

                with st.form("edit_user_form"):
                    e_gender = st.selectbox("性别", g_opts, index=g_idx)
                    e_goal = st.selectbox("主要目标", goal_opts, index=goal_idx)
                    e_height = st.number_input("身高 (cm)", 100, 250, int(t_data.get('height', 170)))
                    e_age = st.number_input("年龄", 10, 100, int(t_data.get('age', 25)))
                    e_weight = st.number_input("体重 (kg)", 30.0, 200.0, float(t_data.get('weight', 65.0)), step=0.1)
                    e_activity = st.selectbox("日常活动量", act_opts, index=act_idx)
                    
                    if st.form_submit_button("📝 强制保存修改"):
                        bmr, tdee, target, macros = calculate_metrics(e_gender, e_weight, e_height, e_age, e_activity, e_goal)
                        users[target_to_edit].update({
                            "gender": e_gender, "age": e_age, "height": e_height, "weight": e_weight, "activity": e_activity, 
                            "goal": e_goal, "bmr": bmr, "tdee": tdee, "target": target, "macros": macros
                        })
                        save_data(users, USERS_FILE)
                        st.success(f"已更新 {target_to_edit} 的档案！")
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🗑️ 永久删除 '{target_to_edit}'", type="primary"):
                    del users[target_to_edit]
                    if target_to_edit in records:
                        del records[target_to_edit]
                    save_data(users, USERS_FILE)
                    save_data(records, RECORDS_FILE)
                    st.success("已删除该档案！")
                    st.rerun()

if not users:
    st.info("👋 欢迎！请先在左侧建立身体档案。")
    st.stop()

if selected_user and selected_user != "➕ 新建身体档案...":
    u_data = users[selected_user]
    
    # 动态时区检测，拿到该用户当地的今天日期
    today_str, current_weekday, today_date = get_user_timezone_date(selected_user)
    
    # 根据用户所在时区，加载今日专属壁纸
    inject_dynamic_bg(current_weekday)
    
    # ================= 每周一更新体重提醒 =================
    if current_weekday == 0:
        st.warning(f"📅 **今天是{selected_user}时区的周一！** 新的一周，为了让 AI 监控更精准，请记录一下最新体重吧！")
        with st.expander("⚖️ 更新本周体重", expanded=False):
            new_weight = st.number_input("最新空腹体重 (kg)", value=float(u_data['weight']), step=0.1)
            if st.button("更新并重算计划"):
                bmr, tdee, target, macros = calculate_metrics(u_data['gender'], new_weight, u_data['height'], u_data['age'], u_data['activity'], u_data.get('goal', '减脂'))
                users[selected_user].update({"weight": new_weight, "bmr": bmr, "tdee": tdee, "target": target, "macros": macros})
                save_data(users, USERS_FILE)
                st.success("计划已更新！")
                st.rerun()

    # ================= 🌸 智能生理期追踪闭环 =================
    is_period = False
    if u_data['gender'] == '女':
        if 'period' not in u_data:
            u_data['period'] = {"is_active": False, "last_start": None, "last_end": None, "cycle_length": 28}
        
        p_data = u_data['period']
        
        st.markdown("### 🌸 生理期智能追踪")
        if p_data['is_active']:
            st.error("🩸 **您当前正处于生理期。** AI 营养师已自动介入，为您增加温暖热量预算，请注意保暖！")
            if st.button("✅ 标记本次大姨妈已结束"):
                p_data['is_active'] = False
                p_data['last_end'] = today_str
                users[selected_user]['period'] = p_data
                save_data(users, USERS_FILE)
                st.rerun()
            is_period = True
        else:
            if p_data['last_start']:
                last_start_dt = datetime.datetime.strptime(p_data['last_start'], "%Y-%m-%d").date()
                next_start_dt = last_start_dt + datetime.timedelta(days=p_data['cycle_length'])
                days_left = (next_start_dt - today_date).days
                
                if days_left > 3:
                    st.info(f"⏳ 距离下一次生理期预计还有 **{days_left}** 天。")
                elif 0 < days_left <= 3:
                    st.warning(f"⚠️ **倒计时提醒**：距离下次生理期仅剩 **{days_left}** 天！请提前准备好保暖物资，避免寒凉食物。")
                else:
                    st.error(f"🚨 **到期确认**：预计生理期已经到了 (已延迟 {abs(days_left)} 天)。您的姨妈来了吗？")
                
                if st.button("🩸 是的，大姨妈今天来了"):
                    p_data['is_active'] = True
                    p_data['last_start'] = today_str
                    users[selected_user]['period'] = p_data
                    save_data(users, USERS_FILE)
                    st.rerun()
            else:
                st.info("首次使用，当您大姨妈来临之际请在此标记，系统将自动开启下月的循环提醒。")
                if st.button("🩸 标记今天生理期开始"):
                    p_data['is_active'] = True
                    p_data['last_start'] = today_str
                    users[selected_user]['period'] = p_data
                    save_data(users, USERS_FILE)
                    st.rerun()
            is_period = False

    # ================= 跨天重置与保存逻辑 =================
    if selected_user not in records: records[selected_user] = {}
    if today_str not in records[selected_user]:
        records[selected_user][today_str] = {"breakfast": None, "lunch": None, "dinner": None, "snacks": None, "exercise": None, "daily_nutrition_analysis": None}
    if "snacks" not in records[selected_user][today_str]: records[selected_user][today_str]["snacks"] = None
    
    daily = records[selected_user][today_str]
    target = u_data['target']
    
    if is_period: target += 150 

    consumed = sum([daily[k].get('calories', 0) for k in ['breakfast', 'lunch', 'dinner', 'snacks'] if daily[k]])
    p_sum = sum([daily[k].get('protein', 0) for k in ['breakfast', 'lunch', 'dinner', 'snacks'] if daily[k]])
    c_sum = sum([daily[k].get('carbs', 0) for k in ['breakfast', 'lunch', 'dinner', 'snacks'] if daily[k]])
    f_sum = sum([daily[k].get('fat', 0) for k in ['breakfast', 'lunch', 'dinner', 'snacks'] if daily[k]])
    
    burned = daily['exercise'].get('burned_calories', 0) if daily['exercise'] else 0
    remaining = target - consumed + burned
    
    # ================= 数据大盘 =================
    st.markdown(f"### 📊 今日全景监控 (归属地: {today_str})")
    
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
            
            with tab1:
                meal_type = st.radio("当前餐段", ["早餐", "午餐", "晚餐", "零食/加餐"], horizontal=True)
                meal_key = {"早餐": "breakfast", "午餐": "lunch", "晚餐": "dinner", "零食/加餐": "snacks"}[meal_type]
                
                # 动态 Key 机制：切换餐段时系统会自动清空上一餐段的内容
                uploaded_imgs = st.file_uploader("上传美食照片 (可多图上传，支持 500MB 以内)", type=["jpg", "png", "webp"], accept_multiple_files=True, key=f"imgs_{meal_type}_{today_str}")
                meal_input = st.text_area("补充文字说明 (例如：油很大，半碗饭)", height=100, key=f"txt_{meal_type}_{today_str}")
                
                if st.button("✨ 开启 AI 深度识图分析"):
                    if not meal_input and not uploaded_imgs: 
                        st.error("请传图或输入文字描述！")
                    else:
                        loader_ui = show_custom_loader("AI 营养师正在精准分析食物元素...")
                        period_prompt = "【特别提醒：用户目前处于生理期，请在点评时额外关注是否有补铁、暖身需求，并避免推荐寒凉食物。】" if is_period else ""
                        prompt = f"""
                        用户({u_data['gender']}, {u_data['weight']}kg, 目标:{u_data.get('goal','减脂')})记录了一顿 {meal_type}。
                        补充说明: {meal_input or '无'}。
                        {period_prompt}
                        请识别所有提供的食物图片并估算热量和三大营养素。
                        务必返回纯 JSON，不包含任何外部文字或Markdown框！格式严格如下：
                        {{"food": "识别出的食物及分量", "calories": 整数, "protein": 蛋白质克数整数, "carbs": 碳水克数整数, "fat": 脂肪克数整数, "analysis": "简短且专业的营养点评"}}
                        """
                        contents = [prompt]
                        if uploaded_imgs:
                            for img in uploaded_imgs:
                                contents.append(Image.open(img))
                        
                        try:
                            res_text = safe_generate_content(contents)
                            json_match = re.search(r'\{[\s\S]*\}', res_text)
                            if json_match:
                                res = json.loads(json_match.group())
                            else:
                                res = {"food": meal_input, "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "analysis": "AI 返回格式有误。"}
                        except Exception as e:
                            res = {"food": "解析失败", "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "analysis": f"API 错误: {str(e)}"}
                        
                        # 分析完毕后清除动画并重载页面
                        loader_ui.empty()
                        daily[meal_key] = res
                        save_data(records, RECORDS_FILE)
                        st.rerun()
            
            with tab2:
                exercise_input = st.text_area("今天做了什么运动？", height=100)
                if st.button("🔥 计算消耗"):
                    loader_ui = show_custom_loader("正在核算运动卡路里...")
                    prompt_ex = f"用户({u_data['weight']}kg)运动: {exercise_input}。返回纯JSON: {{\"burned\": 整数, \"analysis\": \"点评\"}}"
                    try:
                        res_text = safe_generate_content(prompt_ex)
                        json_match = re.search(r'\{[\s\S]*\}', res_text)
                        res = json.loads(json_match.group()) if json_match else {"burned": 0, "analysis": "解析失败"}
                    except Exception:
                        res = {"burned": 0, "analysis": "错误"}
                    
                    loader_ui.empty()
                    daily['exercise'] = {"text": exercise_input, "burned_calories": res.get("burned", 0), "analysis": res.get("analysis", "")}
                    save_data(records, RECORDS_FILE)
                    st.rerun()

    with col_right:
        with st.container():
            st.markdown("### 📝 今日打卡清单")
            for m_key, m_name, icon in [("breakfast", "早餐", "🥞"), ("lunch", "午餐", "🍱"), ("dinner", "晚餐", "🥗"), ("snacks", "零食", "🍿")]:
                if daily.get(m_key):
                    with st.expander(f"{icon} {m_name}账单 (+{daily[m_key].get('calories',0)} kcal)", expanded=True):
                        st.write(f"**内容**: {daily[m_key].get('food', daily[m_key].get('text', ''))}")
                        st.caption(f"营养素估算: 蛋白质 {daily[m_key].get('protein',0)}g | 碳水 {daily[m_key].get('carbs',0)}g | 脂肪 {daily[m_key].get('fat',0)}g")
                        st.write(f"**点评**: {daily[m_key].get('analysis', '')}")
            
            if daily.get('exercise'):
                with st.expander(f"🏃 运动流水 (-{daily['exercise']['burned_calories']} kcal)", expanded=True):
                    st.write(f"**内容**: {daily['exercise']['text']}\n\n**点评**: {daily['exercise']['analysis']}")
            
            st.markdown("---")
            st.markdown("### 🥗 每日营养闭环分析")
            if st.button("🧬 召唤 AI 分析今日整体营养缺口"):
                meals_dict = {k: daily[k] for k in ['breakfast','lunch','dinner','snacks'] if daily.get(k)}
                if not meals_dict:
                    st.warning("今天还没有记录足够的饮食哦！")
                else:
                    loader_ui = show_custom_loader("正在生成今日营养元素透视报告...")
                    period_note = "【特别提醒：该女生正处于生理期】" if is_period else ""
                    prompt = f"用户今日饮食：{str(meals_dict)}。目标:{u_data.get('goal','减脂')}。{period_note} 请作为高级营养师分析今天营养摄入比例是否合理，重点指出缺乏的微量元素/宏量元素，并给出明确的补足建议。"
                    daily['daily_nutrition_analysis'] = safe_generate_content(prompt)
                    save_data(records, RECORDS_FILE)
                    loader_ui.empty()
                    st.rerun()
            
            if daily.get('daily_nutrition_analysis'):
                with st.expander("📊 查看今日详细营养缺口报告", expanded=True):
                    st.info(daily['daily_nutrition_analysis'])
    
    # ================= 历史归档与修改窗口 =================
    st.markdown("---")
    st.markdown("### 🕰️ 往日餐饮归档与修改")
    with st.expander("点击展开：查看或修改历史记录（每日24点自动归档）", expanded=False):
        # 筛选出非今天的历史日期并倒序排列
        past_dates = sorted([d for d in records[selected_user].keys() if d != today_str], reverse=True)
        
        if not past_dates:
            st.info("🕒 暂无历史归档数据。每日过了当地时间 24 点后，您的旧数据会自动安全归档于此。")
        else:
            sel_date = st.selectbox("📅 选择要查看的归档日期", past_dates)
            if sel_date:
                archived_data = records[selected_user][sel_date]
                st.caption(f"正在编辑 {sel_date} 的档案记录")
                
                for m_key, m_name in [("breakfast", "早餐"), ("lunch", "午餐"), ("dinner", "晚餐"), ("snacks", "零食")]:
                    if archived_data.get(m_key):
                        with st.container():
                            st.markdown(f"**{m_name}**")
                            # 布局比例：食物文本框占大头，宏量营养素各占一份，保存按钮在最右侧
                            c_txt, c_cal, c_pro, c_car, c_fat, c_btn = st.columns([3.5, 1, 1, 1, 1, 1.5])
                            e_food = c_txt.text_input("内容", value=archived_data[m_key].get('food', ''), key=f"ef_{sel_date}_{m_key}", label_visibility="collapsed")
                            e_cal = c_cal.number_input("热量", value=int(archived_data[m_key].get('calories', 0)), key=f"ec_{sel_date}_{m_key}", label_visibility="collapsed")
                            e_pro = c_pro.number_input("蛋白质", value=int(archived_data[m_key].get('protein', 0)), key=f"ep_{sel_date}_{m_key}", label_visibility="collapsed")
                            e_car = c_car.number_input("碳水", value=int(archived_data[m_key].get('carbs', 0)), key=f"eca_{sel_date}_{m_key}", label_visibility="collapsed")
                            e_fat = c_fat.number_input("脂肪", value=int(archived_data[m_key].get('fat', 0)), key=f"efa_{sel_date}_{m_key}", label_visibility="collapsed")
                            
                            if c_btn.button("💾 确认修改", key=f"btn_{sel_date}_{m_key}"):
                                records[selected_user][sel_date][m_key].update({
                                    'food': e_food, 'calories': e_cal, 'protein': e_pro, 'carbs': e_car, 'fat': e_fat
                                })
                                save_data(records, RECORDS_FILE)
                                st.success(f"✅ {sel_date} 的 {m_name} 数据已永久更新！")
                                st.rerun()
                            st.divider()

    # ================= 月度终极报告 =================
    st.markdown("---")
    st.markdown("### 📅 月度身材与饮食复盘")
    if st.button("📈 生成当月 AI 深度诊断报告"):
        all_data = records.get(selected_user, {})
        if len(all_data) < 3: 
            st.warning("记录少于 3 天，积累更多数据再来生成报告会更准哦！")
        else:
            loader_ui = show_custom_loader("AI 正在深度挖掘未来规划报告...")
            prompt = f"高级身材管理专家。用户({u_data['gender']}, {u_data['weight']}kg, 目标:{u_data.get('goal','减脂')})打卡日志：{json.dumps(all_data, ensure_ascii=False)}。出具专业复盘与次月调整方案(必须包含致命问题诊断和具体采购建议)。"
            report_res = safe_generate_content(prompt)
            loader_ui.empty()
            st.write(report_res)
