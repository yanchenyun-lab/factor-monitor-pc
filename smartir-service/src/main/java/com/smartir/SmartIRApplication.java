package com.smartir;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication
@MapperScan("com.smartir.mapper")
@EnableDiscoveryClient
@EnableFeignClients(basePackages = "com.smartir.feign")
public class SmartIRApplication {
    public static void main(String[] args) {
        SpringApplication.run(SmartIRApplication.class, args);
    }

    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(10000); // 10s 连接超时
        factory.setReadTimeout(120000);   // 120s 读取超时 (回测计算量较大)
        return new RestTemplate(factory);
    }
}
