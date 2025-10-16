package org.example.backendspringboot;

import org.example.backendspringboot.Entity.UserLogin;
import org.example.backendspringboot.Service.UserLoginService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest
class BackEndSpringBootApplicationTests {
    @Autowired
    private UserLoginService userLoginService;
    @Test
    void contextLoads() {
        List<UserLogin> users = userLoginService.getAllUsers();
        assertNotNull(users); // 断言结果非空
        // 可以根据实际情况添加更多断言
        System.out.println(users);
    }

}
