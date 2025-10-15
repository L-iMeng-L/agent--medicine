package org.example.Dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.example.backendspringboot.Entity.ConversationContent;
import java.util.List;

/**
 * 对话内容数据访问接口
 * 实现 conversation_content 表的基础增删查改操作及动态条件查找功能
 */
@Mapper
public interface ConversationContentMapper {

    /**
     * 新增一条对话内容（消息）记录
     * @param content 对话内容实体
     * @return 影响的行数
     */
    int insertConversationContent(ConversationContent content);

    /**
     * 根据主键 message_id 删除消息记录
     * @param message_id 消息ID
     * @return 影响的行数
     */
    int deleteById(@Param("message_id") Long message_id);

    /**
     * 更新消息记录（按 message_id 匹配）
     * @param content 对话内容实体，需包含 message_id
     * @return 影响的行数
     */
    int updateConversationContent(ConversationContent content);

    /**
     * 查询所有消息记录
     * @return 对话内容实体列表
     */
    List<ConversationContent> selectAll();

    /**
     * 根据主键 message_id 查询消息记录
     * @param message_id 消息ID
     * @return 对话内容实体
     */
    ConversationContent selectById(@Param("message_id") Long message_id);

    /**
     * 动态条件查找，传入匹配列名和匹配值
     * @param column 匹配的列名
     * @param value 匹配的值
     * @return 对话内容实体列表
     */
    List<ConversationContent> selectByColumn(@Param("column") String column, @Param("value") Object value);
}