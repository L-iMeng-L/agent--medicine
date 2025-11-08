package org.example.backendspringboot.Service;

import org.example.Dao.UserLoginMapper;
import org.example.backendspringboot.Entity.UserLogin;
import org.apache.shiro.crypto.hash.SimpleHash;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 用户登录/注册等业务服务
 */
@Service
public class UserLoginService {

    @Autowired
    private UserLoginMapper userMapper;

    private static final String HASH_ALGORITHM_NAME = "SHA-256";
    private static final int HASH_ITERATIONS = 1024;
    /** 接口失败时统一返回码 */
    public static final long FAIL_CODE = -1L;

    /**
     * 获取所有用户
     */
    public List<UserLogin> getAllUsers() {
        return userMapper.selectAllUsers();
    }

    /**
     * 注册用户：密码加密存储，注册成功返回 user_id，失败返回 -1
     * 失败场景：用户名已存在或插入失败
     *
     * @param username 用户名
     * @param password 明文密码
     * @return 注册成功返回用户ID；失败返回 -1
     */
    public Long register(String username, String password) {
        UserLogin exist = userMapper.selectUserByUsername(username);
        if (exist != null) return FAIL_CODE;

        String hashedPassword = hashPassword(username, password);
        UserLogin user = new UserLogin();
        user.setUsername(username);
        user.setPassword(hashedPassword);

        int result = userMapper.registerUser(user);
        if (result > 0 && user.getUser_id() != null) {
            // useGeneratedKeys 会把自增主键回填到 user.user_id
            return user.getUser_id();
        }
        return FAIL_CODE;
    }

    /**
     * 用户登录：校验用户名和密码，成功返回 user_id，失败返回 -1
     * 失败场景：用户不存在或密码不正确
     *
     * @param username 用户名
     * @param password 明文密码
     * @return 成功返回用户ID；失败返回 -1
     */
    public Long login(String username, String password) {
        UserLogin user = userMapper.selectUserByUsername(username);
        if (user == null) return FAIL_CODE;

        String hashedPassword = hashPassword(username, password);
        if (hashedPassword.equals(user.getPassword())) {
            return user.getUser_id();
        }
        return FAIL_CODE;
    }

    /**
     * 注销用户（根据用户名删除）
     *
     * @param oldName 用户名
     * @return 是否成功
     */
    public boolean deleteUserByOldName(String oldName) {
        return deleteUserByName(oldName);
    }

    /**
     * 注销用户（根据用户名删除）
     *
     * @param newName 用户名
     * @return 是否成功
     */
    public boolean deleteUserByNewName(String newName) {
        return deleteUserByName(newName);
    }

    /**
     * 修改密码（根据用户名）
     *
     * @param oldName 用户名
     * @param newPassword 新密码（明文）
     * @return 是否成功
     */
    public boolean updatePasswordByOldName(String oldName, String newPassword) {
        return updatePasswordByName(oldName, newPassword);
    }

    /**
     * 修改密码（根据用户名）
     *
     * @param newName 用户名
     * @param newPassword 新密码（明文）
     * @return 是否成功
     */
    public boolean updatePasswordByNewName(String newName, String newPassword) {
        return updatePasswordByName(newName, newPassword);
    }

    /**
     * 修改用户名（根据旧用户名修改为新用户名）
     *
     * @param oldName 旧用户名
     * @param newUsername 新用户名
     * @return 是否成功
     */
    public boolean updateUsernameByOldName(String oldName, String newUsername) {
        return updateUsernameByName(oldName, newUsername);
    }

    /**
     * 修改用户名（根据旧用户名修改为新用户名）
     *
     * @param newName 旧用户名
     * @param newUsername 新用户名
     * @return 是否成功
     */
    public boolean updateUsernameByNewName(String newName, String newUsername) {
        return updateUsernameByName(newName, newUsername);
    }

    /* -------------------- 私有辅助方法 -------------------- */

    /**
     * 统一加密规则：SHA-256 + username 作为 salt + 1024 次迭代
     */
    private String hashPassword(String username, String password) {
        return new SimpleHash(HASH_ALGORITHM_NAME, password, username, HASH_ITERATIONS).toHex();
    }

    /**
     * 注销用户（根据用户名私有方法）
     */
    private boolean deleteUserByName(String username) {
        UserLogin user = userMapper.selectUserByUsername(username);
        if (user == null) return false;
        int result = userMapper.deleteUserById(user.getUser_id());
        return result > 0;
    }

    /**
     * 修改密码（根据用户名私有方法）
     */
    private boolean updatePasswordByName(String username, String newPassword) {
        UserLogin user = userMapper.selectUserByUsername(username);
        if (user == null) return false;
        String hashedPassword = hashPassword(username, newPassword);
        int result = userMapper.updatePassword(user.getUser_id(), hashedPassword);
        return result > 0;
    }

    /**
     * 修改用户名（根据用户名私有方法）
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