package org.example.Dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.example.backendspringboot.Entity.UserLogin;
import java.util.List;

/**
 * 用户登录数据访问接口
 * 提供对 users 表的相关操作方法，包括用户的增删查改和认证相关功能
 */
@Mapper
public interface UserLoginMapper {

    /**
     * 查询所有用户信息（用于测试或管理）
     * @return 用户登录实体对象列表
     */
    List<UserLogin> selectAllUsers();

    /**
     * 注册新用户（插入一条用户记录）
     * @param userLogin 用户登录实体对象
     * @return 影响的数据库行数
     */
    int registerUser(UserLogin userLogin);

    /**
     * 注销用户（根据用户ID删除用户记录）
     * @param user_id 用户ID，主键
     * @return 影响的数据库行数
     */
    int deleteUserById(@Param("user_id") Long user_id);

    /**
     * 修改用户密码
     * @param user_id 用户ID，主键
     * @param password 新密码
     * @return 影响的数据库行数
     */
    int updatePassword(@Param("user_id") Long user_id, @Param("password") String password);

    /**
     * 修改用户名
     * @param user_id 用户ID，主键
     * @param username 新用户名
     * @return 影响的数据库行数
     */
    int updateUsername(@Param("user_id") Long user_id, @Param("username") String username);

    /**
     * 根据用户名查询用户信息（用于登录或校验用户名是否存在）
     * @param username 用户名
     * @return 用户登录实体对象
     */
    UserLogin selectUserByUsername(@Param("username") String username);
}