package org.example.backendspringboot.Service;

import org.example.Dao.ConversationIndexMapper;
import org.example.backendspringboot.Entity.ConversationIndex;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 会话索引服务层
 * 实现会话索引的查询、添加、删除和更新等功能
 */
@Service
public class ConversationIndexService {

    @Autowired
    private ConversationIndexMapper conversationIndexMapper;

    /**
     * 新增一条会话索引记录
     * @param index 会话索引实体
     * @return 是否成功（影响行数 > 0）
     */
    public boolean addConversationIndex(ConversationIndex index) {
        return conversationIndexMapper.insertConversationIndex(index) > 0;
    }

    /**
     * 根据主键 conversation_id 删除会话记录
     * @param conversationId 会话ID
     * @return 是否成功（影响行数 > 0）
     */
    public boolean deleteById(Long conversationId) {
        return conversationIndexMapper.deleteById(conversationId) > 0;
    }

    /**
     * 更新会话索引记录（按 conversation_id 匹配）
     * @param index 会话索引实体，需包含 conversation_id
     * @return 是否成功（影响行数 > 0）
     */
    public boolean updateConversationIndex(ConversationIndex index) {
        return conversationIndexMapper.updateConversationIndex(index) > 0;
    }

    /**
     * 查询所有会话索引记录
     * @return 会话索引实体列表
     */
    public List<ConversationIndex> getAllConversationIndexes() {
        return conversationIndexMapper.selectAll();
    }

    /**
     * 根据主键 conversation_id 查询会话索引记录
     * @param conversationId 会话ID
     * @return 会话索引实体
     */
    public ConversationIndex getConversationIndexById(Long conversationId) {
        return conversationIndexMapper.selectById(conversationId);
    }

    /**
     * 动态条件查找，传入匹配列名和匹配值
     * @param column 匹配的列名（如 user_id, agent_id, start_time, last_message_time）
     * @param value 匹配的值
     * @return 会话索引实体列表
     */
    public List<ConversationIndex> getConversationIndexesByColumn(String column, Object value) {
        return conversationIndexMapper.selectByColumn(column, value);
    }
}