package org.example.backendspringboot.Service;

import org.example.Dao.UserInformationMapper;
import org.example.backendspringboot.Entity.UserInformation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 用户基础信息服务层
 * 提供基于 user_id 的增删查改操作
 */
@Service
public class UserInfoService {

    @Autowired
    private UserInformationMapper userInformationMapper;

    /**
     * 根据用户ID查询用户基础信息
     * @param userId 用户ID
     * @return 用户基础信息实体对象
     */
    public UserInformation getUserInfoByUserId(Long userId) {
        return userInformationMapper.selectByUserId(userId);
    }

    /**
     * 新增用户基础信息
     * @param info 用户基础信息实体对象
     * @return 是否添加成功
     */
    public boolean addUserInfo(UserInformation info) {
        return userInformationMapper.insertUserInformation(info) > 0;
    }

    /**
     * 更新指定 info_id 的用户基础信息（根据 info_id 更新）
     * @param info 用户基础信息实体对象，需包含 info_id
     * @return 是否修改成功
     */
    public boolean updateUserInfo(UserInformation info) {
        return userInformationMapper.updateUserInformation(info) > 0;
    }

    /**
     * 根据 info_id 删除用户基础信息
     * @param infoId 用户信息记录ID
     * @return 是否删除成功
     */
    public boolean deleteUserInfoByInfoId(Long infoId) {
        return userInformationMapper.deleteByInfoId(infoId) > 0;
    }

    /**
     * 查询所有用户基础信息（可选：用于后端管理）
     * @return 用户基础信息实体对象列表
     */
    public List<UserInformation> getAllUserInfo() {
        return userInformationMapper.selectAll();
    }
}