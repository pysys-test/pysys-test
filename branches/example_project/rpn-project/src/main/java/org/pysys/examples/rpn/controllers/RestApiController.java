package org.pysys.examples.rpn.controllers;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.PropertySource;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
@PropertySource("application.properties")
public class RestApiController {

    public static final Logger logger = LoggerFactory.getLogger(RestApiController.class);

    @Value("${app.version}")
    private String version;

    @RequestMapping(value = "/getVersion", method = RequestMethod.GET)
    public ResponseEntity<?> printVersion() {
        logger.info("Received get request for version");
        return new ResponseEntity<String>(version, HttpStatus.OK);
    }
}
