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
    import pytz # 如果报错，请确保 pip install pytz

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

# ================= 读取桌面图片并转为 Base64 =================
def get_base64_image(file_path):
    expanded_path = os.path.expanduser(file_path)
    if not os.path.exists(expanded_path):
        return ""
    with open(expanded_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

dog_gif_b64 = get_base64_image("~/Desktop/dog.gif")
dog1_jpg_b64 = get_base64_image("~/Desktop/dog 1.jpeg")

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
        z-index: 10;
        position: relative;
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
    /* 桌面宠物背景图 CSS */
    .bg-pet-left {
        position: fixed; bottom: 20px; left: 20px; width: 180px; 
        opacity: 0.3; z-index: 0; pointer-events: none; /* pointer-events: none 确保不阻挡鼠标点击 */
    }
    .bg-pet-right {
        position: fixed; bottom: 20px; right: 20px; width: 180px; 
        opacity: 0.3; z-index: 0; pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# 注入桌面宠物图片
if dog_gif_b64:
    st.markdown(f'<img src="data:image/gif;base64,{dog_gif_b64}" class="bg-pet-left">', unsafe_allow_html=True)
if dog1_jpg_b64:
    st.markdown(f'<img src="data:image/jpeg;base64,{dog1_jpg_b64}" class="bg-pet-right">', unsafe_allow_html=True)

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
    # 'ben' 用乌拉圭时区，'宝'（及其他人）默认使用中国时区
    tz_str = "Asia/Shanghai" if username == "宝" else "America/Montevideo"
    try:
        try:
            tz = ZoneInfo(tz_str)
        except NameError:
            import pytz
            tz = pytz.timezone(tz_str)
        user_now = datetime.datetime.now(tz)
    except Exception:
        # Fallback to local time if timezone library fails
        user_now = datetime.datetime.now()
    
    return user_now.strftime("%Y-%m-%d"), user_now.weekday()

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
        st.caption("输入授权码即可修改或删除用户档案。")
        admin_auth = st.text_input("管理员授权码", type="password", key="admin_auth")
        if admin_auth == "240909":  # 这里用你的进入密码作为管理员密码
            st.success("✅ 权限已验证")
            target_to_edit = st.selectbox("选择要管理的档案", list(users.keys()), key="target_to_edit")
            
            if target_to_edit:
                t_data = users[target_to_edit]
                with st.form("edit_user_form"):
                    e_gender = st.selectbox("性别", ["男", "女"], index=0 if t_data.get('gender')=="男" else 1)
                    e_goal = st.selectbox("主要目标", ["减脂", "营养监测/维持健康", "增肌"], index=["减脂", "营养监测/维持健康", "增肌"].index(t_data.get('goal', '减脂')))
                    e_height = st.number_input("身高 (cm)", 100, 250, int(t_data.get('height', 170)))
                    e_age = st.number_input("年龄", 10, 100, int(t_data.get('age', 25)))
                    e_weight = st.number_input("体重 (kg)", 30.0, 200.0, float(t_data.get('weight', 65.0)), step=0.1)
                    e_activity = st.selectbox("日常活动量", ["几乎不运动", "轻度活动", "中度活动"], index=["几乎不运动", "轻度活动", "中度活动"].index(t_data.get('activity', '几乎不运动')))
                    
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
                if st.button(f"🗑️ 删除用户 '{target_to_edit}'", type="primary"):
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
    
    # 根据用户所在时区获取今天的日期字符串和星期几
    today_str, current_weekday = get_user_timezone_date(selected_user)
    
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

    # ================= 女生专属生理期选项 =================
    is_period = False
    if u_data['gender'] == '女':
        is_period = st.checkbox("🌸 我当前正处于生理期 (将自动调整推荐与关怀)")

    # 跨天重置逻辑：如果今天的日期不在该用户的记录里，自动创建一天的空数据（旧的按日期妥善保存在 records.json 中）
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
    st.markdown(f"### 📊 今日全景监控 (时区归属: {today_str})")
    
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
                uploaded_img = st.file_uploader("上传美食照片", type=["jpg", "png", "webp"])
                meal_input = st.text_area("补充文字说明 (例如：油很大，半碗饭)", height=100)
                
                if st.button("✨ 开启 AI 深度识图分析"):
                    if not meal_input and not uploaded_img: 
                        st.error("请传图或输入文字描述！")
                    else:
                        with st.spinner("AI 营养师正在精准分析元素..."):
                            period_prompt = "【特别提醒：用户目前处于生理期，请在点评时额外关注是否有补铁、暖身需求，并避免推荐寒凉食物。】" if is_period else ""
                            prompt = f"""
                            用户({u_data['gender']}, {u_data['weight']}kg, 目标:{u_data.get('goal','减脂')})记录了一顿 {meal_type}。
                            补充说明: {meal_input or '无'}。
                            {period_prompt}
                            请识别食物并估算热量和三大营养素。
                            务必返回纯 JSON，不包含任何外部文字或Markdown框！格式严格如下：
                            {{"food": "识别出的食物及分量", "calories": 整数, "protein": 蛋白质克数整数, "carbs": 碳水克数整数, "fat": 脂肪克数整数, "analysis": "简短且专业的营养点评"}}
                            """
                            contents = [prompt] + ([Image.open(uploaded_img)] if uploaded_img else [])
                            
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
                            save_data(records, RECORDS_FILE)
                            st.rerun()
            
            with tab2:
                exercise_input = st.text_area("今天做了什么运动？", height=100)
                if st.button("🔥 计算消耗"):
                    with st.spinner("计算中..."):
                        prompt_ex = f"用户({u_data['weight']}kg)运动: {exercise_input}。返回纯JSON: {{\"burned\": 整数, \"analysis\": \"点评\"}}"
                        try:
                            res_text = safe_generate_content(prompt_ex)
                            json_match = re.search(r'\{[\s\S]*\}', res_text)
                            res = json.loads(json_match.group()) if json_match else {"burned": 0, "analysis": "解析失败"}
                        except Exception:
                            res = {"burned": 0, "analysis": "错误"}
                        
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
                    with st.spinner("正在生成今日营养元素透视报告..."):
                        period_note = "【特别提醒：该女生正处于生理期】" if is_period else ""
                        prompt = f"用户今日饮食：{str(meals_dict)}。目标:{u_data.get('goal','减脂')}。{period_note} 请作为高级营养师分析今天营养摄入比例是否合理，重点指出缺乏的微量元素/宏量元素，并给出明确的补足建议。"
                        daily['daily_nutrition_analysis'] = safe_generate_content(prompt)
                        save_data(records, RECORDS_FILE)
            
            if daily.get('daily_nutrition_analysis'):
                with st.expander("📊 查看今日详细营养缺口报告", expanded=False):
                    st.info(daily['daily_nutrition_analysis'])

# ================= 月度终极报告 =================
st.markdown("---")
st.markdown("### 📅 月度身材与饮食复盘")
if st.button("📈 生成当月 AI 深度诊断报告"):
    all_data = records.get(selected_user, {})
    if len(all_data) < 3: 
        st.warning("记录少于 3 天，积累更多数据再来生成报告会更准哦！")
    else:
        with st.spinner("AI 正在深度挖掘未来规划报告..."):
            u_data = users[selected_user]
            prompt = f"高级身材管理专家。用户({u_data['gender']}, {u_data['weight']}kg, 目标:{u_data.get('goal','减脂')})打卡日志：{json.dumps(all_data, ensure_ascii=False)}。出具专业复盘与次月调整方案(必须包含致命问题诊断和具体采购建议)。"
            st.write(safe_generate_content(prompt))
