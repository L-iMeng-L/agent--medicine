package org.example.backendspringboot.Entity;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;
import java.sql.Date;

/**
 * 用户基础信息实体类
 * 对应表：user_info
 * 包含用户的基本个人信息
 */
@Data
@Getter
@Setter
public class UserInformation {
    /** 记录ID，主键，自增 */
    private Long info_id;

    /** 用户ID，外键，关联users表 */
    private Long user_id;

    /** 出生年月日，date */
    private Date birth_date;

    /** 手机号码，varchar(20) */
    private String phone;

    /** 邮箱，varchar(255) */
    private String email;

    /** 用户真实名字，text */
    private String name;
}