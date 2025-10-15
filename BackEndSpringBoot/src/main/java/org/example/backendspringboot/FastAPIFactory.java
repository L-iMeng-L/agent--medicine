package org.example.backendspringboot;

public class FastAPIFactory {
    public static FastAPIClient getClient(String type) {
        switch (type) {
            case "user":
                return new UserInfoClient();
            case "order":
                return new OrderClient();
            default:
                throw new IllegalArgumentException("未知类型: " + type);
        }
    }
}