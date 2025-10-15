package org.example.Dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.example.backendspringboot.Entity.UserHealthRecord;
import java.util.List;
/**
 * 用户健康档案数据访问接口
 * 提供针对 user_health_record 表的基础操作，包括按用户ID查询、批量删除和新增健康档案记录等方法。
 * 适用于健康档案信息的管理、统计和维护场景。
 */
@Mapper
public interface UserHealthRecordMapper {
    /**
     * 根据用户ID查询所有健康档案记录
     * @param user_id 用户ID
     * @return 健康档案记录列表
     */
    List<UserHealthRecord> selectRecordsByUserId(@Param("user_id") Long user_id);

    /**
     * 根据用户ID清空记录
     * @param user_id 用户ID
     * @return 是否成功
     */
    int deleteRecordsByUserId(@Param("user_id") Long user_id);

    /**
     * 增加一条健康档案记录
     * @param record 健康档案记录对象
     * @return 影响行数
     */
    int insertUserHealthRecord(UserHealthRecord record);
}