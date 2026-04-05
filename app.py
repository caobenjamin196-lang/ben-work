import streamlit as st
import json
import os
import datetime
import re
import base64
import time
import google.generativeai as genai
from PIL import Image
import firebase_admin
from firebase_admin import credentials, firestore

# 兼容不同的 Python 版本来处理时区
try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz 

# ================= 🚨 页面配置 =================
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
    local_path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    mac_path = os.path.expanduser(f"~/Desktop/{filename}")
    if os.path.exists(mac_path):
        with open(mac_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
            
    return ""

# 加载边角装饰图片及加载动画素材
dog_gif_b64 = get_base64_media("dog.gif")
dog1_jpg_b64 = get_base64_media("dog 1.jpeg")

# ================= 动态背景与边缘虚化遮罩注入 =================
def inject_dynamic_bg(weekday_index):
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
            /* 边缘虚化遮罩 */
            .bg-vignette {{
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: radial-gradient(circle, rgba(247,249,252,0) 20%, rgba(247,249,252,0.95) 100%);
                z-index: -1; pointer-events: none;
            }}
        </style>
        <div class="dynamic-bg"></div>
        <div class="bg-vignette"></div>
        ''', unsafe_allow_html=True)

# ================= 全局 CSS 深度优化 =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&family=Varela+Round&display=swap');
    
    html, body, div:not([class*="icon"]), p, span:not([class*="icon"]), label {
        font-family: 'Nunito', 'Varela Round', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        color: #1f2937; 
    }
    
    .material-symbols-rounded, .material-icons, [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-weight: 900 !important;
        color: #111827 !important;
        letter-spacing: 0.5px;
        font-family: 'Nunito', 'Varela Round', 'PingFang SC', sans-serif;
    }

    p, .stMarkdown { font-weight: 700; }
    strong { font-weight: 900 !important; color: #065f46 !important; }

    .stApp > header { background-color: transparent !important; }
    
    .stApp .main .block-container {
        background: rgba(255, 255, 255, 0.93) !important;
        border-radius: 28px !important; 
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
    
    .stButton > button, [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important; 
        border: 1px solid rgba(255,255,255,0.4) !important; 
        border-radius: 20px !important; 
        padding: 0.6rem 1rem !important; 
        font-weight: 800 !important; 
        font-size: 1.05rem !important;
        transition: all 0.3s ease !important;
        box-shadow: inset 0 2px 4px rgba(255,255,255,0.4), 0 4px 8px rgba(16,185,129,0.3) !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
    }
    .stButton > button:hover, [data-testid="stFileUploader"] button:hover { 
        transform: translateY(-3px) scale(1.02) !important; 
        box-shadow: inset 0 2px 4px rgba(255,255,255,0.5), 0 10px 20px -3px rgba(16,185,129,0.45) !important; 
        color: white !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: rgba(240, 253, 244, 0.6) !important;
        border: 2px dashed #10b981 !important;
        border-radius: 20px !important;
    }
    
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
    .bg-pet-left { position: fixed; bottom: 10px; left: 10px; width: 350px; opacity: 0.25; z-index: 0; pointer-events: none; }
    .bg-pet-right { position: fixed; bottom: 10px; right: 10px; width: 350px; opacity: 0.25; z-index: 0; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

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

# ================= ☁️ 云端数据库持久化 (Firebase Firestore) =================
if not firebase_admin._apps:
    cert_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(cert_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

USERS_COLLECTION = "users"
RECORDS_COLLECTION = "records"

def load_data(collection_name):
    """拉取全局基础用户配置"""
    try:
        docs = db.collection(collection_name).stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except Exception as e:
        st.error(f"⚠️ 云端数据加载失败: {e}")
        return {}

def save_user_data(user_id, user_data, collection_name):
    """【隔离写入】：只把当前用户的数据安全地盖到他的专属文档上"""
    try:
        db.collection(collection_name).document(user_id).set(user_data)
    except Exception as e:
        st.sidebar.error(f"云端同步失败: {e}")

# 初始化拉取用户配置 
users = load_data(USERS_COLLECTION)

# ================= 时区与日期计算 =================
def get_user_timezone_date(username, u_data):
    """【强制时区绑定】"""
    if username == "本比" or username.lower() == "ben":
        tz_str = "America/Montevideo"
    elif username == "宝比":
        tz_str = "Asia/Shanghai"
    else:
        tz_str = u_data.get("timezone", "Asia/Shanghai")
            
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
        inject_dynamic_bg(datetime.datetime.now().weekday())
        
        with st.form("new_user_form"):
            new_name = st.text_input("如何称呼您？")
            gender = st.selectbox("性别", ["男", "女"])
            timezone = st.selectbox("所在时区", ["Asia/Shanghai", "America/Montevideo", "America/New_York", "Europe/London"])
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
                    "timezone": timezone,
                    "period": {"is_active": False, "last_start": None, "last_end": None, "cycle_length": 28}
                }
                save_user_data(new_name, users[new_name], USERS_COLLECTION)
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
                g_idx = g_opts.index(t_data.get('gender', '男')) if t_data.get('gender', '男') in g_opts else 0
                
                goal_opts = ["减脂", "营养监测/维持健康", "增肌"]
                goal_idx = goal_opts.index(t_data.get('goal', '减脂')) if t_data.get('goal', '减脂') in goal_opts else 0
                
                tz_opts = ["Asia/Shanghai", "America/Montevideo", "America/New_York", "Europe/London"]
                t_tz = t_data.get('timezone', "America/Montevideo" if target_to_edit.lower() in ["ben", "本比"] else "Asia/Shanghai")
                tz_idx = tz_opts.index(t_tz) if t_tz in tz_opts else 0

                act_opts = ["几乎不运动", "轻度活动", "中度活动"]
                act_idx = act_opts.index(t_data.get('activity', '几乎不运动')) if t_data.get('activity', '几乎不运动') in act_opts else 0

                with st.form("edit_user_form"):
                    e_gender = st.selectbox("性别", g_opts, index=g_idx)
                    e_timezone = st.selectbox("所在时区", tz_opts, index=tz_idx)
                    e_goal = st.selectbox("主要目标", goal_opts, index=goal_idx)
                    e_height = st.number_input("身高 (cm)", 100, 250, int(t_data.get('height', 170)))
                    e_age = st.number_input("年龄", 10, 100, int(t_data.get('age', 25)))
                    e_weight = st.number_input("体重 (kg)", 30.0, 200.0, float(t_data.get('weight', 65.0)), step=0.1)
                    e_activity = st.selectbox("日常活动量", act_opts, index=act_idx)
                    
                    if st.form_submit_button("📝 强制保存修改"):
                        bmr, tdee, target, macros = calculate_metrics(e_gender, e_weight, e_height, e_age, e_activity, e_goal)
                        users[target_to_edit].update({
                            "gender": e_gender, "age": e_age, "height": e_height, "weight": e_weight, "activity": e_activity, 
                            "goal": e_goal, "bmr": bmr, "tdee": tdee, "target": target, "macros": macros, "timezone": e_timezone
                        })
                        save_user_data(target_to_edit, users[target_to_edit], USERS_COLLECTION)
                        st.success(f"已更新 {target_to_edit} 的档案！")
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🗑️ 永久删除 '{target_to_edit}'", type="primary"):
                    db.collection(USERS_COLLECTION).document(target_to_edit).delete()
                    db.collection(RECORDS_COLLECTION).document(target_to_edit).delete()
                    st.success("已删除该档案！")
                    st.rerun()

if not users:
    st.info("👋 欢迎！请先在左侧建立身体档案。")
    st.stop()

if selected_user and selected_user != "➕ 新建身体档案...":
    u_data = users[selected_user]
    today_str, current_weekday, today_date = get_user_timezone_date(selected_user, u_data)
    inject_dynamic_bg(current_weekday)

    # ================= 【核心修复：绝对数据隔离拉取】 =================
    user_record_doc = db.collection(RECORDS_COLLECTION).document(selected_user).get()
    user_records = user_record_doc.to_dict() if user_record_doc.exists else {}

    # ================= 每周一更新体重提醒 =================
    if current_weekday == 0:
        st.warning(f"📅 **今天是{selected_user}时区的周一！** 新的一周，为了让 AI 监控更精准，请记录一下最新体重吧！")
        with st.expander("⚖️ 更新本周体重", expanded=False):
            new_weight = st.number_input("最新空腹体重 (kg)", value=float(u_data['weight']), step=0.1, key=f"wt_{selected_user}_{today_str}")
            if st.button("更新并重算计划", key=f"btn_wt_{selected_user}_{today_str}"):
                bmr, tdee, target, macros = calculate_metrics(u_data['gender'], new_weight, u_data['height'], u_data['age'], u_data['activity'], u_data.get('goal', '减脂'))
                users[selected_user].update({"weight": new_weight, "bmr": bmr, "tdee": tdee, "target": target, "macros": macros})
                save_user_data(selected_user, users[selected_user], USERS_COLLECTION)
                st.success("计划已更新！")
                st.rerun()

    # ================= 🌸 智能生理期追踪闭环 (全新升级天数追踪) =================
    is_period = False
    if u_data.get('gender') == '女':
        # 安全获取并初始化 period 字段，确保不会因历史遗留问题丢失
        needs_save = False
        if 'period' not in u_data:
            u_data['period'] = {"is_active": False, "last_start": None, "last_end": None, "cycle_length": 28}
            needs_save = True
        
        p_data = u_data['period']
        
        st.markdown("### 🌸 生理期智能追踪")
        
        if p_data.get('is_active'):
            # 精确计算今天是生理期的第几天
            days_in = 1
            if p_data.get('last_start'):
                try:
                    start_dt = datetime.datetime.strptime(p_data['last_start'], "%Y-%m-%d").date()
                    days_in = (today_date - start_dt).days + 1
                except:
                    pass
            
            # 前7天每日强提醒确认，超过7天增加警示
            if days_in <= 7:
                st.error(f"🩸 **您当前正处于生理期（第 {days_in} 天）。** AI 营养师已自动介入，为您增加温暖热量预算，请注意保暖！")
                st.info("🌸 **每日确认**：今天大姨妈走了吗？如果已经彻底干净，请点击下方按钮恢复正常追踪。")
            else:
                st.error(f"🩸 **您当前正处于生理期（第 {days_in} 天）。**")
                st.warning("🌸 您的生理期记录已经超过 7 天啦！如果大姨妈已经彻底离开，请千万记得点击下方按钮结束本次记录哦！")
                
            if st.button("✅ 确认大姨妈已彻底结束", key=f"p_end_{selected_user}_{today_str}"):
                p_data['is_active'] = False
                p_data['last_end'] = today_str
                users[selected_user]['period'] = p_data
                save_user_data(selected_user, users[selected_user], USERS_COLLECTION)
                st.success("已记录，系统恢复正常追踪模式！")
                st.rerun()
            is_period = True
        else:
            if p_data.get('last_start'):
                last_start_dt = datetime.datetime.strptime(p_data['last_start'], "%Y-%m-%d").date()
                next_start_dt = last_start_dt + datetime.timedelta(days=p_data['cycle_length'])
                days_left = (next_start_dt - today_date).days
                
                if days_left > 3:
                    st.info(f"⏳ 距离下一次生理期预计还有 **{days_left}** 天。")
                elif 0 < days_left <= 3:
                    st.warning(f"⚠️ **倒计时提醒**：距离下次生理期仅剩 **{days_left}** 天！请提前准备好保暖物资，避免寒凉食物。")
                else:
                    st.error(f"🚨 **到期确认**：预计生理期已经到了 (已延迟 {abs(days_left)} 天)。您的姨妈来了吗？")
                
                if st.button("🩸 是的，大姨妈今天来了", key=f"p_start_{selected_user}_{today_str}"):
                    p_data['is_active'] = True
                    p_data['last_start'] = today_str
                    users[selected_user]['period'] = p_data
                    save_user_data(selected_user, users[selected_user], USERS_COLLECTION)
                    st.rerun()
            else:
                st.info("首次使用，当您大姨妈来临之际请在此标记，系统将自动开启下月的循环提醒。")
                if st.button("🩸 标记今天生理期开始", key=f"p_first_{selected_user}_{today_str}"):
                    p_data['is_active'] = True
                    p_data['last_start'] = today_str
                    users[selected_user]['period'] = p_data
                    save_user_data(selected_user, users[selected_user], USERS_COLLECTION)
                    st.rerun()
            is_period = False
            
        # 如果是老用户强行补齐字段，顺手保存一下防丢失
        if needs_save:
            save_user_data(selected_user, users[selected_user], USERS_COLLECTION)

    # ================= 跨天重置与保存逻辑 =================
    if today_str not in user_records:
        user_records[today_str] = {"breakfast": None, "lunch": None, "dinner": None, "snacks": None, "exercise": None, "daily_nutrition_analysis": None}
    if "snacks" not in user_records[today_str]: user_records[today_str]["snacks"] = None
    
    daily = user_records[today_str]
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
                meal_type = st.radio("当前餐段", ["早餐", "午餐", "晚餐", "零食/加餐"], horizontal=True, key=f"radio_meal_{selected_user}_{today_str}")
                meal_key = {"早餐": "breakfast", "午餐": "lunch", "晚餐": "dinner", "零食/加餐": "snacks"}[meal_type]
                
                uploaded_imgs = st.file_uploader("上传美食照片 (可多图上传，支持 500MB 以内)", type=["jpg", "png", "webp"], accept_multiple_files=True, key=f"imgs_{selected_user}_{meal_type}_{today_str}")
                meal_input = st.text_area("补充文字说明 (例如：油很大，半碗饭)", height=100, key=f"txt_{selected_user}_{meal_type}_{today_str}")
                
                if st.button("✨ 开启 AI 深度识图分析", key=f"btn_ai_{selected_user}_{meal_type}_{today_str}"):
                    if not meal_input and not uploaded_imgs: 
                        st.error("请传图或输入文字描述！")
                    else:
                        with st.spinner("AI 营养师正在精准分析食物元素..."):
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
                            
                            daily[meal_key] = res
                            save_user_data(selected_user, user_records, RECORDS_COLLECTION)
                            st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                if daily.get(meal_key):
                    st.info(f"👉 当前 {meal_type} 已有记录。如果数据有误，您可以直接清空并重新录入。")
                    if st.button(f"🗑️ 彻底清空当前 {meal_type} 记录", key=f"clear_{selected_user}_{meal_type}_{today_str}"):
                        daily[meal_key] = None
                        save_user_data(selected_user, user_records, RECORDS_COLLECTION)
                        st.success("清理成功！")
                        st.rerun()
            
            with tab2:
                exercise_input = st.text_area("今天做了什么运动？", height=100, key=f"txt_ex_{selected_user}_{today_str}")
                if st.button("🔥 计算消耗", key=f"btn_ex_{selected_user}_{today_str}"):
                    with st.spinner("正在核算运动卡路里..."):
                        prompt_ex = f"用户({u_data['weight']}kg)运动: {exercise_input}。返回纯JSON: {{\"burned\": 整数, \"analysis\": \"点评\"}}"
                        try:
                            res_text = safe_generate_content(prompt_ex)
                            json_match = re.search(r'\{[\s\S]*\}', res_text)
                            res = json.loads(json_match.group()) if json_match else {"burned": 0, "analysis": "解析失败"}
                        except Exception:
                            res = {"burned": 0, "analysis": "错误"}
                        
                        daily['exercise'] = {"text": exercise_input, "burned_calories": res.get("burned", 0), "analysis": res.get("analysis", "")}
                        save_user_data(selected_user, user_records, RECORDS_COLLECTION)
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                if daily.get('exercise'):
                    if st.button("🗑️ 彻底清空今日运动记录", key=f"clear_ex_{selected_user}_{today_str}"):
                        daily['exercise'] = None
                        save_user_data(selected_user, user_records, RECORDS_COLLECTION)
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
            if st.button("🧬 召唤 AI 分析今日整体营养缺口", key=f"btn_close_{selected_user}_{today_str}"):
                meals_dict = {k: daily[k] for k in ['breakfast','lunch','dinner','snacks'] if daily.get(k)}
                if not meals_dict:
                    st.warning("今天还没有记录足够的饮食哦！")
                else:
                    with st.spinner("正在生成今日营养元素透视报告..."):
                        period_note = "【特别提醒：该女生正处于生理期】" if is_period else ""
                        prompt = f"用户今日饮食：{str(meals_dict)}。目标:{u_data.get('goal','减脂')}。{period_note} 请作为高级营养师分析今天营养摄入比例是否合理，重点指出缺乏的微量元素/宏量元素，并给出明确的补足建议。"
                        daily['daily_nutrition_analysis'] = safe_generate_content(prompt)
                        save_user_data(selected_user, user_records, RECORDS_COLLECTION)
                        st.rerun()
            
            if daily.get('daily_nutrition_analysis'):
                with st.expander("📊 查看今日详细营养缺口报告", expanded=True):
                    st.info(daily['daily_nutrition_analysis'])
    
    # ================= 历史归档与补录窗口 =================
    st.markdown("---")
    st.markdown("### 🕰️ 往日餐饮补录与修改")
    with st.expander("点击展开：补录遗漏数据或修改历史记录", expanded=False):
        max_date = today_date - datetime.timedelta(days=1)
        default_date = max_date
        
        sel_date_obj = st.date_input("📅 选择要查看或补录的日期", value=default_date, max_value=max_date, key=f"date_input_{selected_user}_{today_str}")
        
        if sel_date_obj:
            sel_date = sel_date_obj.strftime("%Y-%m-%d")
            
            if sel_date not in user_records:
                user_records[sel_date] = {"breakfast": None, "lunch": None, "dinner": None, "snacks": None, "exercise": None, "daily_nutrition_analysis": None}
                
            archived_data = user_records[sel_date]
            st.caption(f"正在查看或补录 **{sel_date}** 的档案记录")
            
            for m_key, m_name in [("breakfast", "早餐"), ("lunch", "午餐"), ("dinner", "晚餐"), ("snacks", "零食")]:
                if not archived_data.get(m_key):
                    archived_data[m_key] = {}
                    
                with st.container():
                    st.markdown(f"**{m_name}**")
                    c_txt, c_cal, c_pro, c_car, c_fat, c_btn = st.columns([3.5, 1, 1, 1, 1, 1.5])
                    e_food = c_txt.text_input("内容", value=archived_data[m_key].get('food', ''), key=f"ef_{selected_user}_{sel_date}_{m_key}", label_visibility="collapsed", placeholder=f"输入{m_name}的内容")
                    e_cal = c_cal.number_input("热量", value=int(archived_data[m_key].get('calories', 0)), key=f"ec_{selected_user}_{sel_date}_{m_key}", label_visibility="collapsed")
                    e_pro = c_pro.number_input("蛋白质", value=int(archived_data[m_key].get('protein', 0)), key=f"ep_{selected_user}_{sel_date}_{m_key}", label_visibility="collapsed")
                    e_car = c_car.number_input("碳水", value=int(archived_data[m_key].get('carbs', 0)), key=f"eca_{selected_user}_{sel_date}_{m_key}", label_visibility="collapsed")
                    e_fat = c_fat.number_input("脂肪", value=int(archived_data[m_key].get('fat', 0)), key=f"efa_{selected_user}_{sel_date}_{m_key}", label_visibility="collapsed")
                    
                    if c_btn.button("💾 保存修改", key=f"btn_save_{selected_user}_{sel_date}_{m_key}"):
                        if e_food or e_cal > 0:
                            user_records[sel_date][m_key].update({
                                'food': e_food, 'calories': e_cal, 'protein': e_pro, 'carbs': e_car, 'fat': e_fat
                            })
                            save_user_data(selected_user, user_records, RECORDS_COLLECTION)
                            st.success(f"✅ {sel_date} 的 {m_name} 数据已成功记录！")
                            st.rerun()
                        else:
                            st.warning("食物内容或热量不能为空哦！")
                    st.divider()

    # ================= 月度终极报告 =================
    st.markdown("---")
    st.markdown("### 📅 月度身材与饮食复盘")
    if st.button("📈 生成当月 AI 深度诊断报告", key=f"btn_report_{selected_user}_{today_str}"):
        all_data = user_records
        if len(all_data) < 3: 
            st.warning("记录少于 3 天，积累更多数据再来生成报告会更准哦！")
        else:
            with st.spinner("AI 正在深度挖掘未来规划报告..."):
                prompt = f"高级身材管理专家。用户({u_data['gender']}, {u_data['weight']}kg, 目标:{u_data.get('goal','减脂')})打卡日志：{json.dumps(all_data, ensure_ascii=False)}。出具专业复盘与次月调整方案(必须包含致命问题诊断和具体采购建议)。"
                report_res = safe_generate_content(prompt)
                st.write(report_res)
