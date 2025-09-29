import os
import pypdf
import pytesseract
from typing import Annotated, Optional, List, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langchain_community.chat_models import ChatTongyi
from PIL import Image
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langchain_tavily import TavilySearch
from langchain.prompts import PromptTemplate
from utility import show_graph
import dashscope
from langchain.chains import LLMChain,GraphCypherQAChain
# 配置API密钥
from config import DASHSCOPE_API_KEY, TAVILY_API_KEY, password, neo4j_name, LANGSMITH_API_KEY, project

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_PROJECT"] = project
os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
os.environ["DASHSCOPE_API_KEY"] = DASHSCOPE_API_KEY
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY


# 配置知识图谱
from langchain_community.graphs import Neo4jGraph
neo4j_graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username=neo4j_name,
    password=password
)
# 刷新图谱模式
neo4j_graph.refresh_schema()
# print("Neo4j连接成功，图谱Schema：")
# print(neo4j_graph.schema)

# 初始化通义千问模型
llm = ChatTongyi(
    model="qwen-max",
    top_p=0.9
)

# 定义状态 - 扩展以支持知识图谱查询
class State(TypedDict):
    messages: Annotated[list, add_messages] #对话历史
    is_graph_query: Optional[bool] = None # 辅助标识：是否为图查询需求（True/False）
    user_question: Optional[str] = None #对话问题(如果总是选择对话历史的最后一个当作用户问题，在工作流中原始问题会被ai对话覆盖
    user_class: Optional[str] = None #目标群体


# 定义工具
@tool
def parse_pdf(file_path: str) -> str:
    """解析PDF文件并返回文本内容。当用户提到需要处理PDF文件时使用。"""
    try:
        if not os.path.exists(file_path):
            return f"错误：文件不存在 - {file_path}"

        pdf_reader = pypdf.PdfReader(file_path)
        content = []
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text() or ""
            content.append(f"第{page_num}页:\n{text}")

        return "\n\n".join(content)
    except Exception as e:
        return f"解析PDF失败: {str(e)}"


@tool
# def parse_image(file_path: str) -> str:
#     """解析图片文件并通过OCR提取文本内容。当用户提到需要处理图片时使用。"""
#     try:
#         if not os.path.exists(file_path):
#             return f"错误：文件不存在 - {file_path}"
#
#         img = Image.open(file_path)
#         text = pytesseract.image_to_string(img, lang='chi_sim+eng')
#         return f"图片中的文本内容:\n{text}" if text else "图片中未识别到文本内容"
#     except Exception as e:
#         return f"解析图片失败: {str(e)}"


@tool
def parse_text(file_path: str) -> str:
    """解析文本文件并返回内容。当用户提到需要处理文本文件时使用。"""
    try:
        if not os.path.exists(file_path):
            return f"错误：文件不存在 - {file_path}"

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"文本文件内容:\n{content}"
    except UnicodeDecodeError:
        return "错误：无法解析非UTF-8编码的文本文件"
    except Exception as e:
        return f"解析文本文件失败: {str(e)}"

@tool
def analyze_image(file_path: str) -> str:
    """理解图片内容，实现多模态"""
    try:
        messages = [
            {
                "role": "system",
                "content": [
                    {"text": "You are a professional medical expert. "
                             "Based on the pictures, describe the symptoms,recommend medications and hospital departments,suggest foods to eat, and advise against certain foods."}]
            },
            {
                "role": "user",
                "content": [
                    {"image": file_path},
                    {"text": "请分析这张图片"}]
            }]
        response = dashscope.MultiModalConversation.call(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            model='qwen-vl-max-latest',
            messages=messages
        )
        return response.output.choices[0].message.content[0]["text"]
    except Exception as e:
        return f"解析图片失败: {str(e)}"

search_tool = TavilySearch(max_results=3)
# 工具列表
tools = [parse_pdf, analyze_image, parse_text, search_tool]
# 绑定工具到LLM
llm_with_tools = llm.bind_tools(tools)

# 创建工具节点
tool_node = ToolNode(tools=tools)


# 对话节点 - 初始处理用户问题
def chatbot(state: State):
    # 保存用户问题
    user_question = state["user_question"]
    return {
        "messages": [llm_with_tools.invoke(state["messages"])],
        "user_question": user_question
    }

#处理图查询
def Neo4j_query(state: State):
    user_question = state["user_question"]
    if not user_question:
        return {"messages": [{"role": "ai", "content": "未获取到有效的查询问题"}],
                "user_question": user_question}

    chain = GraphCypherQAChain.from_llm(
        graph=neo4j_graph,
        llm=llm,
        verbose=True,
        allow_dangerous_requests=True,
    )

    try:
        # 调用链查询知识图谱
        response = chain.invoke({"query": user_question})
        answer = response["result"]

        # # 调试：打印生成的Cypher语句
        # if "intermediate_steps" in response:
        #     cypher = response["intermediate_steps"][0]["query"]
        #     print(f"生成的Cypher语句：{cypher}")
        #
        #     # 检查查询结果是否为空（如果知识图谱中没有匹配数据）
        #     if not response.get("intermediate_steps", [{}])[0].get("result", []):
        #         answer = f"知识图谱中未找到相关信息。问题：{user_question}"

    except Exception as e:
        answer = f"图谱查询失败：{str(e)}"

    return {
        "messages": [{"role": "ai", "content": answer}],
        "user_question": user_question
    }


# 判断是否需要图查询的节点
def judge_question_intent(state: State) -> Dict:
    """判断用户问题是否需要查询知识图谱"""
    user_question=state["user_question"]
    if not user_question:
        return {"is_graph_query": False,"user_question":user_question}

    prompt = f"""
    请判断以下问题是否需要查询医疗领域知识图谱（仅回答 True 或 False）：
    知识图谱包含节点类型：检查(Check)、科室(Department)、疾病(Disease)、药品(Drug)、食物(Food)、厂商(Producer)、症状(Symptom)。
    关系类型包括：伴随(acompany_with)、属于(belongs_to)、常用药(common_drug)、宜吃(do_eat)、药品所属(drugs_of)、有症状(has_symptom)、需要检查(need_check)、忌吃(no_eat)、推荐药(recommand_drug)、推荐吃(recommand_eat)。
    属性包括：病因(cause)、治疗科室(cure_department)、治疗时长(cure_lasttime)、治疗方式(cure_way)、治愈概率(cured_prob)、描述(desc)、易患人群(easy_get)、名称(name)、预防措施(prevent)。
    问题：{user_question}
    """
    response = llm.invoke(prompt).content.strip()
    #print(response)
    return {"is_graph_query": response == "True",
            "user_question": user_question}

# 处理非图查询需求的节点
def handle_non_graph_query(state: State) -> Dict:
    """继续原有的工具调用流程处理非图查询需求"""
    return {"messages": state["messages"],
            "user_question": state["user_question"]}


# 创建图
graph = StateGraph(State)

# 添加所有节点
graph.add_node("chatbot", chatbot)  # 初始对话节点
graph.add_node("tools", tool_node)  # 工具调用节点
graph.add_node("judge_intent", judge_question_intent)  # 判断是否需要图查询
graph.add_node("Neo4j_query", Neo4j_query ) #查询知识图谱
graph.add_node("handle_non_graph", handle_non_graph_query)  # 处理非图查询

# 定义工作流
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", "judge_intent")

# 根据意图判断结果分流
graph.add_conditional_edges(
    "judge_intent",
    # 条件判断函数：是否为图查询
    lambda state: "graph" if state["is_graph_query"] else "non_graph",
    {
        "graph": "Neo4j_query",  # 是图查询
        "non_graph": "handle_non_graph"  # 非图查询，继续工具调用流程
    }
)

# 非图查询流程（原有工具调用流程）
graph.add_conditional_edges(
    "handle_non_graph",
    tools_condition,
    {
        "tools": "tools",  # 需要调用工具时流向工具节点
        END: END  # 不需要调用工具时结束
    }
)
graph.add_edge("tools", "chatbot")  # 工具调用后返回对话节点
# 添加记忆功能
memory = InMemorySaver()

app = graph.compile(checkpointer=memory)
#打印图形结构
#show_graph(app)

def chat_loop():
    print("欢迎使用！输入 'exit' 退出")
    thread_id = "thread-1"  # 用于记忆的线程ID，可扩展多对话场景

    while True:
        user_input = input("User: ")
        # 退出逻辑
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        # -------------------------- 统一消息变量：修复分支覆盖问题 --------------------------
        # 初始化当前轮次的初始消息（统一用 initial_messages，避免 messages/initial_messages 混用）
        initial_messages = None

        # 1. 处理文件路径输入场景
        if os.path.exists(user_input):
            file_extension = os.path.splitext(user_input)[1].lower()
            if file_extension == '.pdf':
                print("正在解析PDF文件，请稍等...")
                initial_messages = [
                    ("user", f"请解析此PDF文件：{user_input}"),  # 明确用户意图
                    ("function", {"name": "parse_pdf", "arguments": {"file_path": user_input}})
                ]
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
                print("正在解析图片文件，请稍等...")
                initial_messages = [
                    ("user", f"请解析此图片文件中的文本：{user_input}"),
                    ("function", {"name": "analyze_image", "arguments": {"file_path": user_input}})
                ]
            elif file_extension == '.txt':
                print("正在解析文本文件，请稍等...")
                initial_messages = [
                    ("user", f"请读取此文本文件内容：{user_input}"),
                    ("function", {"name": "parse_text", "arguments": {"file_path": user_input}})
                ]
            else:
                print("不支持的文件类型")
                continue  # 跳过后续流程，等待下一次有效输入

        # 2. 处理纯文本输入场景（非文件路径）
        else:
            # 构造纯文本用户消息（统一用列表格式，与文件场景对齐）
            initial_messages = [("user", user_input)]

        # -------------------------- 运行工作流：传递完整初始状态 --------------------------
        # 配置线程ID（确保记忆功能生效，多轮对话共享上下文）
        config = {"configurable": {"thread_id": thread_id}}

        # 构造初始状态：包含「当前轮次消息」和「原始用户问题」（对齐 State 定义）
        initial_state = {
            "messages": initial_messages,  # 传递当前轮次的初始消息（纯文本/文件指令）
            "user_question": user_input  # 稳定存储原始输入，供后续节点使用
        }

        # 执行工作流，收集最终状态（跳过中间节点快照，避免重复输出）
        final_state = None
        for event in app.stream(initial_state, config, stream_mode="values"):
            final_state = event  # 持续更新为最新状态，最终获取结束节点结果

        if final_state and final_state.get("messages"):
            last_msg = final_state["messages"][-1]  # 获取最后一条消息（最新结果）

            # 展示AI回复
            if last_msg.type == "ai":
                print(f"AI: {last_msg.content}")

            # 展示工具调用结果（如PDF解析内容、图片OCR文本）
            elif last_msg.type == "function_result":
                print(f"工具调用结果:\n{last_msg.content}")

            # 展示工具调用过程（仅调试用，可选保留）
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                tool_name = last_msg.tool_calls[0]["name"]
                print(f"正在调用工具: {tool_name}")

if __name__ == "__main__":
    chat_loop()
