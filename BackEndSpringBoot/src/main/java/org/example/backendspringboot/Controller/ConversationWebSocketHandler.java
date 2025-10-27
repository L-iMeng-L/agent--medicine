package org.example.backendspringboot.Controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.NonNull;
import org.example.backendspringboot.Entity.ConversationMessage;
import org.example.backendspringboot.Entity.ConversationIndex;
import org.example.backendspringboot.Entity.ConversationContent;
import org.example.backendspringboot.Service.ConversationContentService;
import org.example.backendspringboot.Service.ConversationIndexService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.sql.Timestamp;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class ConversationWebSocketHandler extends TextWebSocketHandler {

    @Autowired
    private ConversationContentService contentService;
    @Autowired
    private ConversationIndexService indexService;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final Map<Long, WebSocketSession> sessionMap = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        Long userId = extractUserId(session);
        if (userId != null) sessionMap.put(userId, session);
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage textMessage) throws Exception {
        ConversationMessage msg = objectMapper.readValue(textMessage.getPayload(), ConversationMessage.class);

        // 保存到数据库（创建新会话或追加消息）
        Long convId = saveMessageToDb(msg);
        msg.setConversation_id(convId);

        // 这里模拟 Python FastAPI 回复内容
        String pythonReply = "这是AI回复：" + msg.getContent(); // TODO: 调用实际 Python API
        ConversationMessage replyMsg = buildAgentReplyMessage(msg, pythonReply);
        saveMessageToDb(replyMsg);

        // 推送 agent 回复到前端
        session.sendMessage(new TextMessage(objectMapper.writeValueAsString(replyMsg)));
    }

    @Override
    public void afterConnectionClosed(@NonNull WebSocketSession session, @NonNull CloseStatus status) {
        Long userId = extractUserId(session);
        if (userId != null) sessionMap.remove(userId);
    }

    // ---- 辅助方法 ----

    private Long extractUserId(WebSocketSession session) {
        try {
            String query = Objects.requireNonNull(session.getUri()).getQuery(); // userId=123
            if (query != null) {
                for (String kv : query.split("&")) {
                    String[] a = kv.split("=", 2);
                    if (a.length == 2 && "userId".equals(a[0])) return Long.valueOf(a[1]);
                }
            }
        } catch (Exception ignored) {}
        return null;
    }

    private Long saveMessageToDb(ConversationMessage message) {
        Long conversationId = message.getConversation_id();
        Timestamp now = new Timestamp(System.currentTimeMillis());
        if (conversationId == null) {
            ConversationIndex idx = new ConversationIndex();
            idx.setUser_id(message.getUser_id());
            idx.setAgent_id(message.getAgent_id());
            idx.setStart_time(now);
            idx.setLast_message_time(now);
            idx.setRemark(message.getRemark());
            indexService.addConversationIndex(idx);
            List<ConversationIndex> userIndexes = indexService.getConversationIndexesByColumn("user_id", message.getUser_id());
            Optional<ConversationIndex> newest = userIndexes.stream().max(Comparator.comparing(ConversationIndex::getStart_time));
            conversationId = newest.map(ConversationIndex::getConversation_id).orElse(null);
        }
        ConversationContent content = new ConversationContent();
        content.setConversation_id(conversationId);
        content.setSender_type(message.getSender_type());
        content.setSender_id(message.getSender_id());
        content.setSend_time(now);
        List<ConversationContent> existing = contentService.getConversationContentsByColumn("conversation_id", conversationId);
        int seq = existing.stream().mapToInt(m -> m.getMessage_seq() != null ? m.getMessage_seq() : 0).max().orElse(0) + 1;
        content.setMessage_seq(seq);
        content.setContent(message.getContent());
        content.setReference(message.getReference());
        contentService.addConversationContent(content);
        ConversationIndex idxToUpdate = indexService.getConversationIndexById(conversationId);
        if (idxToUpdate != null) {
            idxToUpdate.setLast_message_time(now);
            indexService.updateConversationIndex(idxToUpdate);
        }
        return conversationId;
    }

    private ConversationMessage buildAgentReplyMessage(ConversationMessage req, String replyText) {
        ConversationMessage reply = new ConversationMessage();
        reply.setConversation_id(req.getConversation_id());
        reply.setUser_id(req.getUser_id());
        reply.setAgent_id(req.getAgent_id());
        reply.setStart_time(req.getStart_time());
        reply.setLast_message_time(new Timestamp(System.currentTimeMillis()));
        reply.setRemark(req.getRemark());
        reply.setSender_type("agent");
        reply.setSender_id(req.getAgent_id());
        reply.setSend_time(new Timestamp(System.currentTimeMillis()));
        reply.setMessage_seq((req.getMessage_seq() != null ? req.getMessage_seq() : 0) + 1);
        reply.setContent(replyText);
        reply.setReference(null);
        return reply;
    }
}