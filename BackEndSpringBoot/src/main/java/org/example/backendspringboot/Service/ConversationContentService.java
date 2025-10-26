package org.example.backendspringboot.Service;

import org.example.Dao.ConversationContentMapper;
import org.example.backendspringboot.Entity.ConversationContent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 对话内容服务层
 * 实现 conversation_content 表的消息记录的增删查改和条件查询
 */
@Service
public class ConversationContentService {

    @Autowired
    private ConversationContentMapper conversationContentMapper;

    /**
     * 新增一条对话内容（消息）记录
     * @param content 对话内容实体
     * @return 是否成功（影响行数 > 0）
     */
    public boolean addConversationContent(ConversationContent content) {
        return conversationContentMapper.insertConversationContent(content) > 0;
    }

    /**
     * 根据主键 message_id 删除消息记录
     * @param messageId 消息ID
     * @return 是否成功（影响行数 > 0）
     */
    public boolean deleteById(Long messageId) {
        return conversationContentMapper.deleteById(messageId) > 0;
    }

    /**
     * 更新消息记录（按 message_id 匹配）
     * @param content 对话内容实体，需包含 message_id
     * @return 是否成功（影响行数 > 0）
     */
    public boolean updateConversationContent(ConversationContent content) {
        return conversationContentMapper.updateConversationContent(content) > 0;
    }

    /**
     * 查询所有消息记录
     * @return 对话内容实体列表
     */
    public List<ConversationContent> getAllConversationContents() {
        return conversationContentMapper.selectAll();
    }

    /**
     * 根据主键 message_id 查询消息记录
     * @param messageId 消息ID
     * @return 对话内容实体
     */
    public ConversationContent getConversationContentById(Long messageId) {
        return conversationContentMapper.selectById(messageId);
    }

    /**
     * 动态条件查找，传入匹配列名和匹配值
     * @param column 匹配的列名（仅限 conversation_id, sender_type, sender_id, send_time, message_seq）
     * @param value 匹配的值
     * @return 对话内容实体列表
     */
    public List<ConversationContent> getConversationContentsByColumn(String column, Object value) {
        return conversationContentMapper.selectByColumn(column, value);
    }
}