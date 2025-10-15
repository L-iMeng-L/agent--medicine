package org.example.backendspringboot.Entity;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.sql.Timestamp;

/**
 * 对话内容实体类
 * 对应表：conversation_content
 * 记录用户和智能体的每一条消息，包括文本和附件引用信息
 */
@Data
@Getter
@Setter
public class ConversationContent {
    /** 消息ID，主键，自增 */
    private Long message_id;

    /** 会话ID，外键，关联会话索引表 */
    private Long conversation_id;

    /** 发送方类型（user, agent） */
    private String sender_type;

    /** 发送者ID（user_id或agent_id） */
    private Long sender_id;

    /** 发送时间 */
    private Timestamp send_time;

    /** 当前会话中的消息序号（递增） */
    private Integer message_seq;

    /** 消息文本内容 */
    private String content;

    /** 附件引用信息（如附件ID列表、URL列表、JSON等） */
    private String reference;
}