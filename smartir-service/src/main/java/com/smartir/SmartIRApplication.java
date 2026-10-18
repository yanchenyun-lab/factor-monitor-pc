package com.smartir;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.smartir.mapper")
public class SmartIRApplication {
    public static void main(String[] args) {
        SpringApplication.run(SmartIRApplication.class, args);
    }
}
