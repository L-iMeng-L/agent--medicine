from langchain_core.tools import tool
import pypdf,os
import dashscope
import base64
import requests
from config import skin_key, skin_secret
import decimal

def show_graph(app):
    try:
        mermaid_code = app.get_graph(xray=True).draw_mermaid()
        print("=== LangGraph 工作流 ===")
        print(mermaid_code)
        print("\n复制以上代码到在线编辑器生成图片：https://mermaid.live/")
    except Exception as e:
        print("生成 Mermaid 语法失败:", e)

def parse_health_record(health_data: dict) -> str:
    """
    格式化UserHealthRecord对应的健康数据为结构化文本
    :param health_data: 从JSON解析的健康数据字典（对应UserHealthRecord）
    :return: 分组整理后的健康信息文本
    """
    if not health_data:
        return "无健康档案信息"

    # 辅助函数：处理空值和数值格式
    def get_value(key: str, unit: str = "") -> str:
        value = health_data.get(key)
        # 处理空值（null或空字符串）
        if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
            return f"未记录{unit}"
        # 处理数值型（保留原始格式，补充单位）
        if isinstance(value, (int, float, decimal.Decimal)):
            return f"{value}{unit}"
        # 字符串类型直接返回
        return f"{value}{unit}"

    # 1. 基本身体数据
    basic_data = [
        f"身高：{get_value('height_cm', '厘米')}",
        f"体重：{get_value('weight_kg', '公斤')}",
        f"BMI：{get_value('bmi')}",
        f"血型：{get_value('blood_type')}"
    ]

    # 2. 生理指标
    physiological = [
        f"收缩压：{get_value('blood_pressure_systolic', 'mmHg')}",
        f"舒张压：{get_value('blood_pressure_diastolic', 'mmHg')}",
        f"心率：{get_value('heart_rate', '次/分钟')}",
        f"体温：{get_value('body_temperature', '℃')}"
    ]

    # 3. 血液指标
    blood_indicators = [
        f"血糖：{get_value('blood_sugar', 'mmol/L')}",
        f"总胆固醇：{get_value('cholesterol_total', 'mmol/L')}",
        f"低密度胆固醇：{get_value('cholesterol_ldl', 'mmol/L')}",
        f"高密度胆固醇：{get_value('cholesterol_hdl', 'mmol/L')}",
        f"甘油三酯：{get_value('triglycerides', 'mmol/L')}"
    ]

    # 4. 视力
    vision = [
        f"左眼视力：{get_value('vision_left')}",
        f"右眼视力：{get_value('vision_right')}"
    ]

    # 5. 病史
    medical_history = [
        f"过敏史：{get_value('allergies') if get_value('allergies') != '未记录' else '无'}",
        f"慢性病史：{get_value('chronic_diseases') if get_value('chronic_diseases') != '未记录' else '无'}",
        f"既往病史：{get_value('medical_history') if get_value('medical_history') != '未记录' else '无'}"
    ]

    # 6. 生活习惯
    lifestyle = [
        f"吸烟状况：{get_value('smoking_status')}",
        f"饮酒状况：{get_value('drinking_status')}",
        f"锻炼频率：{get_value('exercise_frequency')}",
        f"平均睡眠时长：{get_value('sleep_hours', '小时')}"
    ]

    # 7. 记录信息
    record_info = [
        f"健康记录日期：{get_value('date')}"
    ]

    # 按类别拼接，用空行分隔不同组
    all_sections = [
        ("基本身体数据", basic_data),
        ("生理指标", physiological),
        ("血液指标", blood_indicators),
        ("视力", vision),
        ("病史信息", medical_history),
        ("生活习惯", lifestyle),
        ("记录信息", record_info)
    ]

    # 生成最终文本（过滤空组，每组用“类别：\n- 字段1\n- 字段2”格式）
    formatted_sections = []
    for section_name, items in all_sections:
        # 过滤掉所有“未记录”的组（可选，减少冗余）
        if not all("未记录" in item for item in items):
            formatted_sections.append(f"{section_name}：")
            formatted_sections.extend([f"- {item}" for item in items])
            formatted_sections.append("")  # 组间空行

    # 合并所有部分，去掉最后一个空行
    return "\n".join(formatted_sections).rstrip()

def parse_facepp_result(result: dict) -> str:
    """
    遍历Face++ skinanalyze_advanced的result字典，按规则输出结构化字符串
    """
    # 定义各字段的解析规则映射
    # 眼皮类型规则
    eyelid_rule = {
        "0": "单眼皮",
        "1": "平行双眼皮",
        "2": "扇形双眼皮"
    }
    # 二元有无字段规则（0=无，1=有）
    binary_rule = {
        "0": "无",
        "1": "有"
    }
    #  肤质规则
    skin_type_rule = {
        0: "油性皮肤",
        1: "干性皮肤",
        2: "中性皮肤",
        3: "混合性皮肤"
    }
    # details字段的key对应肤质
    details_key_rule = {
        "0": "油性皮肤",
        "1": "干性皮肤",
        "2": "中性皮肤",
        "3": "混合性皮肤"
    }

    # 遍历result，按字段类型解析
    output_lines = []  # 存储每一行的解析结果
    for field, value_dict in result.items():

        # 处理眼皮类型字段（left_eyelids/right_eyelids）
        if field in ["left_eyelids", "right_eyelids"]:
            field_name = "左眼眼皮" if field == "left_eyelids" else "右眼眼皮"
            output_lines.append(f"- {field_name}：{value_dict['value']}（置信度：{value_dict['confidence']}）")

        #  处理二元有无字段
        elif field in ["eye_pouch", "dark_circle", "forehead_wrinkle", "crows_feet",
                      "eye_finelines", "glabella_wrinkle", "nasolabial_fold", "pores",
                      "pores_forehead", "pores_left_cheek", "pores_right_cheek", "pores_jaw",
                      "blackhead", "acne", "mole", "skin_spot"]:
            # 字段名中文映射
            field_name_map = {
                "eye_pouch": "眼袋",
                "dark_circle": "黑眼圈",
                "forehead_wrinkle": "抬头纹",
                "crows_feet": "鱼尾纹",
                "eye_finelines": "眼部细纹",
                "glabella_wrinkle": "眉间纹",
                "nasolabial_fold": "法令纹",
                "pores": "整体毛孔粗大",
                "pores_forehead": "前额毛孔粗大",
                "pores_left_cheek": "左脸颊毛孔粗大",
                "pores_right_cheek": "右脸颊毛孔粗大",
                "pores_jaw": "下巴毛孔粗大",
                "blackhead": "黑头",
                "acne": "痘痘",
                "mole": "痣",
                "skin_spot": "斑点"
            }
            field_name = field_name_map.get(field, field)
            desc = binary_rule.get(value_dict['value'])
            output_lines.append(f"- {field_name}：{desc}（置信度：{value_dict['confidence']}）")

        elif field == "skin_type":
            # skin_type的value是数字，直接用数字匹配规则
            desc = skin_type_rule[value_dict]
            output_lines.append(f"- 整体肤质：{desc}")  # skin_type本身无confidence，从details补充

        # 处理「嵌套肤质详情字段」（details）
        elif field == "details":
            output_lines.append("- 肤质详细分析（含各肤质置信度）：")
            # 遍历details的嵌套字典
            for detail_key, detail_val in value_dict.items():
                skin_subtype = details_key_rule.get(detail_key, f"未知肤质类型（key：{detail_key}）")
                sub_value = str(detail_val.get("value", "未知"))
                sub_confidence = round(detail_val.get("confidence", 0), 2)
                sub_desc = binary_rule.get(sub_value, f"未知状态（值：{sub_value}）")
                output_lines.append(f"  - {skin_subtype}：{sub_desc}（置信度：{sub_confidence}）")

        # 处理未定义的字段（避免遗漏）
        else:
            output_lines.append(f"- 未定义字段[{field}]：值={value_dict['value']}（置信度：{value_dict['confidence']}）")

    # 拼接所有行，生成最终字符串
    final_str = "面部皮肤检测结果：\n" + "\n".join(output_lines)
    return final_str

@tool
def analyze_skin(file_path: str) -> str:
    """专门针对皮肤图片进行处理，最终得到皮肤的状态、肤质等。当用户需要针对皮肤处理时使用"""
    API_URL = "https://api-cn.faceplusplus.com/facepp/v1/skinanalyze"

    valid_extensions = [".jpg", ".jpeg", ".png"]
    file_ext = os.path.splitext(file_path)[1].lower()  # 获取文件后缀
    if file_ext not in valid_extensions:
        error_msg = f"图片格式错误：仅支持 JPG/PNG 格式，当前为 {file_ext}"
        print(error_msg)
        return error_msg

    # 2. 校验图片大小（Face++ 限制 ≤2MB，避免超大图片导致400）
    max_size_mb = 2
    max_size_bytes = max_size_mb * 1024 * 1024  # 2MB 转字节
    file_size = os.path.getsize(file_path)
    if file_size > max_size_bytes:
        error_msg = f"图片体积超限：当前 {file_size/1024/1024:.2f}MB，需压缩至 {max_size_mb}MB 以内"
        print(error_msg)
        return error_msg

    with open(file_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")  # 编码为字符串


    data = {
        "api_key": skin_key,
        "api_secret": skin_secret,
        "image_base64": image_base64
    }
    response=None
    try:
        response = requests.post(API_URL, data=data,timeout=10)
        response.raise_for_status()
        print("请求成功，返回结果：", response.json())
    except Exception as e:
        print(f"请求失败：{str(e)}")
        if response:
            print("错误详情：", response.json())

    result = response.json().get("result")
    if result is None or not isinstance(result, dict):
        error_msg = "API 未返回有效皮肤分析数据（可能图片中未检测到人脸，或接口格式不匹配）"
        print(error_msg)
        return error_msg
    return  parse_facepp_result(result)



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
    """通用图片解析，理解图片内容，当用户需要解析图片时使用"""
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

from langchain_tavily import TavilySearch

def web_search(question: str) :
    try:
        search = TavilySearch(max_results=5)
        return search.invoke({"query": question})
    except Exception as e:
        return {"error": f"搜索失败：{str(e)}"}  # 错误时也返回字典
