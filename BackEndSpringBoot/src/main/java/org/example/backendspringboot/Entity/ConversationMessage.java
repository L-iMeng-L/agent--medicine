package org.example.backendspringboot.Entity;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.sql.Timestamp;

/**
 * 会话消息交互体
 * 前后端交互的整体对象，包含会话索引和具体消息内容的所有字段
 */
@Data
@Getter
@Setter
public class ConversationMessage {
    // ConversationIndex字段
    /** 会话ID */
    private Long conversation_id;

    /** 发起用户ID */
    private Long user_id;

    /** 智能体ID */
    private Long agent_id;

    /** 会话开始时间 */
    private Timestamp start_time;

    /** 最后一条消息时间 */
    private Timestamp last_message_time;

    /** 备注 */
    private String remark;

    // ConversationContent字段
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