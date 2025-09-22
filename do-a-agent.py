from langchain_community.chat_models import ChatTongyi
import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
import pypdf
from PIL import Image
import pytesseract
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langchain_tavily import TavilySearch

# 配置API密钥
os.environ["DASHSCOPE_API_KEY"] = "sk-817d27e9c883406a87d98eb23fc4b1a9"
os.environ["TAVILY_API_KEY"] = "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"

# 初始化通义千问模型
llm = ChatTongyi(
    model="qwen-max",
    top_p=0.9
)


# 定义状态
class State(TypedDict):
    messages: Annotated[list, add_messages]


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
        text = pytesseract.image_to_string(img,lang='chi_sim+eng')
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
tools = [parse_pdf, parse_image, parse_text,search_tool]
# 绑定工具到LLM
llm_with_tools = llm.bind_tools(tools)

# 创建工具节点
tool_node = ToolNode(tools=tools)


# 对话节点
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# 创建图
graph = StateGraph(State)

# 添加节点
graph.add_node("chatbot", chatbot)
graph.add_node("tools", tool_node)

# 定义边和条件
graph.add_edge(START, "chatbot")
graph.add_conditional_edges(
    "chatbot",
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


def chat_loop():
    print("欢迎使用！输入 'exit' 退出")
    thread_id = "thread-1"  # 用于记忆的线程ID
    while True:
        user_input = input("您: ")
        if user_input.lower() == 'exit':
            print("再见！")
            break

        # 检查用户输入是否为文件路径
        if os.path.exists(user_input):
            file_extension = os.path.splitext(user_input)[1].lower()
            if file_extension == '.pdf':
                print("正在解析PDF文件，请稍等...")
                messages = [("user", user_input), ("function", {"name": "parse_pdf", "arguments": {"file_path": user_input}})]
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
                print("正在解析图片文件，请稍等...")
                messages = [("user", user_input), ("function", {"name": "parse_image", "arguments": {"file_path": user_input}})]
            elif file_extension == '.txt':
                print("正在解析文本文件，请稍等...")
                messages = [("user", user_input), ("function", {"name": "parse_text", "arguments": {"file_path": user_input}})]
            else:
                print("不支持的文件类型")
                continue
        else:
            messages = [("user", user_input)]

        # 运行工作流
        config = {"configurable": {"thread_id": thread_id}}
        for event in app.stream({"messages": messages}, config, stream_mode="values"):
            # 获取最新消息
            messages = event["messages"]
            if messages:
                last_message = messages[-1]
                if last_message.type == "ai":
                    print(f"AI: {last_message.content}")
                elif last_message.type == "function_result":
                    print(f"工具调用结果: {last_message.content}")
                # 显示工具调用信息
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    print(f"正在调用工具: {last_message.tool_calls[0]['name']}")


if __name__ == "__main__":

    chat_loop()
