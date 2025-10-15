package org.example.backendspringboot.Entity;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.sql.Timestamp;

/**
 * 会话索引实体类
 * 对应表：conversation_index
 * 记录用户和智能体的会话基本信息
 */
@Data
@Getter
@Setter
public class ConversationIndex {
    /** 会话ID，主键，自增 */
    private Long conversation_id;

    /** 发起用户ID（外键，关联用户表） */
    private Long user_id;

    /** 智能体ID */
    private Long agent_id;

    /** 会话开始时间 */
    private Timestamp start_time;

    /** 最后一条消息时间 */
    private Timestamp last_message_time;

    /** 备注 */
    private String remark;
}