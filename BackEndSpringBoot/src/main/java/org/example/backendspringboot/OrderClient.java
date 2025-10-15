package org.example.backendspringboot;

public class OrderClient implements FastAPIClient {
    @Override
    public Object call(Object requestData) {
        // 调用FastAPI处理订单的逻辑
        return true;
    }
}