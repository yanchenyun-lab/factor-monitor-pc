package com.smartir.util;

import java.util.*;

/**
 * 资产与行业板块代码工具类
 */
public class AssetCodeHelper {

    // 默认大类资产代码列表
    public static final List<String> MAJOR_ASSET_CODES = new ArrayList<>(Arrays.asList(
            "H00300.CSI",
            "H00852.SH",
            "000832.CSI",
            "AU9999.SGE",
            "CBA00621.CS",
            "CBA00651.CS"
    ));

    // 默认行业板块代码列表
    public static final List<String> SECTOR_ASSET_CODES = new ArrayList<>(Arrays.asList(
            "881001.WI",
            "CI005919.WI",
            "CI005929.WI",
            "CI005925.WI",
            "CI005931.WI",
            "CI005921.WI"
    ));

    // 代码 -> 传统驼峰属性名映射 (用于兼容旧版前端字段)
    private static final Map<String, String> CODE_TO_CAMEL_MAP = new HashMap<>();
    private static final Map<String, String> CODE_TO_NAME_MAP = new HashMap<>();

    static {
        // 大类资产
        register("H00300.CSI", "h00300Csi", "300收益");
        register("H00852.SH", "h00852Sh", "中证1000全收益");
        register("000832.CSI", "idx000832Csi", "中证转债");
        register("AU9999.SGE", "au9999Sge", "SGE黄金9999");
        register("CBA00621.CS", "cba00621Cs", "中债-国债总财富(1-3年)指数");
        register("CBA00651.CS", "cba00651Cs", "中债-国债总财富(7-10年)指数");

        // 行业板块
        register("881001.WI", "wi881001", "万得全A");
        register("CI005919.WI", "ci005919Wi", "消费(风格.中信)");
        register("CI005929.WI", "ci005929Wi", "科技产业(中信)");
        register("CI005925.WI", "ci005925Wi", "周期产业(中信)");
        register("CI005931.WI", "ci005931Wi", "金融产业(中信)");
        register("CI005921.WI", "ci005921Wi", "稳定(风格.中信)");
    }

    private static void register(String code, String camel, String name) {
        CODE_TO_CAMEL_MAP.put(code, camel);
        CODE_TO_NAME_MAP.put(code, name);
    }

    public static String toCamelCase(String code) {
        if (code == null) return null;
        if (CODE_TO_CAMEL_MAP.containsKey(code)) {
            return CODE_TO_CAMEL_MAP.get(code);
        }
        // 动态规则: 去除标点并转驼峰
        String clean = code.replaceAll("[._-]", " ").trim();
        String[] parts = clean.split("\\s+");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            String p = parts[i].toLowerCase();
            if (i == 0) {
                if (Character.isDigit(p.charAt(0))) {
                    sb.append("idx").append(p);
                } else {
                    sb.append(p);
                }
            } else {
                sb.append(Character.toUpperCase(p.charAt(0))).append(p.substring(1));
            }
        }
        return sb.toString();
    }

    public static String getName(String code) {
        return CODE_TO_NAME_MAP.getOrDefault(code, code);
    }
}
