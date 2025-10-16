package org.example.backendspringboot.Controller;

import org.example.backendspringboot.Service.UserLoginService;
import org.example.backendspringboot.Entity.UserLogin;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class UserController {
    @Autowired
    private UserLoginService userLoginService;

    @GetMapping("/users")
    public List<UserLogin> getUsers() {
        return userLoginService.getAllUsers();
    }
}
