package org.example.backendspringboot.Controller;

import org.example.backendspringboot.Service.UserLoginService;
import org.example.backendspringboot.Entity.UserLogin;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 用户相关接口控制层
 * 提供用户注册、登录、注销、修改用户名/密码等接口
 */
@RestController
@RequestMapping("/user")
public class UserController {

    @Autowired
    private UserLoginService userLoginService;

    /**
     * 获取所有用户信息
     * GET /user/all
     */
    @GetMapping("/all")
    public List<UserLogin> getUsers() {
        return userLoginService.getAllUsers();
    }

    /**
     * 用户注册
     * POST /user/register
     *
     * 入参：
     * - username
     * - password
     *
     * 返回：
     * - 注册成功：返回用户ID（Long）
     * - 注册失败：返回 -1
     */
    @PostMapping("/register")
    public Long register(@RequestParam String username, @RequestParam String password) {
        return userLoginService.register(username, password);
    }

    /**
     * 用户登录
     * POST /user/login
     *
     * 入参：
     * - username
     * - password
     *
     * 返回：
     * - 登录成功：返回用户ID（Long）
     * - 登录失败：返回 -1
     */
    @PostMapping("/login")
    public Long login(@RequestParam String username, @RequestParam String password) {
        return userLoginService.login(username, password);
    }

    /**
     * 注销用户（通过用户名）
     * DELETE /user/delete
     *
     * 返回：
     * - true/false
     */
    @DeleteMapping("/delete")
    public boolean deleteUser(@RequestParam String username) {
        return userLoginService.deleteUserByOldName(username);
    }

    /**
     * 修改密码（通过用户名）
     * PUT /user/password
     *
     * 返回：
     * - true/false
     */
    @PutMapping("/password")
    public boolean updatePassword(@RequestParam String username, @RequestParam String newPassword) {
        return userLoginService.updatePasswordByOldName(username, newPassword);
    }

    /**
     * 修改用户名（通过旧用户名和新用户名）
     * PUT /user/username
     *
     * 返回：
     * - true/false
     */
    @PutMapping("/username")
    public boolean updateUsername(@RequestParam String oldUsername, @RequestParam String newUsername) {
        return userLoginService.updateUsernameByOldName(oldUsername, newUsername);
    }
}