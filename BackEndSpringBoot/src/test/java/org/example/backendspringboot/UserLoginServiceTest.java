package org.example.backendspringboot;

import org.apache.shiro.subject.Subject;
import org.apache.shiro.util.ThreadContext;
import org.example.Dao.UserLoginMapper;
import org.example.backendspringboot.Entity.UserLogin;
import org.example.backendspringboot.Service.UserLoginService;
import org.junit.jupiter.api.*;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.boot.test.context.SpringBootTest;
import org.apache.shiro.mgt.SecurityManager;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * UserLoginService单元测试
 * 测试流程：创建-判断-修改-判断-删除-判断，保证前后数据库数据一致
 */
@SpringBootTest
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserLoginServiceTest {

    @Mock
    private UserLoginMapper userLoginMapper;

    @InjectMocks
    private UserLoginService userLoginService;

    private static final Long TEST_USER_ID = 99999L;
    private static final String TEST_USERNAME = "unit_test_user";
    private static final String TEST_PASSWORD = "unit_test_pass";
    private static final String TEST_NEW_PASSWORD = "unit_test_newpass";
    private static final String TEST_NEW_USERNAME = "unit_test_user_new";

    private UserLogin testUser;

    @BeforeEach
    public void setUp() {
        MockitoAnnotations.openMocks(this);

        testUser = new UserLogin();
        testUser.setUser_id(TEST_USER_ID);
        testUser.setUsername(TEST_USERNAME);
        testUser.setPassword("encryptedPassword");

        SecurityManager securityManager = mock(SecurityManager.class);
        ThreadContext.bind(securityManager);

        Subject subject = mock(Subject.class);
        doNothing().when(subject).login(any());
        ThreadContext.bind(subject);
    }

    @Test
    @Order(1)
    public void testRegister() {
        when(userLoginMapper.selectUserByUsername(TEST_USERNAME)).thenReturn(null);
        when(userLoginMapper.registerUser(any(UserLogin.class))).thenReturn(1);

        boolean registerResult = userLoginService.register(TEST_USERNAME, TEST_PASSWORD);
        assertTrue(registerResult);

        when(userLoginMapper.selectUserByUsername(TEST_USERNAME)).thenReturn(testUser);
        boolean registerFail = userLoginService.register(TEST_USERNAME, TEST_PASSWORD);
        assertFalse(registerFail);
    }

    @Test
    @Order(2)
    public void testLogin() {
        when(userLoginMapper.selectUserByUsername(TEST_USERNAME)).thenReturn(testUser);
        when(userLoginMapper.selectUserByUsername("not_exist")).thenReturn(null);

        testUser.setPassword(new org.apache.shiro.crypto.hash.SimpleHash("SHA-256", TEST_PASSWORD, TEST_USERNAME, 1024).toHex());
        boolean loginResult = userLoginService.login(TEST_USERNAME, TEST_PASSWORD);
        assertTrue(loginResult);

        boolean loginFail = userLoginService.login(TEST_USERNAME, "wrong_password");
        assertFalse(loginFail);

        boolean loginNoUser = userLoginService.login("not_exist", TEST_PASSWORD);
        assertFalse(loginNoUser);
    }

    @Test
    @Order(3)
    public void testUpdatePasswordByOldName() {
        when(userLoginMapper.selectUserByUsername(TEST_USERNAME)).thenReturn(testUser);
        when(userLoginMapper.updatePassword(eq(TEST_USER_ID), anyString())).thenReturn(1);

        boolean updateResult = userLoginService.updatePasswordByOldName(TEST_USERNAME, TEST_NEW_PASSWORD);
        assertTrue(updateResult);

        when(userLoginMapper.selectUserByUsername(TEST_USERNAME)).thenReturn(null);
        boolean updateFail = userLoginService.updatePasswordByOldName(TEST_USERNAME, TEST_NEW_PASSWORD);
        assertFalse(updateFail);
    }

    @Test
    @Order(4)
    public void testUpdateUsernameByOldName() {
        // 新用户名不存在
        when(userLoginMapper.selectUserByUsername(TEST_NEW_USERNAME)).thenReturn(null);
        when(userLoginMapper.selectUserByUsername(TEST_USERNAME)).thenReturn(testUser);
        when(userLoginMapper.updateUsername(eq(TEST_USER_ID), eq(TEST_NEW_USERNAME))).thenReturn(1);

        boolean updateResult = userLoginService.updateUsernameByOldName(TEST_USERNAME, TEST_NEW_USERNAME);
        assertTrue(updateResult);

        // 新用户名已存在
        UserLogin existUser = new UserLogin();
        existUser.setUser_id(TEST_USER_ID + 1);
        existUser.setUsername(TEST_NEW_USERNAME);
        when(userLoginMapper.selectUserByUsername(TEST_NEW_USERNAME)).thenReturn(existUser);

        boolean updateFail = userLoginService.updateUsernameByOldName(TEST_USERNAME, TEST_NEW_USERNAME);
        assertFalse(updateFail);
    }

    @Test
    @Order(5)
    public void testDeleteUserByOldName() {
        when(userLoginMapper.selectUserByUsername(TEST_USERNAME)).thenReturn(testUser);
        when(userLoginMapper.deleteUserById(eq(TEST_USER_ID))).thenReturn(1);

        boolean deleteResult = userLoginService.deleteUserByOldName(TEST_USERNAME);
        assertTrue(deleteResult);

        // 用户不存在
        when(userLoginMapper.selectUserByUsername(TEST_USERNAME)).thenReturn(null);
        boolean deleteFail = userLoginService.deleteUserByOldName(TEST_USERNAME);
        assertFalse(deleteFail);
    }
}