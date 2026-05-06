import streamlit as st
from openai import OpenAI
import pypdf

# ==========================================
# 1. 页面基本配置
# ==========================================
st.set_page_config(
    page_title="AI Physics Tutor - Beta 2.0 Pro", 
    page_icon="🌌", 
    layout="centered"
)

# ==========================================
# 2. 会话状态初始化 
# ==========================================
if "result_text" not in st.session_state:
    st.session_state.result_text = None
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = ""
if "current_file_name" not in st.session_state:
    st.session_state.current_file_name = ""

# ==========================================
# 3. 侧边栏配置
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ 系统设置")
    st.markdown("为你独家定制的 **硬核理论物理** 推导引擎。")
    
    api_key = st.text_input("🔑 DeepSeek API Key:", type="password", help="在此输入你的 API Key")
    st.markdown("👉 [点击获取 DeepSeek API Key](https://platform.deepseek.com/)")
    
    st.divider()
    st.caption("当前版本: Beta 2.0 Pro (纯物理科班版)")
    st.caption("引擎: DeepSeek-Chat")

# ==========================================
# 4. 核心 Prompt 模板 (史诗级物理科班化改造)
# ==========================================
SYSTEM_PROMPT = """你是一个从事理论物理与实验物理研究的顶尖学者及物理专业辅导大牛。
用户会提供一份【PDF提取文本】，以及一条【解析指令】。

你的任务是：
1. 精准锁定题目，无视原书可能粗略的解答，在你的理论框架内重新推演。
2. 以最严谨的物理科班视角重新拆解，明确所有的物理假设、参考系选择、边界条件。

【⚠️ 绝对排版指令 - 极其重要】
所有的数学公式、物理量、微积分算符必须使用 LaTeX 格式：
1. 行内公式用单美元符号：$E=mc^2$、$\mathrm{d}V$、$i\hbar$
2. 独立公式用双美元符号：$$\oint \mathbf{E} \cdot \mathrm{d}\mathbf{A} = \frac{Q_{\text{enc}}}{\varepsilon_0}$$
3. 绝对禁止使用 \\( 和 \\) 或 \\[ 和 \\]！

请严格按照以下专业格式输出，不要有任何多余的寒暄：

### 📌 物理图像与模型建构
👉 **核心物理本质**：(高度概括系统，如：中心力场轨道问题、含时微扰、非惯性系动力学、理想气体可逆绝热过程等)
👉 **物理假设与近似**：(列出隐性假设，例如：忽略次级辐射、刚体近似、非相对论极限、长波近似等)

### 🧠 动力学/热力学思路
👉 **参考系与坐标选择**：(说明为何选择该参考系或广义坐标最优化)
👉 **对称性与守恒律**：(指出系统具备的对称性，以及诺特定理对应的守恒量)

### 📐 支配方程与定解条件
- **核心方程**：(列出支配方程，如牛顿第二定律微分形式、拉格朗日量/哈密顿量、薛定谔方程或麦克斯韦方程组)
- **初始/边界条件**：(明确微积分求解过程中的定解条件)

### ✍️ 解析推导与严密解答
(以极其严密的数理逻辑，给出从基本原理到最终结果的完整解析推导。直接可作为高分答卷，每一步微积分变换需点明依据，如高斯定理、泰勒展开、微扰一阶项等)

### 🧮 物理意义探讨 (量纲与极限分析)
👉 **量纲检验**：(验证最终结果表达式的量纲是否绝对自洽)
👉 **渐近极限**：(探讨当某变量趋于0或无穷大时，该结果退化为哪种经典物理情形，证明其合理性)
"""

# ==========================================
# 5. 主界面 UI 
# ==========================================
st.markdown("# 🌌 AI Physics Tutor <span style='font-size: 20px; color: #2563eb; background: #e0e7ff; padding: 4px 8px; border-radius: 8px;'>beta 2.0 Pro</span>", unsafe_allow_html=True)
st.markdown("**喂入文献，点名提问，极客级物理推导。**")
st.markdown("---")

# --- 第一步：上传与解析 PDF ---
st.subheader("📁 Step 1: 载入物理文献/讲义 (PDF)")
uploaded_file = st.file_uploader("上传 PDF 文件", type=["pdf"], label_visibility="collapsed")

if uploaded_file is not None:
    if st.session_state.current_file_name != uploaded_file.name:
        with st.spinner("正在提取文献数据并向量化..."):
            pdf_reader = pypdf.PdfReader(uploaded_file)
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
            
            st.session_state.pdf_context = extracted_text
            st.session_state.current_file_name = uploaded_file.name
            st.session_state.result_text = None 
            
    st.success(f"✅ 物理文献加载成功！共计 {len(pypdf.PdfReader(uploaded_file).pages)} 页。")

# --- 第二步：人机交互与指令 ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("💬 Step 2: 设定解析目标")
user_command = st.text_input(
    "输入指令", 
    placeholder="例如：'推导第5页的量子谐振子能级' 或 '用拉格朗日力学解一下那道双摆问题'",
    label_visibility="collapsed"
)

# 按钮布局
col1, col2 = st.columns([3, 1])
with col1:
    analyze_btn = st.button("🚀 锁定目标并开始推导", type="primary", use_container_width=True)
with col2:
    if st.button("🗑️ 清空工作区", use_container_width=True):
        st.session_state.result_text = None
        st.rerun()

# ==========================================
# 6. 核心逻辑与 API 调用 (严格遵守 Wait-and-Load)
# ==========================================
if analyze_btn:
    if not api_key:
        st.error("⚠️ 物理学家，请先在左侧栏输入你的 API Key！")
    elif not st.session_state.pdf_context:
        st.warning("⚠️ 请先在上方载入 PDF 讲义！")
    elif not user_command.strip():
        st.warning("⚠️ 请输入明确的解析指令！")
    else:
        client = OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com/v1"
        )
        
        final_user_prompt = f"【PDF文献文本】\n{st.session_state.pdf_context}\n\n【用户的解析指令】\n{user_command}"
        
        with st.spinner("AI 正在构建物理图像并进行纯理论验算，请稍候..."):
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": final_user_prompt}
                    ],
                    temperature=0.1, # 极低温度：确保公式推导的数学确定性和严谨性
                    stream=False     # 坚守 Wait-and-Load 准则
                )
                
                raw_text = response.choices[0].message.content
                
                # 【终极防御】：强力替换掉所有不兼容的 LaTeX 括号
                processed_text = raw_text.replace(r"\(", "$").replace(r"\)", "$")
                processed_text = processed_text.replace(r"\[", "$$").replace(r"\]", "$$")
                
                st.session_state.result_text = processed_text
                
            except Exception as e:
                st.error(f"❌ 解析失败，量子态坍缩。错误信息: {e}")

# ==========================================
# 7. 结果展示区
# ==========================================
if st.session_state.result_text:
    st.success("✨ 验算完成，请查收你的理论推导报告。")
    st.subheader("3. 物理推导全景")
    
    with st.container(border=True):
        st.markdown(st.session_state.result_text)