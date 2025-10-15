package org.example.backendspringboot.Entity;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.math.BigDecimal;
import java.sql.Timestamp;

/**
 * 用户健康档案实体类
 * 对应表：user_health_record
 * 包含用户的健康基本信息与生活习惯、既往病史等
 */
@Data
@Getter
@Setter
public class UserHealthRecord {
    /** 健康档案记录ID，主键，自增 */
    private Long record_id;

    /** 用户ID，外键，关联users表 */
    private Long user_id;

    /** 身高（厘米），decimal(5,2) */
    private BigDecimal height_cm;

    /** 体重（公斤），decimal(5,2) */
    private BigDecimal weight_kg;

    /** 血型，varchar(5) */
    private String blood_type;

    /** 身体质量指数，decimal(4,2) */
    private BigDecimal bmi;

    /** 收缩压（mmHg），int */
    private Integer blood_pressure_systolic;

    /** 舒张压（mmHg），int */
    private Integer blood_pressure_diastolic;

    /** 平均心率（次/分钟），int */
    private Integer heart_rate;

    /** 体温（℃），decimal(4,2) */
    private BigDecimal body_temperature;

    /** 血糖（mmol/L），decimal(5,2) */
    private BigDecimal blood_sugar;

    /** 总胆固醇（mmol/L），decimal(5,2) */
    private BigDecimal cholesterol_total;

    /** 低密度胆固醇（mmol/L），decimal(5,2) */
    private BigDecimal cholesterol_ldl;

    /** 高密度胆固醇（mmol/L），decimal(5,2) */
    private BigDecimal cholesterol_hdl;

    /** 甘油三酯（mmol/L），decimal(5,2) */
    private BigDecimal triglycerides;

    /** 左眼视力，decimal(3,2) */
    private BigDecimal vision_left;

    /** 右眼视力，decimal(3,2) */
    private BigDecimal vision_right;

    /** 过敏史，text */
    private String allergies;

    /** 慢性病史，text */
    private String chronic_diseases;

    /** 既往病史，text */
    private String medical_history;

    /** 吸烟状况，varchar(50) */
    private String smoking_status;

    /** 饮酒状况，varchar(50) */
    private String drinking_status;

    /** 锻炼频率，varchar(50) */
    private String exercise_frequency;

    /** 平均睡眠时长（小时），decimal(3,1) */
    private BigDecimal sleep_hours;

    /** 记录日期，datetime */
    private Timestamp date;
}