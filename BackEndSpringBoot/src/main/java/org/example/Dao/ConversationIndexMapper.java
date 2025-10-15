package org.example.Dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.example.backendspringboot.Entity.ConversationIndex;
import java.util.List;

/**
 * 会话索引数据访问接口
 * 实现 conversation_index 表的基础增删查改操作及动态条件查找功能
 */
@Mapper
public interface ConversationIndexMapper {

    /**
     * 新增一条会话索引记录
     * @param index 会话索引实体
     * @return 影响的行数
     */
    int insertConversationIndex(ConversationIndex index);

    /**
     * 根据主键 conversation_id 删除会话记录
     * @param conversation_id 会话ID
     * @return 影响的行数
     */
    int deleteById(@Param("conversation_id") Long conversation_id);

    /**
     * 更新会话索引记录（按 conversation_id 匹配）
     * @param index 会话索引实体，需包含 conversation_id
     * @return 影响的行数
     */
    int updateConversationIndex(ConversationIndex index);

    /**
     * 查询所有会话索引记录
     * @return 会话索引实体列表
     */
    List<ConversationIndex> selectAll();

    /**
     * 根据主键 conversation_id 查询会话索引记录
     * @param conversation_id 会话ID
     * @return 会话索引实体
     */
    ConversationIndex selectById(@Param("conversation_id") Long conversation_id);

    /**
     * 动态条件查找，传入匹配列名和匹配值
     * @param column 匹配的列名
     * @param value 匹配的值
     * @return 会话索引实体列表
     */
    List<ConversationIndex> selectByColumn(@Param("column") String column, @Param("value") Object value);
}