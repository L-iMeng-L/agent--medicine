import os
import pytesseract
from typing import Annotated, Optional, List, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.chat_models import ChatTongyi
from PIL import Image
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langchain_tavily import TavilySearch
from langchain.prompts import PromptTemplate
from utility import show_graph,parse_pdf,parse_text,analyze_image
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

# 定义状态
class State(TypedDict):
    messages: Annotated[list, add_messages] #对话历史
    user_question: Optional[str] = None #对话问题
    user_type: Optional[str] = None #目标群体
    prompt: Optional[PromptTemplate] = None#长期提示词
    need_back: bool = False#ccb
    neo4j_answer: Optional[str] = None
    chat_answer: Optional[str] = None

    user_info: Optional[str] = None
    has_user_info: bool = False

# 创建工具节点
search_tool = TavilySearch(max_results=3)
tools = [parse_pdf, analyze_image, parse_text, search_tool]
llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools=tools)

#初始节点,扩展功能如人工介入，SQL放长期记忆在这里实现
def temp(state: State):
    user_info = state.get("user_info", "")
    conversation_history = state.get("messages", [])

    prompt = f"""
    基于用户基本信息和对话历史，用简短的1-2个词描述用户类型（如：老年人、成年人、学生、儿童等），如果可以，包含能辅助诊断的额外信息。
    只需返回描述结果，无需额外内容。

    用户问题：{user_info}
    对话历史：{conversation_history}
    """

    # 调用LLM生成结果
    response = llm.invoke(prompt)
    user_type = response.content.strip()
    prompt=f"你是一名专业医生，服务于{user_type}的病人，请做出易懂的回答"

    return {
        "messages": state["messages"],
        "user_type": user_type,
        "prompt": prompt
    }

# 对话节点
def chatbot(state: State):
    # 保存用户问题
    user_question = state["user_question"]
    messages = state["messages"]
    if "prompt" in state and state["prompt"]:
        messages = [{"role": "system", "content": state["prompt"]}] + messages

    response = llm_with_tools.invoke(messages)
    chat_answer = response.content if hasattr(response, "content") else str(response)
    return {
        "messages": response,
        "chat_answer": chat_answer,
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
        "neo4j_answer": answer,
        "user_question": user_question
    }
def compare(state: State):
    neo4j_answer = state["neo4j_answer"]
    chat_answer = state["chat_answer"]
    user_question = state["user_question"]
    prompt = f"""
    请判断回答1和回答2哪个更好，仅回答1或者2，不要添加任何额外内容。
     问题:{user_question}
     回答1:{neo4j_answer}
     回答2：{chat_answer}
     """
    response = llm.invoke(prompt).content.strip()
    if response=="1":
        return {
            "messages": [{"role": "ai", "content": neo4j_answer}],
        }
    elif response=="2":
        return {
            "messages": [{"role": "ai", "content":chat_answer}],
        }


def feedback(state: State):
    """判断用户问题是否需要查询知识图谱"""
    user_question=state["user_question"]
    messages = state["messages"]
    if not user_question:
        return {"need_back": False, "user_question": user_question}
    if not messages:
        return {"need_back": True, "user_question": user_question}  # 无回答时需要回溯

    last_message = messages[-1]
    answer = last_message.content if hasattr(last_message, "content") else str(last_message)
    prompt = f"""
    请判断以下回答是否充分回答了问题（仅回答 True 或 False）：
    - 若回答完整覆盖了问题的核心需求，且信息准确，回答 True
    - 若回答遗漏关键信息、答非所问或信息错误，回答 False
     回答:{answer}
     问题：{user_question}
     """
    response = llm.invoke(prompt).content.strip()
    return {"need_back": response == "True",}

#输出答案，更新数据库
def output(state: State):
    """
    等待添加代码
    """
    return{**state}


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
     return {"is_graph_query": response == "True",}

def feedback_condition(state: State):
    if state["need_back"]==True:
        return "pre"
    elif state["need_back"]==False:
        return "output"
# 创建图
graph = StateGraph(State)

# 添加所有节点
graph.add_node("pre",temp)
graph.add_node("chatbot", chatbot)  # 初始对话节点
graph.add_node("tools", tool_node)  # 工具调用节点
graph.add_node("Neo4j_query", Neo4j_query ) #查询知识图谱
graph.add_node("cmp",compare)#比较节点
graph.add_node("feedback", feedback)#ccb
graph.add_node("output", output)#输出节点
# graph.add_node("judge_intent", judge_question_intent)  # 判断是否需要图查询

# 定义工作流
graph.add_edge(START, "pre")
graph.add_edge("tools", "chatbot")
graph.add_edge("pre", "chatbot")
graph.add_conditional_edges("chatbot",tools_condition,)
graph.add_edge("tools","chatbot")
graph.add_edge("pre", "Neo4j_query")
graph.add_edge(["Neo4j_query","chatbot"],"cmp")
graph.add_edge("cmp","feedback")
graph.add_conditional_edges(
    "feedback",feedback_condition,
    {
        "pre": "pre",
        "output": "output"
    }
)
graph.add_edge("output",END)
# 添加记忆功能
memory = InMemorySaver()
app = graph.compile(checkpointer=memory)

#打印图形结构
#show_graph(app)

def chat_loop():
    print("欢迎使用医疗咨询助手！首先请完善一些个人信息，帮助我更精准地为您服务～")
    thread_id = "thread-1"
    config = {"configurable": {"thread_id": thread_id}}

    # -------------------------- 新增：初始个人信息采集（仅首次运行） --------------------------
    # 检查是否已采集过信息（通过记忆获取历史状态，避免重复询问）
    try:
        # 尝试获取历史状态，判断是否已有个人信息
        history_state = app.get_state(config)
        has_user_info = history_state.get("user_info", False)
    except:
        # 无历史状态（首次运行），标记为未采集
        has_user_info = False

    user_info = ""
    if not has_user_info:
        # 采集关键个人信息（可根据需求调整字段）
        print("\n请回答以下简单问题（仅用于精准服务，不会泄露）：")
        age = input("1. 您的年龄（如：25、60）：")
        identity = input("2. 您的身份（如：学生、上班族、退休人员）：")
        health_note = input("3. 是否有基础疾病或特殊健康情况（无则填“无”）：")

        # 整理为结构化信息字符串
        user_info = f"年龄：{age}，身份：{identity}，健康情况：{health_note}"
        print(f"\n感谢配合！您的信息已记录：{user_info}\n")

    # -------------------------- 对话循环逻辑 --------------------------
    print("现在可以开始咨询了，输入 'exit' 退出")
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        # 1. 统一初始化消息（整合个人信息+用户问题）
        initial_messages = None
        # 处理文件路径输入
        if os.path.exists(user_input):
            file_extension = os.path.splitext(user_input)[1].lower()
            if file_extension == '.pdf':
                initial_messages = [
                    ("user", f"我的个人信息：{user_info}。请解析此PDF文件并结合我的信息回答：{user_input}"),
                    ("function", {"name": "parse_pdf", "arguments": {"file_path": user_input}})
                ]
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
                initial_messages = [
                    ("user", f"我的个人信息：{user_info}。请解析此图片文本并结合我的信息回答：{user_input}"),
                    ("function", {"name": "analyze_image", "arguments": {"file_path": user_input}})
                ]
            elif file_extension == '.txt':
                initial_messages = [
                    ("user", f"我的个人信息：{user_info}。请读取此文本并结合我的信息回答：{user_input}"),
                    ("function", {"name": "parse_text", "arguments": {"file_path": user_input}})
                ]
            else:
                print("不支持的文件类型")
                continue
        # 处理纯文本输入
        else:
            initial_messages = [("user", f"我的个人信息：{user_info}。我的问题是：{user_input}")]

        # 2. 构造初始状态
        initial_state = {
            "messages": initial_messages,
            "user_question": user_input,
            "user_info": user_info,  # 传入个人信息，供 pre 节点使用
            "has_user_info": True  # 标记已采集，下次运行不重复询问
        }

        # 3. 执行工作流
        final_state = None
        for event in app.stream(initial_state, config, stream_mode="values"):
            final_state = event

        # 4. 展示结果
        if final_state and final_state.get("messages"):
            last_msg = final_state["messages"][-1]
            if last_msg.type == "ai":
                print(f"AI: {last_msg.content}")
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                tool_name = last_msg.tool_calls[0]["name"]
                print(f"（正在调用工具：{tool_name}）")

if __name__ == "__main__":
    chat_loop()
