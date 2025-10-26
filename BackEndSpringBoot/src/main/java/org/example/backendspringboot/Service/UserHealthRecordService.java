package org.example.backendspringboot.Service;

import org.example.Dao.UserHealthRecordMapper;
import org.example.backendspringboot.Entity.UserHealthRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 用户健康档案服务层
 * 实现健康档案的查询、添加和删除等功能
 */
@Service
public class UserHealthRecordService {

    @Autowired
    private UserHealthRecordMapper userHealthRecordMapper;

    /**
     * 根据用户ID查询所有健康档案记录
     * @param userId 用户ID
     * @return 健康档案记录列表
     */
    public List<UserHealthRecord> getRecordsByUserId(Long userId) {
        return userHealthRecordMapper.selectRecordsByUserId(userId);
    }

    /**
     * 根据用户ID清空健康档案记录
     * @param userId 用户ID
     * @return 是否成功（影响行数 > 0）
     */
    public boolean clearRecordsByUserId(Long userId) {
        return userHealthRecordMapper.deleteRecordsByUserId(userId) > 0;
    }

    /**
     * 新增一条健康档案记录
     * @param record 健康档案记录对象
     * @return 是否成功（影响行数 > 0）
     */
    public boolean addUserHealthRecord(UserHealthRecord record) {
        return userHealthRecordMapper.insertUserHealthRecord(record) > 0;
    }
}