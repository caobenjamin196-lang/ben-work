import streamlit as st
import json
import os
import datetime
import re
import google.generativeai as genai
from PIL import Image

# ================= 🚨 修复致命错误 =================
# st.set_page_config 必须是整个脚本的第一个 Streamlit 命令，不能被任何界面代码拦截！
st.set_page_config(page_title="🍏 AI 减脂与营养监督", layout="wide", initial_sidebar_state="expanded")

# ================= 访问权限控制 =================
def check_password():
    # 设定你的专属邀请码
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

# 拦截所有没密码的人
if not check_password():
    st.stop()

# ================= 自定义 CSS 美化 =================
st.markdown("""
<style>
 /* =============== 终极开源线条小狗背景 ================ */
 div.stApp {
     background: url("https://raw.githubusercontent.com/openclaw/openclaw/main/docs/static/dog.png") no-repeat center center fixed !important;
     background-color: #f7f9fc !important;
     background-size: cover !important;
 }
 
 /* 强行穿透所有的内层遮挡板 */
 .stApp > header { background-color: transparent !important; }
 
 .stApp .main .block-container {
     background: rgba(255, 255, 255, 0.85) !important;
     border-radius: 20px !important;
     padding: 3rem 2rem !important;
     box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15) !important;
     backdrop-filter: blur(12px) !important;
     -webkit-backdrop-filter: blur(12px) !important;
     border: 1px solid rgba(255, 255, 255, 0.3) !important;
     max-width: 1200px !important;
     margin-top: 2rem !important;
 }
 
 section[data-testid="stSidebar"] {
     background-color: rgba(255, 255, 255, 0.95) !important;
 }
 
 div[data-testid="stMetricValue"] { color: #10b981; font-weight: bold; }
 
 .stButton > button {
     background: linear-gradient(135deg, #10b981 0%, #059669 100%);
     color: white; border: none; border-radius: 8px;
     padding: 0.6rem 1rem; font-weight: 600; width: 100%;
     transition: all 0.3s ease;
 }
 .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 10px -3px rgba(16,185,129,0.3); color: white;}
 
 .budget-info {
     background-color: #e0f2fe; color: #0369a1; padding: 12px 16px;
     border-radius: 8px; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px;
     border-left: 4px solid #0ea5e9;
 }
</style>
""", unsafe_allow_html=True)

# ================= API Key 配置 =================
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("GOOGLE_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

st.title("✨ 您的专属 AI 减脂与营养监督员")
st.markdown("<p style='text-align: center; color: #6b7280; font-size: 1.1rem; margin-top: -15px; margin-bottom: 20px;'>不仅算热量，更懂营养学。吃得明明白白，瘦得轻轻松松。</p>", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/avocado.png", width=60)
    st.header("⚙️ 系统设置")
    input_key = st.text_input("配置 Google API Key", type="password", value=api_key if api_key else "")
    if input_key and input_key != api_key:
        api_key = input_key
        with open(".env", "w") as f: 
            f.write(f'GOOGLE_API_KEY="{api_key}"\n')
        st.success("API Key 已保存！")

if api_key:
    genai.configure(api_key=api_key)
    # ================= 🚨 强制使用万能版 gemini-1.5-flash-latest 模型 =================
    model = genai.GenerativeModel('gemini-1.5-flash-latest') 
else:
    st.warning("👈 请先在左侧输入您的 GOOGLE_API_KEY 来激活 AI 引擎。")
    st.stop()

# ================= 数据持久化 =================
USERS_FILE = "users.json"
RECORDS_FILE = "records.json"

def load_data(path):
    return json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else {}

def save_data(data, path):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)

users = load_data(USERS_FILE)
records = load_data(RECORDS_FILE)

def calculate_tdee(gender, weight, height, age, activity):
    bmr = 10*weight + 6.25*height - 5*age + (5 if gender=="男" else -161)
    activity_multiplier = {"几乎不运动 (坐办公室)": 1.2, "轻度活动 (日常走动)": 1.375, "中度活动 (体力劳动)": 1.55}.get(activity, 1.2)
    tdee = int(bmr * activity_multiplier)
    return tdee, tdee - 400

# ================= 侧边栏用户档案 =================
with st.sidebar:
    st.markdown("---")
    st.header("👤 档案与目标")
    user_names = list(users.keys())
    selected_user = st.selectbox("当前使用者", user_names + ["➕ 新建身体档案..."], index=0 if user_names else len(user_names))

    if selected_user == "➕ 新建身体档案...":
        with st.form("new_user_form"):
            new_name = st.text_input("如何称呼您？")
            gender = st.selectbox("性别", ["男", "女"])
            height = st.number_input("身高 (cm)", 100, 250, 170)
            age = st.number_input("年龄", 10, 100, 25)
            weight = st.number_input("体重 (kg)", 30, 200, 65)
            activity = st.selectbox("日常活动量", ["几乎不运动 (坐办公室)", "轻度活动 (日常走动)", "中度活动 (体力劳动)"])
            
            if st.form_submit_button("💾 生成方案") and new_name:
                tdee, target = calculate_tdee(gender, weight, height, age, activity)
                users[new_name] = {"gender": gender, "age": age, "height": height, "weight": weight, "activity": activity, "tdee": tdee, "target": target}
                save_data(users, USERS_FILE)
                st.rerun()
    else:
        u_data = users[selected_user]
        st.info(f"🦸 **{selected_user}**\n\n📏 {u_data['height']}cm | ⚖️ {u_data['weight']}kg\n\n🔥 维持热量: {u_data['tdee']} kcal\n🎯 减脂限额: {u_data['target']} kcal")

if not users:
    st.info("👋 欢迎！请先在左侧建立身体档案。")
    st.stop()

# ================= 主界面功能 =================
if selected_user and selected_user != "➕ 新建身体档案...":
    today_str = str(datetime.date.today())
    if selected_user not in records: 
        records[selected_user] = {}
    if today_str not in records[selected_user]:
        records[selected_user][today_str] = {"breakfast": None, "lunch": None, "dinner": None, "exercise": None, "daily_nutrition_analysis": None}
    
    daily = records[selected_user][today_str]
    target = users[selected_user]['target']
    u_weight = users[selected_user]['weight']
    u_gender = users[selected_user]['gender']
    
    consumed = sum([daily[k]['calories'] for k in ['breakfast', 'lunch', 'dinner'] if daily[k]])
    burned = daily['exercise']['burned_calories'] if daily['exercise'] else 0
    remaining = target - consumed + burned
    
    st.markdown("### 📊 今日热量账本")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 预算 (减脂期)", f"{target} kcal")
    c2.metric("🍔 摄入 (饮食)", f"{consumed} kcal", delta_color="inverse")
    c3.metric("🏃 消耗 (运动)", f"{burned} kcal")
    c4.metric("⚖️ 结余 (剩余可吃)", f"{remaining} kcal", delta_color="normal" if remaining >= 0 else "inverse")
    
    st.progress(min(max(consumed / (target + burned + 0.001), 0.0), 1.0))
    st.markdown("""
    <div class="budget-info">
    💡 <b>关于减脂预算的硬核科普：</b><br>
    上方的【目标预算】是你今天的<b>绝对安全线</b>。这个数值已经提前帮你扣除了每天 400 大卡的热量缺口。
    这意味着，<b>只要你今天吃满这个预算值，你就已经处于稳健的减脂状态了！</b><br>
    ❌ <b>千万不要为了追求速度，吃得比预算少很多！</b> 强行制造过大缺口会导致严重掉肌肉、基础代谢受损、大姨妈出走、以及后期的疯狂暴食反弹。请安心把预算吃满！
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        with st.container():
            st.markdown("### 📸 记录饮食与运动")
            tab1, tab2 = st.tabs(["🍽️ 记饮食", "🏃 记运动"])
            
            with tab1:
                meal_type = st.radio("当前餐段", ["早餐", "午餐", "晚餐"], horizontal=True)
                meal_key = {"早餐": "breakfast", "午餐": "lunch", "晚餐": "dinner"}[meal_type]
                uploaded_img = st.file_uploader("上传美食照片", type=["jpg", "png", "webp"])
                meal_input = st.text_area("补充文字说明 (例如：油很大，半碗饭)", height=100)
                
                if st.button("✨ 开启 AI 深度分析"):
                    if not meal_input and not uploaded_img: 
                        st.error("请传图或输入文字描述！")
                    else:
                        with st.spinner("AI 营养师正在分析..."):
                            prompt = f"用户({u_gender},{u_weight}kg)记录饮食。补充说明: {meal_input or '无'}。请识别食物并估算卡路里，返回纯JSON，不要输出任何其他文字，格式严格如下: {{\"food\": \"食物及分量\", \"calories\": 整数, \"analysis\": \"简短点评\"}}"
                            contents = [prompt] + ([Image.open(uploaded_img)] if uploaded_img else [])
                            
                            try:
                                res_text = model.generate_content(contents).text
                                # 💡 改进：正则提取防崩溃
                                json_match = re.search(r'\{.*\}', res_text.replace('\n', ''), re.DOTALL)
                                if json_match:
                                    res = json.loads(json_match.group())
                                else:
                                    res = {"food": meal_input or "未知食物", "calories": 0, "analysis": "AI 返回格式有误，未找到JSON。"}
                            except Exception as e:
                                res = {"food": "解析失败", "calories": 0, "analysis": f"AI服务出错: {str(e)}"}
                                
                            daily[meal_key] = {"text": res.get("food", meal_input), "calories": res.get("calories", 0), "analysis": res.get("analysis", "")}
                            save_data(records, RECORDS_FILE)
                            st.rerun()
                            
            with tab2:
                exercise_input = st.text_area("今天做了什么运动？", height=100)
                if st.button("🔥 计算消耗"):
                    with st.spinner("计算中..."):
                        prompt_ex = f"用户运动: {exercise_input}。返回纯JSON，不要多余文字: {{\"burned\": 整数, \"analysis\": \"点评\"}}"
                        try:
                            res_text = model.generate_content(prompt_ex).text
                            json_match = re.search(r'\{.*\}', res_text.replace('\n', ''), re.DOTALL)
                            if json_match:
                                res = json.loads(json_match.group())
                            else:
                                res = {"burned": 0, "analysis": "AI 返回格式有误。"}
                        except Exception as e:
                            res = {"burned": 0, "analysis": f"AI服务出错: {str(e)}"}
                            
                        daily['exercise'] = {"text": exercise_input, "burned_calories": res.get("burned", 0), "analysis": res.get("analysis", "")}
                        save_data(records, RECORDS_FILE)
                        st.rerun()

    with col_right:
        with st.container():
            st.markdown("### 📝 今日打卡清单")
            for m_key, m_name, icon in [("breakfast", "早餐", "🥞"), ("lunch", "午餐", "🍱"), ("dinner", "晚餐", "🥗")]:
                if daily[m_key]:
                    with st.expander(f"{icon} {m_name}账单 (+{daily[m_key]['calories']} kcal)", expanded=True):
                        st.write(f"**内容**: {daily[m_key]['text']}\n\n**点评**: {daily[m_key]['analysis']}")
            
            if daily['exercise']:
                with st.expander(f"🏃 运动流水 (-{daily['exercise']['burned_calories']} kcal)", expanded=True):
                    st.write(f"**内容**: {daily['exercise']['text']}\n\n**点评**: {daily['exercise']['analysis']}")
            
            st.markdown("---")
            st.markdown("### 🥗 每日营养闭环分析")
            if st.button("🧬 召唤 AI 分析今日整体营养缺口"):
                meals_dict = {k: daily[k] for k in ['breakfast','lunch','dinner'] if daily[k]}
                meals_text = str(meals_dict)
                if len(meals_dict) == 0:
                    st.warning("今天还没有记录足够的饮食哦！")
                else:
                    with st.spinner("正在生成今日营养元素透视报告..."):
                        prompt = f"用户今日饮食记录：{meals_text}。请作为高级营养师，分析今天蛋白质、碳水、脂肪、膳食纤维和微量元素的摄入比例是否合理。重点指出【缺乏了什么元素】，并给出今晚或明早吃什么食材来【补足】的明确建议。500字左右，排版清晰易读。"
                        report = model.generate_content(prompt).text
                        daily['daily_nutrition_analysis'] = report
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
        st.warning("记录天数少于 3 天，积累更多数据后再来生成月度报告会更准哦！")
    else:
        with st.spinner("AI 正在深度挖掘您过去记录的所有饮食与运动数据，出具千字级未来规划报告..."):
            history_str = json.dumps(all_data, ensure_ascii=False)
            u_data = users[selected_user]
            prompt = f"""
            你是一位顶级的身材管理专家。这是用户({u_data['gender']}, {u_data['weight']}kg, 减脂期)当月的所有饮食和运动打卡日志：
            {history_str}
            
            请出具一份极其专业的「当月复盘与次月减脂规划报告」，必须包含：
            1. 当月热量与营养总结（暴露出这几个月他们最爱吃什么，碳水或脂肪有没有整体超标）。
            2. 发现的致命问题（比如是不是蔬菜吃得太少，或者热量缺口做得不好）。
            3. 【核心输出】下个月的针对性摄取建议与饮食结构调整方案（明确告诉他们下个月哪几样食材必须增加买入，哪几样必须减少）。
            使用 Markdown 格式，语气要专业、有温度且一针见血。
            """
            monthly_report = model.generate_content(prompt).text
            st.markdown("### 🏆 您的专属月度营养与减脂报告")
            st.write(monthly_report)
