package org.example.backendspringboot.Service;

import org.example.Dao.UserMapper;
import org.example.backendspringboot.UserLogin;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class UserService {
    @Autowired
    private UserMapper userMapper;

    public List<UserLogin> getAllUsers() {
        return userMapper.selectAllUsers();
    }
}