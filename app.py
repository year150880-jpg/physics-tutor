import streamlit as st
from openai import OpenAI
import pypdf

# ==========================================
# 1. 页面基本配置
# ==========================================
st.set_page_config(
    page_title="AI Physics Tutor - Beta 3.0", 
    page_icon="📡", 
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
    st.markdown("为你独家定制的 **理论物理智能检索引擎**。")
    
    api_key = st.text_input("🔑 DeepSeek API Key:", type="password", help="在此输入你的 API Key")
    st.markdown("👉 [点击获取 DeepSeek API Key](https://platform.deepseek.com/)")
    
    st.divider()
    st.caption("当前版本: Beta 3.0 (知识检索版)")
    st.caption("引擎: DeepSeek-Chat")

# ==========================================
# 4. 核心 Prompt 模板 (双轨逻辑：命中 vs 未命中)
# ==========================================
SYSTEM_PROMPT = """你是一个顶尖的理论物理学者及物理辅导专家。
用户会提供一份【带页码标记的PDF提取文本】和一个【目标知识点】。

你的任务逻辑如下：
**第一步：全卷检索**
在提供的PDF文本中寻找与【目标知识点】高度相关的“例题”或“习题”。

**第二步：分情况输出（严格遵守以下格式）**

🟢 情况 A：如果找到了相关例题
请严格按以下格式输出（必须明确指出页码）：

### 🎯 目标锁定与出处
👉 **例题出处**：(明确指出在第几页，例如“发现于文献第 5 页”)
👉 **原题重述**：(简要提炼并复述原题干，使用 LaTeX 格式化里面的变量)

### 📌 物理图像与模型建构
👉 **核心物理本质**：(说明这道题考什么物理模型或定理)
👉 **物理假设与近似**：(列出隐性假设，如忽略次级辐射、刚体近似等)

### 🧠 动力学/热力学思路
👉 **参考系与坐标选择**：(说明参考系或广义坐标的最优化选择)
👉 **对称性与守恒律**：(指出系统具备的对称性及守恒量)

### 📐 支配方程与定解条件
- **核心方程**：(列出支配方程，如拉格朗日量、麦克斯韦方程组)
- **初始/边界条件**：(明确微积分求解过程中的定解条件)

### ✍️ 解析推导与严密解答
(给出从基本原理到最终结果的完整解析推导。每一步微积分变换需点明物理依据)

### 🧮 物理意义探讨 (量纲与极限分析)
👉 **量纲检验**：(验证最终结果表达式的量纲是否自洽)
👉 **渐近极限**：(探讨当某变量趋于0或无穷大时，该结果的物理退化情形)

---

🔴 情况 B：如果没有找到相关的例题
请不要强行生编硬造，严格按以下格式输出：

### 📭 检索结果
👉 经过对全文的扫描，未能在当前讲义中找到与“【目标知识点】”直接相关的完整例题。

### 📚 知识点硬核重构 (理论补偿梳理)
(既然讲义里没有，请直接调用你的内建知识库，对该知识点进行纯理论的系统梳理，教会学生)
👉 **核心物理图像**：(直击本质的概念解释)
👉 **基本支配方程**：(给出该知识点最核心的数学物理方程及推导思路)
👉 **适用边界与典型考法**：(这个知识点通常在考研或高阶物理考试中怎么设置陷阱)


【⚠️ 绝对排版指令 - 极其重要】
所有的数学公式必须使用 LaTeX 格式：行内公式用单美元符号 $...$，独立公式用双美元符号 $$...$$。绝对禁止使用 \\( \\) 或 \\[ \\]！
"""

# ==========================================
# 5. 主界面 UI 
# ==========================================
st.markdown("# 📡 AI Physics Tutor <span style='font-size: 20px; color: #2563eb; background: #e0e7ff; padding: 4px 8px; border-radius: 8px;'>beta 3.0</span>", unsafe_allow_html=True)
st.markdown("**输入知识点，系统全卷扫描找题，并进行极客级推演。**")
st.markdown("---")

# --- 第一步：上传与解析 PDF ---
st.subheader("📁 Step 1: 载入物理文献/讲义 (PDF)")
uploaded_file = st.file_uploader("上传 PDF 文件", type=["pdf"], label_visibility="collapsed")

if uploaded_file is not None:
    if st.session_state.current_file_name != uploaded_file.name:
        with st.spinner("正在提取文献数据并构建页码坐标系..."):
            pdf_reader = pypdf.PdfReader(uploaded_file)
            extracted_text = ""
            # 核心改进：为每一页打上页码标签，让 AI 知道具体位置
            for i, page in enumerate(pdf_reader.pages):
                extracted_text += f"\n\n=========== 第 {i+1} 页 ===========\n\n"
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
            
            st.session_state.pdf_context = extracted_text
            st.session_state.current_file_name = uploaded_file.name
            st.session_state.result_text = None 
            
    st.success(f"✅ 物理文献加载成功！共计 {len(pypdf.PdfReader(uploaded_file).pages)} 页已建立检索坐标。")

# --- 第二步：人机交互与指令 ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("💬 Step 2: 输入你想掌握的知识点")
knowledge_point = st.text_input(
    "输入知识点", 
    placeholder="例如：'中心力场与轨道方程' 或 '麦克斯韦关系式的推导'",
    label_visibility="collapsed"
)

# 按钮布局
col1, col2 = st.columns([3, 1])
with col1:
    analyze_btn = st.button("🚀 检索例题并开始推演", type="primary", use_container_width=True)
with col2:
    if st.button("🗑️ 清空工作区", use_container_width=True):
        st.session_state.result_text = None
        st.rerun()

# ==========================================
# 6. 核心逻辑与 API 调用 
# ==========================================
if analyze_btn:
    if not api_key:
        st.error("⚠️ 物理学家，请先在左侧栏输入你的 API Key！")
    elif not st.session_state.pdf_context:
        st.warning("⚠️ 请先在上方载入 PDF 讲义！")
    elif not knowledge_point.strip():
        st.warning("⚠️ 请输入明确的知识点名称！")
    else:
        client = OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com/v1"
        )
        
        final_user_prompt = f"【带页码的PDF提取文本】\n{st.session_state.pdf_context}\n\n【用户寻找的目标知识点】\n{knowledge_point}"
        
        with st.spinner(f"AI 正在全卷扫描【{knowledge_point}】相关例题并验算，请稍候..."):
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": final_user_prompt}
                    ],
                    temperature=0.1, 
                    stream=False     
                )
                
                raw_text = response.choices[0].message.content
                
                # LaTeX 格式强力清洗
                processed_text = raw_text.replace(r"\(", "$").replace(r"\)", "$")
                processed_text = processed_text.replace(r"\[", "$$").replace(r"\]", "$$")
                
                st.session_state.result_text = processed_text
                
            except Exception as e:
                st.error(f"❌ 检索或解析失败，量子态坍缩。错误信息: {e}")

# ==========================================
# 7. 结果展示区
# ==========================================
if st.session_state.result_text:
    st.success("✨ 运算完成，请查收你的理论推导报告。")
    st.subheader("3. 检索与推演全景")
    
    with st.container(border=True):
        st.markdown(st.session_state.result_text)