package org.example.backendspringboot.Controller;

import org.example.backendspringboot.Service.UserLoginService;
import org.example.backendspringboot.Entity.UserLogin;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 用户相关接口控制层
 * 实现用户注册、登录、注销、修改用户名/密码等功能接口
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
     */
    @PostMapping("/register")
    public boolean register(@RequestParam String username, @RequestParam String password) {
        return userLoginService.register(username, password);
    }

    /**
     * 用户登录
     * POST /user/login
     */
    @PostMapping("/login")
    public boolean login(@RequestParam String username, @RequestParam String password) {
        return userLoginService.login(username, password);
    }

    /**
     * 注销用户（通过用户名）
     * DELETE /user/delete
     */
    @DeleteMapping("/delete")
    public boolean deleteUser(@RequestParam String username) {
        return userLoginService.deleteUserByOldName(username);
    }

    /**
     * 修改密码（通过用户名）
     * PUT /user/password
     */
    @PutMapping("/password")
    public boolean updatePassword(@RequestParam String username, @RequestParam String newPassword) {
        return userLoginService.updatePasswordByOldName(username, newPassword);
    }

    /**
     * 修改用户名（通过旧用户名和新用户名）
     * PUT /user/username
     */
    @PutMapping("/username")
    public boolean updateUsername(@RequestParam String oldUsername, @RequestParam String newUsername) {
        return userLoginService.updateUsernameByOldName(oldUsername, newUsername);
    }
}