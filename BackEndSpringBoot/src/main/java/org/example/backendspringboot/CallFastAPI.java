package org.example.backendspringboot;

public class CallFastAPI {
    public Object process(String type, Object requestData) {
        FastAPIClient client = FastAPIFactory.getClient(type);
        return client.call(requestData);
    }
}
