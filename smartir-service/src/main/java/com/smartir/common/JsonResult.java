package com.smartir.common;

import lombok.Data;
import java.io.Serializable;

/**
 * 统一 API 响应实体封装
 * 参考 smart-invest-research 规范
 */
@Data
public class JsonResult<T> implements Serializable {

    public static final Integer EXCEPTION_CODE_500 = 500;
    public static final Integer EXCEPTION_CODE_400 = 400;
    public static final Integer SUCCESS_CODE_200 = 200;

    public static final String EXCEPTION_MESSAGE_500 = "Server Internal Error";
    public static final String EXCEPTION_MESSAGE_400 = "Bad request";

    private static final long serialVersionUID = 1L;

    private Boolean status;
    private String message;
    private Integer code;
    private T data;

    public JsonResult() {
    }

    public JsonResult(Boolean status, String message, Integer code, T data) {
        this.status = status;
        this.message = message;
        this.code = code;
        this.data = data;
    }

    public static <T> JsonResult<T> success(T data) {
        return new JsonResult<>(true, "success", SUCCESS_CODE_200, data);
    }

    public static <T> JsonResult<T> success(T data, String message) {
        return new JsonResult<>(true, message, SUCCESS_CODE_200, data);
    }

    public static <T> JsonResult<T> error(String message) {
        return new JsonResult<>(false, message, EXCEPTION_CODE_500, null);
    }

    public static <T> JsonResult<T> error(Integer code, String message) {
        return new JsonResult<>(false, message, code, null);
    }
}
