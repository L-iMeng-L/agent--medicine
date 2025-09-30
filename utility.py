def show_graph(app):
    try:
        mermaid_code = app.get_graph(xray=True).draw_mermaid()
        print("=== LangGraph 工作流 ===")
        print(mermaid_code)
        print("\n复制以上代码到在线编辑器生成图片：https://mermaid.live/")
    except Exception as e:
        print("生成 Mermaid 语法失败:", e)

from langchain_core.tools import tool
import pypdf,os
import dashscope
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
