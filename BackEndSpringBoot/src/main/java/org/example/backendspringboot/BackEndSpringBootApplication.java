package org.example.backendspringboot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.mybatis.spring.annotation.MapperScan;
@SpringBootApplication
@MapperScan("org.example.Dao")  // 扫描 Mapper 接口
public class BackEndSpringBootApplication {

    public static void main(String[] args) {
        SpringApplication.run(BackEndSpringBootApplication.class, args);
    }
        
}
