package org.example.backendspringboot.Service;

import org.example.Dao.UserLoginMapper;
import org.example.backendspringboot.Entity.UserLogin;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class UserService {
    @Autowired
    private UserLoginMapper userMapper;

    public List<UserLogin> getAllUsers() {
        return userMapper.selectAllUsers();
    }
}