package org.example.Dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.example.backendspringboot.Entity.UserHealthRecord;
import java.util.List;

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