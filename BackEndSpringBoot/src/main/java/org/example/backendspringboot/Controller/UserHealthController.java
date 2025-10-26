package org.example.backendspringboot.Controller;

import org.example.backendspringboot.Entity.UserHealthRecord;
import org.example.backendspringboot.Service.UserHealthRecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 用户健康档案相关接口控制层
 * 实现健康档案的查询、添加和删除等功能
 */
@RestController
@RequestMapping("/user-health")
public class UserHealthController {

    @Autowired
    private UserHealthRecordService userHealthRecordService;

    /**
     * 根据用户ID查询健康档案记录（按日期降序排列）
     * GET /user-health/records?uid={uid}
     * @param uid 用户ID
     * @return 健康档案记录列表
     */
    @GetMapping("/records")
    public List<UserHealthRecord> getHealthRecordsByUserId(@RequestParam("uid") Long uid) {
        List<UserHealthRecord> records = userHealthRecordService.getRecordsByUserId(uid);
        // 按日期降序排列
        return records.stream()
                .sorted(Comparator.comparing(UserHealthRecord::getDate).reversed())
                .collect(Collectors.toList());
    }

    /**
     * 新增一条健康档案记录
     * POST /user-health/record
     * @param record 健康档案记录对象（JSON格式提交）
     * @return 是否添加成功
     */
    @PostMapping("/record")
    public boolean addHealthRecord(@RequestBody UserHealthRecord record) {
        return userHealthRecordService.addUserHealthRecord(record);
    }

    /**
     * 清空某用户的健康档案记录
     * DELETE /user-health/records?uid={uid}
     * @param uid 用户ID
     * @return 是否删除成功
     */
    @DeleteMapping("/records")
    public boolean clearHealthRecordsByUserId(@RequestParam("uid") Long uid) {
        return userHealthRecordService.clearRecordsByUserId(uid);
    }
}