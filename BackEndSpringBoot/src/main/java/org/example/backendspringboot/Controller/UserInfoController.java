package org.example.backendspringboot.Controller;

import org.example.backendspringboot.Entity.UserInformation;
import org.example.backendspringboot.Service.UserInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 用户基础信息接口控制层
 * 提供基于 user_id 的增删查改操作
 */
@RestController
@RequestMapping("/user-info")
public class UserInfoController {

    @Autowired
    private UserInfoService userInfoService;

    /**
     * 根据用户ID查询用户基础信息
     * GET /user-info/{userId}
     *
     * @param userId 用户ID
     * @return 用户基础信息实体对象
     * 调用示例:
     * GET http://localhost:8080/user-info/123
     */
    @GetMapping("/{userId}")
    public UserInformation getUserInfoByUserId(@PathVariable("userId") Long userId) {
        return userInfoService.getUserInfoByUserId(userId);
    }

    /**
     * 新增用户基础信息
     * POST /user-info
     *
     * @param info 用户基础信息实体对象（JSON格式提交）
     * @return 是否添加成功
     * 调用示例:
     * POST http://localhost:8080/user-info
     * Body (JSON):
     * {
     *   "user_id": 123,
     *   "birth_date": "2000-01-01",
     *   "phone": "12345678901",
     *   "email": "test@example.com",
     *   "name": "张三"
     * }
     */
    @PostMapping("")
    public boolean addUserInfo(@RequestBody UserInformation info) {
        return userInfoService.addUserInfo(info);
    }

    /**
     * 更新用户基础信息（根据 info_id 修改）
     * PUT /user-info
     *
     * @param info 用户基础信息实体对象（JSON格式提交，需包含 info_id）
     * @return 是否修改成功
     * 调用示例:
     * PUT http://localhost:8080/user-info
     * Body (JSON):
     * {
     *   "info_id": 1,
     *   "user_id": 123,
     *   "birth_date": "2000-01-01",
     *   "phone": "12345678901",
     *   "email": "newemail@example.com",
     *   "name": "张三"
     * }
     */
    @PutMapping("")
    public boolean updateUserInfo(@RequestBody UserInformation info) {
        return userInfoService.updateUserInfo(info);
    }

    /**
     * 根据 info_id 删除用户基础信息
     * DELETE /user-info/{infoId}
     *
     * @param infoId 用户信息记录ID
     * @return 是否删除成功
     * 调用示例:
     * DELETE http://localhost:8080/user-info/1
     */
    @DeleteMapping("/{infoId}")
    public boolean deleteUserInfoByInfoId(@PathVariable("infoId") Long infoId) {
        return userInfoService.deleteUserInfoByInfoId(infoId);
    }

    /**
     * 查询所有用户基础信息（后端管理用）
     * GET /user-info/all
     *
     * @return 用户基础信息实体对象列表
     * 调用示例:
     * GET http://localhost:8080/user-info/all
     */
    @GetMapping("/all")
    public List<UserInformation> getAllUserInfo() {
        return userInfoService.getAllUserInfo();
    }
}