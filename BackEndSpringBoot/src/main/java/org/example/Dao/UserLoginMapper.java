package org.example.Dao;
import org.apache.ibatis.annotations.Mapper;
import org.example.backendspringboot.Entity.UserLogin;
import java.util.List;
import org.apache.ibatis.annotations.Param;
@Mapper
public interface UserLoginMapper {
    //返回所有用户，测试用
    List<UserLogin> selectAllUsers();

    // 注册（插入新用户）
    int registerUser(UserLogin userLogin);

    // 注销（根据ID删除用户）
    int deleteUserById(@Param("user_id") Long user_id);

    // 修改密码
    int updatePassword(@Param("user_id") Long user_id, @Param("password") String password);

    // 修改用户名
    int updateUsername(@Param("user_id") Long user_id, @Param("username") String username);

    // 根据用户名查找用户
    UserLogin selectUserByUsername(@Param("username") String username);
}
