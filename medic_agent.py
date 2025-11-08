import os
from typing import Annotated, Optional, List, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.chat_models import ChatTongyi
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.prompts import PromptTemplate
from utility import show_graph, parse_pdf, parse_text, analyze_image, analyze_skin, web_search
from langchain.chains import LLMChain,GraphCypherQAChain

# 配置API密钥
from config import DASHSCOPE_API_KEY, TAVILY_API_KEY, password, neo4j_name, LANGSMITH_API_KEY, project
#
# os.environ["LANGSMITH_TRACING"] = "true"
# os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
# os.environ["LANGSMITH_PROJECT"] = project
# os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
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
print("Neo4j连接成功，图谱Schema：")
print(neo4j_graph.schema)

# 初始化通义千问模型
llm_max = ChatTongyi(
    model="qwen-max",
    top_p=0.9,
)
llm_fast = ChatTongyi(
    model="qwen-flash",
    top_p=0.9
)

# 定义状态
class State(TypedDict):
    messages: Annotated[list, add_messages] #对话历史
    user_question: Optional[str] = None #对话问题
    prompt: Optional[PromptTemplate] = None#长期提示词

    need_back: bool = False#ccb
    back_times: Optional[int] = 0#循环次数
    how_to_do: Optional[str] = None#需要在哪些方面优化

    has_file_path: Optional[bool] = False# 用户问题是否有包含路径
    file_path: Optional[str] = None #路径/可以改成List

    neo4j_answer: Optional[str] = None
    chat_answer: Optional[str] = None
    search_results: Optional[Dict] = None
    final_answer: Optional[str] = None

    user_info: Optional[str] = None#群体，年龄，往期情况
    has_user_info: bool = False

    use_search: bool = False#是否使用联网搜索，

# 创建工具节点
tools = [parse_pdf, analyze_image, parse_text, analyze_skin]
llm_with_tools = llm_max.bind_tools(tools)

tool_node = ToolNode(tools=tools)

#初始节点,扩展功能如人工介入，SQL放长期记忆在这里实现
def pre(state: State):
    user_question = state.get("user_question", "")
    user_info = state.get("user_info", "")
    prompt = f"""
    基于用户基本信息和问题，用简短的1-2个词描述用户类型（如老年人、学生；年龄；职业等），如果可以，包含能辅助诊断的额外信息。
    只需返回描述结果，无需额外内容。

    用户基本信息：{user_info}
    问题：{user_question}
    """

    # 调用LLM生成结果
    response = llm_fast.invoke(prompt)
    user_info= response.content.strip()
    suggestion=state.get("how_to_do", "")
    prompt=f"你是一名专业医生，服务于{user_info}的病人，请做出易懂的回答。参考建议{suggestion}"

    return {
        "messages": state["messages"],
        "user_info": user_info,
        "prompt": prompt
    }

#输出答案，更新数据库
def output(state: State):
    """
    等待添加代码
    """

    #更新用户的特征
    user_question=state["user_question"]
    user_info=state.get("user_info", "")
    answer=state["final_answer"]
    prompt = f"""
    请根据用户的个人信息、本次对话的问题和回答，更新用户的信息，帮助进一步诊断。
    要求：
    1. 保留原有关键信息（如年龄、基础疾病）
    2. 新增与本次健康咨询相关的特征（如症状、用药需求等）
    3. 用简洁的结构化语言描述（如：年龄：25，身份：学生，症状：咳嗽，疑似感冒）

    个人信息：{user_info}
    问题：{user_question}
    回答：{answer}
    """
    response = llm_fast.invoke(prompt).content.strip()
    return{"user_info": response}


def router(state: State):
    user_question = state["user_question"]
    prompt = f"""
    请判断以下问题中是否包含“文件路径”，并严格按照格式回答 True 或 False（仅返回这两个词，不添加任何其他内容）。
    “文件路径”指：
    - Windows 系统路径：如 D:/data/image.png（含盘符和斜杠）
    - Linux/macOS 系统路径：如 /home/user/photo.png、~/Documents/skin.jpg（含 / 或 ~）
    - 相对路径：如 ./image.png、../data/file.jpg（含 ./ 或 ../）
    只要包含上述格式的字符串，无论是否有效，均判断为存在路径。

    问题：{user_question}
    """
    response = llm_fast.invoke(prompt).content.strip()
    # 2. 容错处理：支持小写、带空格等情况
    has_path = response.lower() == "true"  # 忽略大小写，只要包含"true"就判定为存在
    return {"has_file_path": has_path}

def router_condition(state: State):
    """在这里修改模块的调用逻辑，实现联网搜索和知识图谱的调用选项"""
    has_file_path = state.get("has_file_path", False)
    if has_file_path == True:
        return "file"
    else :
        return "temp"

def temp(state: State):
    """规划搜索 图谱 回答的使用"""
    return{**state}

# 对话节点
def chatbot(state: State):
    messages = state["messages"]
    if "prompt" in state and state["prompt"]:
        messages = [{"role": "system", "content": state["prompt"]}] + messages

    response = llm_with_tools.invoke(messages)
    chat_answer = response.content if hasattr(response, "content") else str(response)
    return {
        "messages": response,
        "chat_answer": chat_answer,
    }
def chatbot_new(state: State):
    messages = state["messages"]
    if "prompt" in state and state["prompt"]:
        messages = [{"role": "system", "content": state["prompt"]}] + messages

    response = llm_with_tools.invoke(messages)
    chat_answer = response.content if hasattr(response, "content") else str(response)
    return {
        "messages": response,
        "final_answer": chat_answer,
    }

# 处理图查询
def Neo4j_query(state: State):
    user_question = state["user_question"]
    if not user_question:
        return {"messages": [{"role": "ai", "content": "未获取到有效的查询问题"}],
                "user_question": user_question}

    chain = GraphCypherQAChain.from_llm(
        graph=neo4j_graph,
        llm=llm_max,
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

        if not answer:
            answer = f"知识图谱未包含该信息"

    except Exception as e:
        answer = f"图谱查询失败"

    return {
        "messages": [{"role": "ai", "content": answer}],
        "neo4j_answer": answer,
        "user_question": user_question
    }


def web_search_node(state: State):
    user_question = state["user_question"]
    try:
        search_result = web_search(user_question)
        if "error" in search_result:
            messages_content = search_result["error"]
        else:
            # 搜索成功，格式化前3条结果
            results_summary = []
            for i, res in enumerate(search_result["results"][:3], 1):
                results_summary.append(f"{i}. {res['title']}\n   {res['content'][:100]}...\n   来源：{res['url']}")
            messages_content = f"网络搜索结果：\n" + "\n\n".join(results_summary)

        return {
            "messages": [{"role": "ai", "content": messages_content}],
            "search_results": search_result
        }

    except Exception as e:
        error_msg = f"搜索节点执行失败：{str(e)}"
        return {
            "messages": [{"role": "ai", "content": error_msg}],
            "search_results": {"error": error_msg}
        }

def sumup(state: State):
    neo4j_answer = state.get("neo4j_answer", "知识图谱暂未提供相关信息")
    chat_answer = state.get("chat_answer", "对话模型暂未提供相关信息")
    search_results = state.get("search_results", "")
    user_question = state["user_question"]

    if search_results != "网络查询失败" and "results" in search_results:
        search_summary = ""
        # 格式化原始搜索结果（提取标题、内容、来源，去除冗余字段）
        formatted_raw = "\n".join([
            f"【来源{idx + 1}】标题：{res['title']}\n内容：{res['content']}\n来源链接：{res['url']}"
            for idx, res in enumerate(search_results["results"][:3])  # 取前3条避免过长
        ])
        # 用LLM总结搜索结果
        summary_prompt = f"""
               任务：将以下关于“{user_question}”的医疗相关搜索结果，按“核心结论+关键建议”总结（仅保留医疗相关信息，去除无关内容）：
               要求：1. y语言有条理；2. 冲突信息标注来源；3. 语言简洁，无冗余。
               搜索结果：{formatted_raw}
               """
        try:
                search_summary = llm_max.invoke(summary_prompt).content.strip()
        except Exception as e:
                search_summary = f"搜索结果总结失败：{str(e)}（可参考原始信息：{[res['content'][:50] for res in search_results['results'][:2]]}）"
    else :
            search_summary = "无" # 搜索失败时的兜底信息

    prompt = f"""
    任务：综合以下三个信息，生成一个更全面、逻辑清晰的最终回复，服务于用户的医疗咨询需求。
    遵循规则：
    1. 保留回答1（知识图谱或网络搜寻）中的信息，如药物建议、饮食推荐、检查项目等；
    2. 用回答2（对话模型）的回答补充信息；
    3. 去除重复内容，若两个回答冲突，以回答1为准；
    4. 结尾可简要标注“信息来源：知识图谱+对话补充+网络搜索”，增强可信度；
    5. 语言风格保持医疗咨询的专业性和易懂性，避免冗余。

    用户问题：{user_question}
    回答1（知识图谱）：{neo4j_answer}
    回答2（对话模型）：{chat_answer}
    搜索结果 ：{search_summary}
    """
    try:
        response = llm_max.invoke(prompt).content.strip()
        # 校验响应有效性：为空则用原始回答拼接兜底
        if not response:
            final_answer = f"综合信息：\n1. 知识图谱提示：{neo4j_answer}\n2. 对话补充：{chat_answer}\n3.搜索：{search_summary[:100]}（注：自动综合失败，为您展示原始信息）"
        else:
            final_answer = response
    except Exception as e:
        # 捕获 LLM 调用异常，用原始回答兜底
        print(f"综合回答生成失败：{str(e)}")
        final_answer = f"综合信息：\n1. 知识图谱提示：{neo4j_answer}\n2. 对话补充：{chat_answer}\n3.搜索：{search_summary[:100]}（注：综合过程异常，为您展示原始信息）"

    return {
        "messages": [{"role": "ai", "content": final_answer}],  # 更新最终回复
        "final_answer": final_answer
    }


def feedback(state: State):
    user_question=state["user_question"]
    messages = state["messages"]
    times=state["back_times"]
    if not user_question:
        return {"need_back": False, "user_question": user_question}
    if not messages:
        return {"need_back": True, "user_question": user_question}  # 无回答时需要回溯

    last_message = messages[-1]
    answer = last_message.content if hasattr(last_message, "content") else str(last_message)
    prompt = f"""
    请判断以下回答是否充分回答了问题,并严格按照格式回答 True 或 False：
    - 若回答完整覆盖了问题的核心需求，且信息准确，仅回答 True，第二行不需要任何信息
    - 若回答遗漏关键信息、答非所问或信息错误，回答 False，在第二行给出修改建议
     回答:{answer}
     问题：{user_question}
     """
    response = llm_fast.invoke(prompt).content.strip()
    response_lines = [line.strip() for line in response.split("\n") if line.strip()]  # 过滤空行
    judge_result = response_lines[0]
    if judge_result.lower() == "false" and len(response_lines) > 1:
        feedback_suggestion = "\n".join(response_lines[1:])  # 拼接第二行及以后作为建议
        times=times+1
    else:
        feedback_suggestion = ""
        times=0

    need_back = judge_result.lower() != "true"
    return {
        "need_back": need_back,
        "user_question": user_question,
        "how_to_do": feedback_suggestion,
        "back_times": times
    }

def feedback_condition(state: State):
    times=state["back_times"]
    if times >3:
        return "output"
    if state["need_back"]==True:
        return "pre"
    elif state["need_back"]==False:
        return "output"


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
     response = llm_max.invoke(prompt).content.strip()
     #print(response)
     return {"is_graph_query": response == "True",}




# 创建图
graph = StateGraph(State)

# 添加所有节点
graph.add_node("pre",pre)
graph.add_node("router",router) #调度节点
graph.add_node("temp",temp) # 临时节点
graph.add_node("chatbot", chatbot)  # 对话节点
graph.add_node("chatbot_new",chatbot_new) #文件处理路径
graph.add_node("tools1", tool_node)  # 工具调用节点
graph.add_node("tools2", tool_node)
# graph.add_node("Neo4j_query", Neo4j_query ) #查询知识图谱
graph.add_node("search",web_search_node)  #搜索节点
graph.add_node("sumup",sumup)#结合节点
graph.add_node("feedback", feedback)#ccb
graph.add_node("output", output)#输出节点
# graph.add_node("judge_intent", judge_question_intent)  # 判断是否需要图查询

# 定义工作流
graph.add_edge(START, "pre")
graph.add_edge("pre","router")
graph.add_conditional_edges(
    "router",router_condition,
    {
        "temp":"temp",
        "file":"chatbot_new",
    }
)
graph.add_edge("temp","chatbot")
# graph.add_edge("temp","Neo4j_query")
graph.add_edge("temp","search")

graph.add_edge("tools1", "chatbot")
graph.add_conditional_edges(
    "chatbot",tools_condition,
    {
    "tools":"tools1",
    "__end__":"sumup",
    }
)
graph.add_edge("tools2", "chatbot_new")
graph.add_conditional_edges(
    "chatbot_new",tools_condition,
    {
    "tools":"tools2",
    "__end__":"feedback",
    }
)
graph.add_edge(["chatbot","search"],"sumup")
graph.add_edge("sumup","feedback")
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
#print(graph.nodes)
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

        else:
            initial_messages = [("user", f"{user_input}")]
            has_file_path = False

        # 构造初始状态
        initial_state = {
            "messages": initial_messages,
            "user_question": user_input,
            "user_info": user_info,  # 传入个人信息，供 pre 节点使用
            "has_user_info": True, # 标记已采集，下次运行不重复询问
            "back_times":0,
            "has_file_path": has_file_path
        }

        # 执行工作流
        final_state = None
        for event in app.stream(initial_state, config, stream_mode="values"):
            final_state = event

        # 展示结果
        if final_state and final_state.get("messages"):
            last_msg = final_state["messages"][-1]
            if last_msg.type == "ai":
                print(f"AI: {last_msg.content}")
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                tool_name = last_msg.tool_calls[0]["name"]
                print(f"（正在调用工具：{tool_name}）")

if __name__ == "__main__":
    chat_loop()
