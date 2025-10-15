package org.example.Dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.example.backendspringboot.Entity.UserInformation;
import java.util.List;

/**
 * 用户基础信息数据访问接口
 * 提供对 user_info 表的增删查改操作方法
 */
@Mapper
public interface UserInformationMapper {

    /**
     * 根据用户ID查询用户基础信息
     * @param user_id 用户ID，外键
     * @return 用户基础信息实体对象
     */
    UserInformation selectByUserId(@Param("user_id") Long user_id);

    /**
     * 新增一条用户基础信息
     * @param info 用户基础信息实体对象
     * @return 影响的数据库行数
     */
    int insertUserInformation(UserInformation info);

    /**
     * 更新指定 info_id 的用户基础信息
     * @param info 用户基础信息实体对象，需包含 info_id
     * @return 影响的数据库行数
     */
    int updateUserInformation(UserInformation info);

    /**
     * 根据 info_id 删除用户基础信息
     * @param info_id 记录ID，主键
     * @return 影响的数据库行数
     */
    int deleteByInfoId(@Param("info_id") Long info_id);

    /**
     * 查询所有用户基础信息
     * @return 用户基础信息实体对象列表
     */
    List<UserInformation> selectAll();
}