# AI WHU Health 后端接口文档

本项目提供 AI+用户健康智能管理的后端 HTTP 与 WebSocket 接口，涵盖用户账号、健康档案、对话系统、文件上传以及用户基础信息管理等模块。

更新提示
- 自 2025-11 起，用户注册与登录接口的返回值由 boolean 改为 Long：
    - 成功：返回数据库中的 user_id
    - 失败：返回 -1

基础信息
- Base URL（开发环境）：http://localhost:8080
- 数据格式：除特别说明外，所有请求与响应均采用 application/json
- 鉴权：当前示例未启用 Token 鉴权。请前端在登录成功后自行持久化保存 user_id，后续接口以 user_id 作为关联键。

目录
- 用户接口（UserController）
- 健康档案接口（UserHealthController）
- 对话接口（HTTP）（ConversationController）
- 对话接口（WebSocket）（ConversationWebSocketHandler）
- 文件上传接口（FileUploadController）
- 用户基础信息接口（UserInfoController）
- 实体与示例
- 常见约定与错误处理
- 配置说明

---------------------------------------
用户接口（/user）
文件：UserController.java

1) 获取所有用户
- GET /user/all
- 响应：UserLogin[]（用户列表）

示例
curl http://localhost:8080/user/all

2) 用户注册（返回 user_id）
- POST /user/register
- Query 参数：
    - username: string
    - password: string
- 响应：number
    - 成功：返回新注册用户的 user_id
    - 失败：-1（用户名已存在等）

示例
curl -X POST "http://localhost:8080/user/register?username=jay&password=123456"

3) 用户登录（返回 user_id）
- POST /user/login
- Query 参数：
    - username: string
    - password: string
- 响应：number
    - 成功：返回该用户的 user_id
    - 失败：-1（用户不存在或密码错误）

示例
curl -X POST "http://localhost:8080/user/login?username=jay&password=123456"

4) 注销用户（按用户名删除）
- DELETE /user/delete
- Query 参数：
    - username: string
- 响应：boolean

示例
curl -X DELETE "http://localhost:8080/user/delete?username=jay"

5) 修改密码
- PUT /user/password
- Query 参数：
    - username: string
    - newPassword: string
- 响应：boolean

示例
curl -X PUT "http://localhost:8080/user/password?username=jay&newPassword=654321"

6) 修改用户名
- PUT /user/username
- Query 参数：
    - oldUsername: string
    - newUsername: string
- 响应：boolean

示例
curl -X PUT "http://localhost:8080/user/username?oldUsername=jay&newUsername=jay_new"

说明
- 密码存储采用 SHA-256 + username 作为 salt + 1024 次迭代。
- 注册/登录统一返回 user_id（Long）；请前端保存以用于后续所有业务接口。


---------------------------------------
健康档案接口（/user-health）
文件：UserHealthController.java

1) 查询健康记录（按日期降序）
- GET /user-health/records
- Query 参数：
    - uid: number（用户 user_id）
- 响应：UserHealthRecord[]

示例
curl "http://localhost:8080/user-health/records?uid=123"

2) 新增健康记录
- POST /user-health/record
- Body：UserHealthRecord（JSON）
- 响应：boolean

示例
curl -X POST http://localhost:8080/user-health/record \
-H "Content-Type: application/json" \
-d '{
"user_id": 123,
"height_cm": 170,
"weight_kg": 65,
"bmi": "22.49",
"date": "2025-11-03T12:00:00Z"
}'

3) 清空用户健康记录
- DELETE /user-health/records
- Query 参数：
    - uid: number
- 响应：boolean

示例
curl -X DELETE "http://localhost:8080/user-health/records?uid=123"


---------------------------------------
对话接口（HTTP）（/conversation）
文件：ConversationController.java

1) 初始化（获取用户所有会话及消息）
- GET /conversation/init
- Query 参数：
    - userId: number
- 响应：ConversationMessage[]（按各会话内 send_time 升序；前端可自行整体排序）

示例
curl "http://localhost:8080/conversation/init?userId=123"

2) 删除会话（及其所有消息）
- DELETE /conversation/delete
- Query 参数：
    - userId: number
    - conversationId: number
- 响应：boolean

示例
curl -X DELETE "http://localhost:8080/conversation/delete?userId=123&conversationId=456"

3) 新增消息 / 新建会话（HTTP）
- POST /conversation/add
- Body：ConversationMessage（JSON）
    - 当 body.conversation_id 为空时自动创建会话
- 响应：boolean（是否保存成功）

示例
curl -X POST http://localhost:8080/conversation/add \
-H "Content-Type: application/json" \
-d '{
"user_id": 123,
"agent_id": 1,
"sender_type": "user",
"sender_id": 123,
"content": "你好，今天步数 8000",
"reference": "/data/upload/ABCD-1234-EF56-7890.png"
}'


---------------------------------------
对话接口（WebSocket）
文件：ConversationWebSocketHandler.java

- 连接地址：ws://localhost:8080/ws/conversation?userId={userId}
- 客户端需在 URL 参数中传入已登录用户的 userId
- 消息协议：JSON，结构同 ConversationMessage（见“实体与示例”）

收发流程
1) 客户端发送用户消息（可不带 conversation_id 以创建新会话）
2) 服务端保存消息，必要时创建会话并回填 conversation_id
3) 服务端调用（或模拟）Python FastAPI 获取 AI 回复（当前示例中为模拟字符串）
4) 服务端保存 AI 回复并推送给客户端（同 JSON 结构）

示例（JS）
const ws = new WebSocket("ws://localhost:8080/ws/conversation?userId=123");
ws.onopen = () => {
ws.send(JSON.stringify({
conversation_id: null,
user_id: 123,
agent_id: 1,
sender_type: "user",
sender_id: 123,
content: "请根据我的BMI给出饮食建议",
reference: null
}));
};
ws.onmessage = (ev) => {
const reply = JSON.parse(ev.data); // ConversationMessage
console.log("AI回复:", reply);
};


---------------------------------------
文件上传接口（/file）
文件：FileUploadController.java

1) 上传文件
- POST /file/upload
- Form-Data:
    - file: MultipartFile
- 响应：string（服务器保存后的绝对路径）

约束
- 允许类型：.txt, .pdf, .png, .jpg, .jpeg, .gif, .bmp
- 存储目录：由 application.properties 中 file.upload-dir 指定，默认 /data/upload
- 命名规则：随机 16 位十六进制，格式 AB12-CD34-EF56-7890.ext
- 前端预览：通常将绝对路径的文件名部分映射到静态 URL（例如 /uploads/{filename}）

示例（cURL）
curl -X POST http://localhost:8080/file/upload \
-F "file=@/path/to/local/image.png"


---------------------------------------
用户基础信息接口（/user-info）
文件：UserInfoController.java

1) 查询用户基础信息
- GET /user-info/{userId}
- 路径参数：
    - userId: number
- 响应：UserInformation

示例
curl http://localhost:8080/user-info/123

2) 新增用户基础信息
- POST /user-info
- Body：UserInformation（JSON）
- 响应：boolean

示例
curl -X POST http://localhost:8080/user-info \
-H "Content-Type: application/json" \
-d '{
"user_id": 123,
"birth_date": "2000-01-01",
"phone": "12345678901",
"email": "test@example.com",
"name": "张三"
}'

3) 更新用户基础信息（按 info_id）
- PUT /user-info
- Body：UserInformation（包含 info_id）
- 响应：boolean

示例
curl -X PUT http://localhost:8080/user-info \
-H "Content-Type: application/json" \
-d '{
"info_id": 1,
"user_id": 123,
"birth_date": "2000-01-01",
"phone": "12345678901",
"email": "new@example.com",
"name": "张三"
}'

4) 删除用户基础信息（按 info_id）
- DELETE /user-info/{infoId}
- 路径参数：
    - infoId: number
- 响应：boolean

示例
curl -X DELETE http://localhost:8080/user-info/1

5) 查询全部用户基础信息
- GET /user-info/all
- 响应：UserInformation[]

示例
curl http://localhost:8080/user-info/all


---------------------------------------
实体与示例

1) ConversationMessage（对话交互体）
   {
   "conversation_id": 456,         // 可为空（创建新会话时）
   "user_id": 123,                  // 必填
   "agent_id": 1,                   // 可为空
   "start_time": "2025-11-03T12:00:00Z",
   "last_message_time": "2025-11-03T12:01:00Z",
   "remark": "string|nullable",
   "sender_type": "user|agent",
   "sender_id": 123,
   "send_time": "2025-11-03T12:00:30Z",
   "message_seq": 1,
   "content": "消息文本",
   "reference": "/data/upload/ABCD-1234-EF56-7890.png" // 附件路径，可为空
   }

2) UserHealthRecord（健康档案）
   {
   "record_id": 1,
   "user_id": 123,
   "height_cm": 170,
   "weight_kg": 65,
   "bmi": "22.49",
   "date": "2025-11-03T12:00:00Z"
   }

3) UserInformation（用户基础信息）
   {
   "info_id": 1,
   "user_id": 123,
   "birth_date": "2000-01-01",
   "phone": "12345678901",
   "email": "test@example.com",
   "name": "张三"
   }

4) UserLogin（账号实体，示例字段）
   {
   "user_id": 123,
   "username": "jay",
   "password": "sha256-hash-hex"
   }


---------------------------------------
常见约定与错误处理
- 登录/注册成功返回 user_id（Long），失败返回 -1。前端需据此判断成功与否，并在成功后持久化 user_id。
- 其他大多数写操作返回 boolean；true 表示操作成功，false 表示失败（如资源不存在、唯一性冲突、数据库写入失败等）。
- 文件上传的类型校验失败或空文件会返回 HTTP 400（Bad Request）与错误信息字符串。
- 对话的消息顺序：
    - HTTP 初始化接口按会话内 send_time 升序返回；前端可自行聚合并排序。
    - WebSocket 收到客户端消息后会立即持久化，并推送模拟的 AI 回复（当前示例）。生产中应替换为真实的 Python 服务调用。

安全建议
- 生产环境请加入鉴权（如 JWT），所有接口从 Token 中解析 user_id，杜绝前端可控的 userId/uid 直传。
- 上传目录应配置访问控制与病毒扫描；对外静态映射仅暴露需要的只读路径（如 /uploads/**）。

---------------------------------------
配置说明

application.properties（示例）
# 文件上传目录（默认 /data/upload）
file.upload-dir=/data/upload

静态资源映射（供前端预览）
- 建议将上传后的文件名映射为 /uploads/{filename}，前端仅暴露 /uploads/** 静态路径而不暴露真实磁盘路径。
- 若使用 Spring Boot 静态资源，可通过 WebMvcConfigurer 添加映射：
  registry.addResourceHandler("/uploads/**")
  .addResourceLocations("file:/data/upload/");

数据库约定
- users.user_id 为自增主键；MyBatis insert 使用 useGeneratedKeys 回填至实体。
- 其他表请确保与 Entity 定义一致（包括主键、自增与外键关系）。

---------------------------------------
前端集成要点
- 登录/注册后保存后端返回的 user_id（非用户名），后续调用 /user-health、/conversation 等接口只需传 user_id。
- WebSocket 连接参数 userId 必须使用已登录的 user_id：ws://host:8080/ws/conversation?userId={uid}
- 文件上传返回服务器绝对路径；前端可取文件名部分并拼接 /uploads/{filename} 进行展示。

如需补充 Swagger/OpenAPI、错误码规范或分页查询等，请提出具体需求。