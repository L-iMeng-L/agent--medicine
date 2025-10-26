import os
from typing import Annotated, Optional, List, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_community.chat_models import ChatTongyi
from langchain.chains import LLMChain,GraphCypherQAChain
# 配置API密钥
from config import DASHSCOPE_API_KEY,LANGSMITH_API_KEY, project

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_PROJECT"] = project
os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
os.environ["DASHSCOPE_API_KEY"] = DASHSCOPE_API_KEY

llm_max = ChatTongyi(
    model="qwen-max",
    top_p=0.9,
)

class State(TypedDict):
    need_back: bool = False#ccb
    back_times: Optional[int] = 0#循环次数
    how_to_do: Optional[str] = None#需要在哪些方面优化

    chat_answer: Optional[str] = None

    user_info: Optional[str] = None#群体，年龄，往期情况

def generate(state:State):
    user_info= state["user_info"]
    suggestions = state["how_to_do"]or "无特殊建议，按标准格式生成报告即可"
    prompt = f"""
    请扮演专业皮肤科健康顾问，基于以下用户完整健康数据并参考建议，生成一份结构化健康报告。
    报告需包含核心症状分析、疑似诊断解读、针对性健康建议三个模块，语言需专业且易懂。
    用户健康数据：{user_info}
    建议： {suggestions}
    """
    response = llm_max.invoke(prompt).content.strip()

    return  {
        "chat_answer": response,
    }


def feedback(state: State):
    times=state["back_times"]
    response=state["chat_answer"]
    user_info=state["user_info"]
    if not response:
        return {"need_back": True, "how_to_do": "", "back_times": 0}

    prompt = f"""
    请判断生成的报告是否合格,并严格按照格式回答 True 或 False：
    - 若报告合格，且信息准确，仅回答 True，第二行不需要任何信息
    - 若报告不合格，回答 False，在第二行给出修改建议
     报告:{response}
     信息：{user_info}
     """
    response = llm_max.invoke(prompt).content.strip()
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
        "how_to_do": feedback_suggestion,
        "back_times": times
    }

def feedback_condition(state: State):
    times=state["back_times"]
    if times >3:
        return "output"
    if state["need_back"]==True:
        return "generate"
    elif state["need_back"]==False:
        return "output"

def output(state: State):
    """上传报告至SQL在这"""
    return{**state}

graph = StateGraph(State)

graph.add_node("generate",generate)
graph.add_node("feedback",feedback)
graph.add_node("output",output)
graph.add_edge(START,"generate")
graph.add_edge("generate","feedback")
graph.add_conditional_edges("feedback",feedback_condition,
{
    "generate":"generate",
    "output":"output",
}
)


graph.add_edge("output",END)
app = graph.compile()

if __name__ == "__main__":
    thread_id = "thread-1"
    config = {"configurable": {"thread_id": thread_id}}
    user_input = input("\nUser: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")

    else:
        initial_messages = [("user", f"{user_input}")]

    user_info= user_input
    initial_state = {
        "user_info": user_info,
        "back_times": 0,
        "how_to_do": "",
    }

    final_state = None
    for event in app.stream(initial_state, config, stream_mode="values"):
        final_state = event

    # 展示结果
    if final_state:
        last_msg = final_state.get("chat_answer","未生成有效报告")
        if last_msg.type == "ai":
            print(f"AI: {last_msg}")
