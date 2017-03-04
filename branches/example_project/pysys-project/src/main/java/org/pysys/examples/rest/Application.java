package org.pysys.examples.rest;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = {"org.pysys.examples.rest"})
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}