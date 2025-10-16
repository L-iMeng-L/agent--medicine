package org.example.backendspringboot.Service;

import org.apache.shiro.SecurityUtils;
import org.apache.shiro.subject.Subject;
import org.example.Dao.UserLoginMapper;
import org.example.backendspringboot.Entity.UserLogin;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.apache.shiro.authc.*;
import org.apache.shiro.crypto.hash.SimpleHash;

import java.util.List;

@Service
public class UserLoginService {
    @Autowired
    private UserLoginMapper userMapper;

    public List<UserLogin> getAllUsers() {
        return userMapper.selectAllUsers();
    }

    private static final String HASH_ALGORITHM_NAME = "SHA-256";
    private static final int HASH_ITERATIONS = 1024;

    /**
     * 用户注册服务（密码加密存储）
     * @param username 用户名
     * @param password 密码
     * @return 是否成功
     */
    public boolean register(String username, String password) {
        UserLogin exist = userMapper.selectUserByUsername(username);
        if (exist != null) return false;
        String hashedPassword = new SimpleHash(HASH_ALGORITHM_NAME, password, username, HASH_ITERATIONS).toHex();
        UserLogin user = new UserLogin();
        user.setUsername(username);
        user.setPassword(hashedPassword);
        int result = userMapper.registerUser(user);
        return result > 0;
    }

    /**
     * 用户登录服务（Shiro认证，密码加密比对）
     * @param username 用户名
     * @param password 密码
     * @return 是否成功
     */
    public boolean login(String username, String password) {
        UserLogin user = userMapper.selectUserByUsername(username);
        if (user == null) return false;
        String hashedPassword = new SimpleHash(HASH_ALGORITHM_NAME, password, username, HASH_ITERATIONS).toHex();
        if (!hashedPassword.equals(user.getPassword())) return false;
        Subject subject = SecurityUtils.getSubject();
        UsernamePasswordToken token = new UsernamePasswordToken(username, password);
        try {
            subject.login(token);
            return true;
        } catch (AuthenticationException e) {
            return false;
        }
    }

    /**
     * 注销用户服务（根据用户名注销）
     * @param oldName 要注销的用户名
     * @return 是否成功
     */
    public boolean deleteUserByOldName(String oldName) {
        return deleteUserByName(oldName);
    }

    /**
     * 注销用户服务（根据用户名注销）
     * @param newName 要注销的用户名
     * @return 是否成功
     */
    public boolean deleteUserByNewName(String newName) {
        return deleteUserByName(newName);
    }

    /**
     * 修改密码服务（根据用户名修改密码）
     * @param oldName 用户名
     * @param newPassword 新密码（明文）
     * @return 修改密码是否成功
     */
    public boolean updatePasswordByOldName(String oldName, String newPassword) {
        return updatePasswordByName(oldName, newPassword);
    }

    /**
     * 修改密码服务（根据用户名修改密码）
     * @param newName 用户名
     * @param newPassword 新密码（明文）
     * @return 修改密码是否成功
     */
    public boolean updatePasswordByNewName(String newName, String newPassword) {
        return updatePasswordByName(newName, newPassword);
    }

    /**
     * 修改用户名服务（根据用户名修改用户名）
     * @param oldName 旧用户名
     * @param newUsername 新用户名
     * @return 修改用户名是否成功
     */
    public boolean updateUsernameByOldName(String oldName, String newUsername) {
        return updateUsernameByName(oldName, newUsername);
    }

    /**
     * 修改用户名服务（根据用户名修改用户名）
     * @param newName 旧用户名
     * @param newUsername 新用户名
     * @return 修改用户名是否成功
     */
    public boolean updateUsernameByNewName(String newName, String newUsername) {
        return updateUsernameByName(newName, newUsername);
    }

    /**
     * 注销用户服务（删除数据库中的用户数据，根据用户名，私有方法）
     * @param username 要注销的用户名
     * @return 是否成功
     */
    private boolean deleteUserByName(String username) {
        UserLogin user = userMapper.selectUserByUsername(username);
        if (user == null) return false;
        int result = userMapper.deleteUserById(user.getUser_id());
        return result > 0;
    }

    /**
     * 修改密码服务（加密新密码存储，根据用户名，私有方法）
     * @param username 用户名
     * @param newPassword 新密码（明文）
     * @return 修改密码是否成功
     */
    private boolean updatePasswordByName(String username, String newPassword) {
        UserLogin user = userMapper.selectUserByUsername(username);
        if (user == null) return false;
        String hashedPassword = new SimpleHash(HASH_ALGORITHM_NAME, newPassword, username, HASH_ITERATIONS).toHex();
        int result = userMapper.updatePassword(user.getUser_id(), hashedPassword);
        return result > 0;
    }

    /**
     * 修改用户名服务（根据用户名，私有方法）
     * @param oldUsername 旧用户名
     * @param newUsername 新用户名
     * @return 修改用户名是否成功
     */
    private boolean updateUsernameByName(String oldUsername, String newUsername) {
        UserLogin exist = userMapper.selectUserByUsername(newUsername);
        if (exist != null) return false;
        UserLogin user = userMapper.selectUserByUsername(oldUsername);
        if (user == null) return false;
        int result = userMapper.updateUsername(user.getUser_id(), newUsername);
        return result > 0;
    }
}