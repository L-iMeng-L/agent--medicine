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
    #对话历史
    messages: Annotated[list, add_messages]
    # 辅助标识：是否为图查询需求（True/False）
    is_graph_query: Optional[bool] = None


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
def parse_image(file_path: str) -> str:
    """解析图片文件并通过OCR提取文本内容。当用户提到需要处理图片时使用。"""
    try:
        if not os.path.exists(file_path):
            return f"错误：文件不存在 - {file_path}"

        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        return f"图片中的文本内容:\n{text}" if text else "图片中未识别到文本内容"
    except Exception as e:
        return f"解析图片失败: {str(e)}"


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


search_tool = TavilySearch(max_results=2)
# 工具列表
tools = [parse_pdf, parse_image, parse_text, search_tool]
# 绑定工具到LLM
llm_with_tools = llm.bind_tools(tools)

# 创建工具节点
tool_node = ToolNode(tools=tools)


# 对话节点 - 初始处理用户问题
def chatbot(state: State):
    # 保存用户问题
    user_question = state["messages"][-1].content if state["messages"] else ""
    return {
        "messages": [llm_with_tools.invoke(state["messages"])],
        "user_question": user_question
    }


# 判断是否需要图查询的节点
def judge_question_intent(state: State) -> Dict:
    """判断用户问题是否需要查询知识图谱"""
    user_question=state["messages"][-1].content if state["messages"] else ""
    if not user_question:
        return {"is_graph_query": False}

    prompt = f"""
    请判断以下问题是否需要查询医疗领域知识图谱（仅回答 True 或 False）：
    知识图谱包含节点类型：检查(Check)、科室(Department)、疾病(Disease)、药品(Drug)、食物(Food)、厂商(Producer)、症状(Symptom)。
    关系类型包括：伴随(acompany_with)、属于(belongs_to)、常用药(common_drug)、宜吃(do_eat)、药品所属(drugs_of)、有症状(has_symptom)、需要检查(need_check)、忌吃(no_eat)、推荐药(recommand_drug)、推荐吃(recommand_eat)。
    属性包括：病因(cause)、治疗科室(cure_department)、治疗时长(cure_lasttime)、治疗方式(cure_way)、治愈概率(cured_prob)、描述(desc)、易患人群(easy_get)、名称(name)、预防措施(prevent)。
    问题：{user_question}
    """
    response = llm.invoke(prompt).content.strip()
    #print(response)
    return {"is_graph_query": response == "True"}

#处理图查询
def Neo4j_query(state: State):
    # 1. 提取用户问题（从最新消息中获取）
    user_question = state["messages"][-1].content if state["messages"] else ""
    if not user_question:
        return {"messages": [{"role": "ai", "content": "未获取到有效的查询问题"}], "user_question": ""}

    # 2. 初始化图谱问答链
    chain = GraphCypherQAChain.from_llm(
        graph=neo4j_graph,
        llm=llm,
        verbose=True,
        allow_dangerous_requests=True,
    )

    # 3. 执行查询
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


# 处理非图查询需求的节点
def handle_non_graph_query(state: State) -> Dict:
    """继续原有的工具调用流程处理非图查询需求"""
    return {"messages": state["messages"]}


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
    thread_id = "thread-1"  # 用于记忆的线程ID
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        # 检查用户输入是否为文件路径
        if os.path.exists(user_input):
            file_extension = os.path.splitext(user_input)[1].lower()
            if file_extension == '.pdf':
                print("正在解析PDF文件，请稍等...")
                messages = [("user", user_input),
                            ("function", {"name": "parse_pdf", "arguments": {"file_path": user_input}})]
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
                print("正在解析图片文件，请稍等...")
                messages = [("user", user_input),
                            ("function", {"name": "parse_image", "arguments": {"file_path": user_input}})]
            elif file_extension == '.txt':
                print("正在解析文本文件，请稍等...")
                messages = [("user", user_input),
                            ("function", {"name": "parse_text", "arguments": {"file_path": user_input}})]
            else:
                print("不支持的文件类型")
                continue
        else:
            messages = [("user", user_input)]

        # 运行工作流
        config = {"configurable": {"thread_id": thread_id}}
        # 收集最终状态（跳过中间节点的快照）
        final_state = None
        for event in app.stream({"messages": messages}, config, stream_mode="values"):
            final_state = event  # 不断更新为最新状态，最终得到结束节点的状态

        # 从最终状态中提取并打印结果
        if final_state:
            last_msg = final_state["messages"][-1] if final_state["messages"] else None
            if last_msg:
                if last_msg.type == "ai":
                    print(f"AI: {last_msg.content}")
                elif last_msg.type == "function_result":
                    print(f"工具调用结果: {last_msg.content}")
                # 工具调用信息（仅在有调用时打印）
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    print(f"正在调用工具: {last_msg.tool_calls[0]['name']}")


if __name__ == "__main__":
    chat_loop()
