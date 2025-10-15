package org.example.backendspringboot.Entity;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

/**
 * 用户登录实体类
 * user_id: 用户ID，主键，自增，bigint
 * username: 用户名，varchar(255)
 * password: 用户密码，varchar(255)
 */
@Data
@Getter
@Setter
public class UserLogin {
    private Long user_id;      // 用户ID，主键，自增
    private String username;   // 用户名
    private String password;   // 用户密码
}
