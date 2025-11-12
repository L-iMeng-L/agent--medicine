#coding=GBK
import requests
import random
from datetime import datetime, timedelta

API_URL = "http://localhost:8080/user-health/record"
USER_ID = 1120  # 假设用户ID为10001
DAYS = 30        # 时间跨度：最近30天
MAX_PER_DAY = 3  # 每天最多几条

def random_health_record(day_offset, record_in_day):
    base_date = datetime.now() - timedelta(days=day_offset)
    # 一天记录多条时加几个小时
    record_time = base_date.replace(hour=8 + 5 * record_in_day, minute=random.randint(0, 59), second=0)
    # 偏胖大学生参数：21岁男，身高175cm，体重80-85kg
    height_cm = 175.0
    weight_kg = round(random.uniform(80, 85), 1)
    bmi = round(weight_kg / ((height_cm / 100) ** 2), 2)
    systolic = random.randint(120, 130)
    diastolic = random.randint(75, 82)
    heart_rate = random.randint(75, 88)
    temp = round(random.uniform(36.5, 37.1), 2)
    blood_sugar = round(random.uniform(4.9, 5.3), 2)
    cholesterol_total = round(random.uniform(4.8, 5.4), 2)
    cholesterol_ldl = round(random.uniform(2.8, 3.5), 2)
    cholesterol_hdl = round(random.uniform(1.0, 1.4), 2)
    triglycerides = round(random.uniform(1.0, 1.5), 2)
    vision_left = round(random.uniform(0.8, 1.0), 2)
    vision_right = round(random.uniform(0.8, 1.0), 2)
    allergies = "无"
    chronic_diseases = "无"
    medical_history = "无"
    smoking_status = random.choice(["不吸烟", "偶尔", "不吸烟"])
    drinking_status = random.choice(["偶尔", "不喝酒"])
    exercise_frequency = random.choice(["每周2-3次", "每周1次", "每周3次"])
    sleep_hours = round(random.uniform(6.5, 7.5), 1)
    # ISO格式
    date = record_time.strftime("%Y-%m-%dT%H:%M:%S")
    blood_type = random.choice(["O", "A", "B", "AB"])
    return {
        "user_id": USER_ID,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "blood_type": blood_type,
        "bmi": bmi,
        "blood_pressure_systolic": systolic,
        "blood_pressure_diastolic": diastolic,
        "heart_rate": heart_rate,
        "body_temperature": temp,
        "blood_sugar": blood_sugar,
        "cholesterol_total": cholesterol_total,
        "cholesterol_ldl": cholesterol_ldl,
        "cholesterol_hdl": cholesterol_hdl,
        "triglycerides": triglycerides,
        "vision_left": vision_left,
        "vision_right": vision_right,
        "allergies": allergies,
        "chronic_diseases": chronic_diseases,
        "medical_history": medical_history,
        "smoking_status": smoking_status,
        "drinking_status": drinking_status,
        "exercise_frequency": exercise_frequency,
        "sleep_hours": sleep_hours,
        "date": date
    }

def batch_add_records():
    total = 0
    for day in range(DAYS, 0, -1):
        count_today = random.randint(1, MAX_PER_DAY)
        for record_in_day in range(count_today):
            record = random_health_record(day, record_in_day)
            try:
                resp = requests.post(API_URL, json=record)
                print(f"{record['date']} | Status: {resp.status_code} | {resp.text}")
                total += 1
            except Exception as e:
                print(f"Error: {e}")
    print(f"Batch complete, total uploaded: {total}")

if __name__ == "__main__":
    batch_add_records()