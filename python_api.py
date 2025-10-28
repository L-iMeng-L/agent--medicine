from medic_agent import app  # 引入langgraph实例
from generate_report import report_app
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from utility import parse_health_record  # 确保该函数返回字典或适配的健康数据
import uvicorn
from dataclasses import dataclass  # 用于UserHealthRecord的字段初始化
from decimal import Decimal
import uuid
import threading  # 用于并行启动两个服务


class ConversationMessage(BaseModel):
    """对应Java的ConversationMessage类，Pydantic模型（用于请求/响应校验）"""
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    agent_id: Optional[int] = None
    start_time: Optional[str] = None
    last_message_time: Optional[str] = None
    remark: Optional[str] = None  # 用户基础信息
    # ConversationContent字段
    sender_type: Optional[str] = None
    sender_id: Optional[int] = None
    send_time: Optional[str] = None
    message_seq: Optional[int] = None
    content: Optional[str] = None
    reference: Optional[str] = None

    class Config:
        extra = "allow"  # 兼容Java端额外字段


@dataclass
class UserHealthRecord:
    """对应Java的UserHealthRecord类，支持便捷实例化（如 UserHealthRecord(height_cm=Decimal("175.5"))）"""
    record_id: Optional[int] = None
    user_id: Optional[int] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    blood_type: Optional[str] = None
    bmi: Optional[Decimal] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    body_temperature: Optional[Decimal] = None
    blood_sugar: Optional[Decimal] = None
    cholesterol_total: Optional[Decimal] = None
    cholesterol_ldl: Optional[Decimal] = None
    cholesterol_hdl: Optional[Decimal] = None
    triglycerides: Optional[Decimal] = None
    vision_left: Optional[Decimal] = None
    vision_right: Optional[Decimal] = None
    allergies: Optional[str] = None
    chronic_diseases: Optional[str] = None
    medical_history: Optional[str] = None
    smoking_status: Optional[str] = None
    drinking_status: Optional[str] = None
    exercise_frequency: Optional[str] = None
    sleep_hours: Optional[Decimal] = None
    date: Optional[datetime] = None

fastapi = FastAPI(title="医疗咨询与报告API", description="包含对话咨询（/api/chat）和健康报告生成（/api/report）接口")


@fastapi.post("/api/chat", response_model=ConversationMessage)
def chat(request: dict):
    try:
        if "msg" not in request:
            raise HTTPException(status_code=400, detail="请求缺少必要字段：msg")
        msg_data = request["msg"]
        health_data = request.get("health", {})  # 容错：health可选，默认空字典

        required_msg_fields = ["conversation_id", "content"]
        for field in required_msg_fields:
            if field not in msg_data:
                raise HTTPException(status_code=400, detail=f"msg缺少必要字段：{field}")

        conversation_id = msg_data["conversation_id"]  # 已校验存在，可直接取
        user_info = msg_data.get("remark", "")  # 容错：无remark则为空字符串
        user_question = msg_data["content"]  # 已校验存在
        file_path = msg_data.get("reference", "").strip()  # 去空格，避免空字符串干扰

        has_file_path = False
        if file_path:
            has_file_path = True
            user_question = f"{user_question}\n（附加文件路径：{file_path}）"

        health_record = parse_health_record(health_data)

        initial_state = {
            "messages": [("user", user_question)],
            "user_question": user_question,
            "user_info": user_info,
            "has_user_info": True,
            "back_times": 0,
            "has_file_path": has_file_path,
            "health_record": health_record,
        }

        thread_id = f"thread-{conversation_id}"
        config = {"configurable": {"thread_id": thread_id}}
        final_state = None
        for event in app.stream(initial_state, config, stream_mode="values"):
            final_state = event
        if not final_state:
            raise HTTPException(status_code=500, detail="LangGraph工作流未返回结果")

        final_answer = final_state.get("final_answer", "未生成有效回答")
        updated_user_info = final_state.get("user_info", user_info)
        new_message_seq = (msg_data.get("message_seq", 0) or 0) + 1  # 容错：message_seq为None则从0开始
        current_time = datetime.now().isoformat()

        return ConversationMessage(
            conversation_id=conversation_id,
            user_id=msg_data.get("user_id"),
            agent_id=msg_data.get("agent_id"),
            start_time=msg_data.get("start_time"),
            last_message_time=current_time,
            sender_type="agent",
            sender_id=msg_data.get("agent_id"),
            send_time=current_time,
            message_seq=new_message_seq,
            content=final_answer,
            remark=updated_user_info,
            reference=""
        )

    except HTTPException as e:
        # 异常响应：确保返回ConversationMessage实例（匹配response_model）
        return ConversationMessage(
            conversation_id=msg_data.get("conversation_id") if "msg" in locals() else None,
            content=f"错误：{e.detail}",
            sender_type="agent",
            send_time=datetime.now().isoformat()
        )
    except Exception as e:
        # 通用异常：避免暴露敏感信息，限制错误长度
        return ConversationMessage(
            conversation_id=msg_data.get("conversation_id") if "msg" in locals() else None,
            content=f"咨询处理失败：{str(e)[:100]}",  # 限制长度，避免过长
            sender_type="agent",
            send_time=datetime.now().isoformat()
        )


class ReportResponse(BaseModel):
    """报告接口的响应模型（适配Java端，包含报告内容和基础会话信息）"""
    report_content: str  # Markdown格式的报告字符串
    user_id: Optional[int] = None  # 关联用户ID
    generate_time: str  # 报告生成时间
    message: str = "success"


@fastapi.post("/api/report", response_model=ReportResponse)
def report(request: dict):
    try:
        if not request:
            raise HTTPException(status_code=400, detail="请求体不能为空，需包含健康档案数据")

        health_record = parse_health_record(request)

        initial_state = {
            "health_record": health_record,
            "back_times": 0,
        }
        thread_id = f"report-thread-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}}

        final_state = None
        for event in report_app.stream(initial_state, config, stream_mode="values"):
            final_state = event
        if not final_state:
            raise HTTPException(status_code=500, detail="报告生成工作流未返回结果")

        final_report = final_state.get("final_answer", "未生成有效健康报告")
        current_time = datetime.now().isoformat()

        return ReportResponse(
            report_content=final_report,
            user_id=request.get("user_id"),  # 从请求中提取用户ID（需Java端传递）
            generate_time=current_time
        )

    except HTTPException as e:
        return ReportResponse(
            report_content=f"错误：{e.detail}",
            generate_time=datetime.now().isoformat(),
            message="error"
        )
    except Exception as e:
        return ReportResponse(
            report_content=f"报告生成失败：{str(e)[:100]}",
            generate_time=datetime.now().isoformat(),
            message="error"
        )



if __name__ == "__main__":
    uvicorn.run(
        app="python_api:fastapi",
        host="0.0.0.0",  # 允许外部访问
        port=8000,  # 单端口承载两个接口
        workers=1,
        reload=False
    )