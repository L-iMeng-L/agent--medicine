package org.example.backendspringboot.Controller;

import org.example.backendspringboot.Entity.*;
import org.example.backendspringboot.Service.ConversationContentService;
import org.example.backendspringboot.Service.ConversationIndexService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Controller;

import javax.annotation.PostConstruct;
import java.io.IOException;
import java.sql.Timestamp;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * ConversationController
 *
 * 对话系统的后端控制器，实现对会话和消息的增删查、websocket实时通信等功能。
 */
@RestController
@RequestMapping("/conversation")
public class ConversationController {

    @Autowired
    private ConversationContentService contentService;

    @Autowired
    private ConversationIndexService indexService;

    /**
     * 初始化会话：获取用户所有会话及消息列表
     * GET /conversation/init?userId={userId}
     *
     * @param userId 用户ID
     * @return List<ConversationMessage> 包含所有会话和消息
     *
     * 调用示例：
     * GET http://localhost:8080/conversation/init?userId=123
     */
    @GetMapping("/init")
    public List<ConversationMessage> getAllConversationsByUserId(@RequestParam("userId") Long userId) {
        List<ConversationIndex> indexes = indexService.getConversationIndexesByColumn("user_id", userId);
        List<ConversationMessage> result = new ArrayList<>();
        for (ConversationIndex idx : indexes) {
            List<ConversationContent> contents = contentService.getConversationContentsByColumn("conversation_id", idx.getConversation_id())
                    .stream()
                    .sorted(Comparator.comparing(ConversationContent::getSend_time))
                    .toList();
            for (ConversationContent c : contents) {
                ConversationMessage msg = mergeIndexContent(idx, c);
                result.add(msg);
            }
        }
        return result;
    }

    /**
     * 删除对话和所有消息
     * DELETE /conversation/delete?userId={userId}&conversationId={conversationId}
     *
     * @param userId 用户ID
     * @param conversationId 会话ID
     * @return boolean 是否删除成功
     *
     * 调用示例：
     * DELETE http://localhost:8080/conversation/delete?userId=123&conversationId=456
     */
    @DeleteMapping("/delete")
    public boolean deleteConversation(@RequestParam("userId") Long userId,
                                      @RequestParam("conversationId") Long conversationId) {
        List<ConversationContent> contents = contentService.getConversationContentsByColumn("conversation_id", conversationId);
        boolean contentDeleted = true;
        for (ConversationContent c : contents) {
            contentDeleted &= contentService.deleteById(c.getMessage_id());
        }
        ConversationIndex idx = indexService.getConversationIndexById(conversationId);
        boolean indexDeleted = false;
        if (idx != null && Objects.equals(idx.getUser_id(), userId)) {
            indexDeleted = indexService.deleteById(conversationId);
        }
        return contentDeleted && indexDeleted;
    }

    /**
     * 新增消息或新增对话（仅HTTP方式，WebSocket见下方）
     * POST /conversation/add
     *
     * @param message ConversationMessage（json体，包含会话与消息内容字段）
     * @return boolean 是否成功
     *
     * 调用示例：
     * POST http://localhost:8080/conversation/add
     * Body:
     * {
     *   "user_id": 123,
     *   "agent_id": 456,
     *   "sender_type": "user",
     *   "sender_id": 123,
     *   "content": "你好",
     *   "reference": "/upload/sample.pdf"
     * }
     */
    @PostMapping("/add")
    public boolean addConversationOrMessage(@RequestBody ConversationMessage message) {
        return handleMessageSave(message);
    }

    /**
     * 合并会话索引与消息内容为前端交互体
     */
    private ConversationMessage mergeIndexContent(ConversationIndex idx, ConversationContent c) {
        ConversationMessage msg = new ConversationMessage();
        msg.setConversation_id(idx.getConversation_id());
        msg.setUser_id(idx.getUser_id());
        msg.setAgent_id(idx.getAgent_id());
        msg.setStart_time(idx.getStart_time());
        msg.setLast_message_time(idx.getLast_message_time());
        msg.setRemark(idx.getRemark());
        msg.setSender_type(c.getSender_type());
        msg.setSender_id(c.getSender_id());
        msg.setSend_time(c.getSend_time());
        msg.setMessage_seq(c.getMessage_seq());
        msg.setContent(c.getContent());
        msg.setReference(c.getReference());
        return msg;
    }

    /**
     * 拆分ConversationMessage为索引和内容，自动处理新增会话、新增消息、更新last_message_time
     *
     * @param message 前端传的ConversationMessage对象
     * @return boolean 是否存储成功
     */
    private boolean handleMessageSave(ConversationMessage message) {
        Long conversationId = message.getConversation_id();
        Timestamp now = new Timestamp(System.currentTimeMillis());
        // 新增会话
        if (conversationId == null) {
            ConversationIndex idx = new ConversationIndex();
            idx.setUser_id(message.getUser_id());
            idx.setAgent_id(message.getAgent_id());
            idx.setStart_time(now);
            idx.setLast_message_time(now);
            idx.setRemark(message.getRemark());
            indexService.addConversationIndex(idx);
            List<ConversationIndex> userIndexes = indexService.getConversationIndexesByColumn("user_id", message.getUser_id());
            Optional<ConversationIndex> newestIdx = userIndexes.stream().max(Comparator.comparing(ConversationIndex::getStart_time));
            if (newestIdx.isPresent()) {
                conversationId = newestIdx.get().getConversation_id();
            } else {
                return false;
            }
        }
        // 新增消息
        ConversationContent content = new ConversationContent();
        content.setConversation_id(conversationId);
        content.setSender_type(message.getSender_type());
        content.setSender_id(message.getSender_id());
        content.setSend_time(now);
        List<ConversationContent> existingMsgs = contentService.getConversationContentsByColumn("conversation_id", conversationId);
        int seq = existingMsgs.stream().mapToInt(m -> m.getMessage_seq() != null ? m.getMessage_seq() : 0).max().orElse(0) + 1;
        content.setMessage_seq(seq);
        content.setContent(message.getContent());
        content.setReference(message.getReference());
        boolean contentSaved = contentService.addConversationContent(content);
        ConversationIndex idx = indexService.getConversationIndexById(conversationId);
        if (idx != null) {
            idx.setLast_message_time(now);
            indexService.updateConversationIndex(idx);
        }
        return contentSaved;
    }

    // ==== WebSocket 全双工部分 ====

//    /**
//     * WebSocket配置入口（建议通过Spring配置类实现，此处为演示）
//     */
//    @Controller
//    public static class ConversationWebSocketConfig {
//        @Autowired
//        private ConversationWebSocketHandler handler;
//        @PostConstruct
//        public void init() {/* WebSocket注册逻辑 */}
//    }

//    /**
//     * WebSocket消息处理器
//     * 实现：
//     * 1. 前端发ConversationMessage，存储消息/会话
//     * 2. 发给python FastAPI（调用HTTP接口，传递内容和reference路径）
//     * 3. 等待python返回内容（字符串）
//     * 4. 存储python回复到数据库
//     * 5. 回复前端（ConversationMessage结构）
//     */
//    @Component
//    public static class ConversationWebSocketHandler extends TextWebSocketHandler {
//
//        @Autowired
//        private ConversationContentService contentService;
//        @Autowired
//        private ConversationIndexService indexService;
//
//        // 管理WebSocket连接（userId -> session）
//        private static final Map<Long, WebSocketSession> sessionMap = new ConcurrentHashMap<>();
//
//        @Override
//        public void afterConnectionEstablished(WebSocketSession session) {
//            Long userId = getUserIdFromSession(session);
//            if (userId != null) {
//                sessionMap.put(userId, session);
//            }
//        }
//
//        @Override
//        protected void handleTextMessage(WebSocketSession session, TextMessage textMessage) throws IOException {
//            // 1. 解析前端消息
//            ConversationMessage msg = parseMessage(textMessage.getPayload());
//            // 2. 存储消息/会话
//            if (msg != null) {
//                handleMessageSave(msg);
//            }
//            else System.out.println("[WARNING]Empty input Message!");
//            // 3. 调用FastAPI（传递内容、reference等字段，可用RestTemplate/WebClient实现）
//            String pythonReply = callPythonFastApi(msg);
//            // 4. 构造agent回复ConversationMessage并存储
//            ConversationMessage replyMsg = buildReplyMessage(msg, pythonReply);
//            handleMessageSave(replyMsg);
//            // 5. 推送回复给前端
//            session.sendMessage(new TextMessage(serializeMessage(replyMsg)));
//        }
//
//        /**
//         * 拆分ConversationMessage为索引和内容，自动处理新增会话、新增消息、更新last_message_time
//         *
//         * @param message 前端传的ConversationMessage对象
//         * @return boolean 是否存储成功
//         */
//        private boolean handleMessageSave(ConversationMessage message) {
//            Long conversationId = message.getConversation_id();
//            Timestamp now = new Timestamp(System.currentTimeMillis());
//            // 新增会话
//            if (conversationId == null) {
//                ConversationIndex idx = new ConversationIndex();
//                idx.setUser_id(message.getUser_id());
//                idx.setAgent_id(message.getAgent_id());
//                idx.setStart_time(now);
//                idx.setLast_message_time(now);
//                idx.setRemark(message.getRemark());
//                indexService.addConversationIndex(idx);
//                List<ConversationIndex> userIndexes = indexService.getConversationIndexesByColumn("user_id", message.getUser_id());
//                Optional<ConversationIndex> newestIdx = userIndexes.stream().max(Comparator.comparing(ConversationIndex::getStart_time));
//                if (newestIdx.isPresent()) {
//                    conversationId = newestIdx.get().getConversation_id();
//                } else {
//                    return false;
//                }
//            }
//            // 新增消息
//            ConversationContent content = new ConversationContent();
//            content.setConversation_id(conversationId);
//            content.setSender_type(message.getSender_type());
//            content.setSender_id(message.getSender_id());
//            content.setSend_time(now);
//            List<ConversationContent> existingMsgs = contentService.getConversationContentsByColumn("conversation_id", conversationId);
//            int seq = existingMsgs.stream().mapToInt(m -> m.getMessage_seq() != null ? m.getMessage_seq() : 0).max().orElse(0) + 1;
//            content.setMessage_seq(seq);
//            content.setContent(message.getContent());
//            content.setReference(message.getReference());
//            boolean contentSaved = contentService.addConversationContent(content);
//            ConversationIndex idx = indexService.getConversationIndexById(conversationId);
//            if (idx != null) {
//                idx.setLast_message_time(now);
//                indexService.updateConversationIndex(idx);
//            }
//            return contentSaved;
//        }
//
//
//        @Override
//        public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
//            Long userId = getUserIdFromSession(session);
//            if (userId != null) {
//                sessionMap.remove(userId);
//            }
//        }
//
//        // === 工具方法 ===
//
//        /**
//         * 从session属性或URL参数获取userId
//         */
//        private Long getUserIdFromSession(WebSocketSession session) {
//            // TODO: 实际项目可从session属性或握手参数获取
//            return null;
//        }
//
//        /**
//         * 反序列化json为ConversationMessage
//         */
//        private ConversationMessage parseMessage(String json) {
//            // TODO: 使用Jackson或Gson实现
//            return null;
//        }
//
//        /**
//         * 序列化ConversationMessage为json
//         */
//        private String serializeMessage(ConversationMessage msg) {
//            // TODO: 使用Jackson或Gson实现
//            return "";
//        }
//
//        /**
//         * 调用Python FastAPI，传递消息内容和附件路径
//         */
//        private String callPythonFastApi(ConversationMessage msg) {
//            // TODO: 用RestTemplate/WebClient调用FastAPI接口
//            // 传递msg.getContent(), msg.getReference等字段
//            // FastAPI返回字符串内容
//            return "Python回复内容";
//        }
//
//        /**
//         * 构造agent（AI）回复的ConversationMessage对象
//         */
//        private ConversationMessage buildReplyMessage(ConversationMessage msg, String pythonReply) {
//            ConversationMessage reply = new ConversationMessage();
//            reply.setConversation_id(msg.getConversation_id());
//            reply.setUser_id(msg.getUser_id());
//            reply.setAgent_id(msg.getAgent_id());
//            reply.setStart_time(msg.getStart_time());
//            reply.setLast_message_time(new Timestamp(System.currentTimeMillis()));
//            reply.setRemark(msg.getRemark());
//            reply.setSender_type("agent");
//            reply.setSender_id(msg.getAgent_id());
//            reply.setSend_time(new Timestamp(System.currentTimeMillis()));
//            reply.setMessage_seq(msg.getMessage_seq() + 1);
//            reply.setContent(pythonReply);
//            reply.setReference(null); // agent无附件
//            return reply;
//        }
//    }
}

/*
==============================================
参数说明及功能解释
==============================================

1. ConversationMessage: 前后端交互体，包含会话信息和消息内容，字段见Entity定义。
2. userId: 用户ID，唯一标识用户。
3. conversationId: 会话ID，唯一标识会话。
4. content: 消息文本内容。
5. reference: 附件路径（如文件上传后返回的URL或本地路径）。

==============================================
调用示例模板
==============================================

1. 初始化会话消息列表
GET /conversation/init?userId={userId}
返回：List<ConversationMessage>

2. 删除会话及消息
DELETE /conversation/delete?userId={userId}&conversationId={conversationId}
返回：true/false

3. 新增消息/新增会话
POST /conversation/add
Body:
{
  "user_id": 123,
  "agent_id": 456,
  "sender_type": "user",
  "sender_id": 123,
  "content": "你好",
  "reference": "/upload/sample.pdf"
}
返回：true/false

4. WebSocket消息交互
- 建立ws连接: ws://localhost:8080/ws/conversation?userId=123
- 前端发送ConversationMessage(json)，后端存储，转发给Python，收到回复后推送给前端
- 附件路径(reference)需保证数据库同步和接口一致

==============================================
*/