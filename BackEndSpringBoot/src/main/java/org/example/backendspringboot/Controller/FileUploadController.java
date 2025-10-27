package org.example.backendspringboot.Controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.http.ResponseEntity;

import java.io.File;
import java.io.IOException;
import java.sql.Timestamp;
import java.util.Locale;
import java.util.UUID;

@RestController
@RequestMapping("/file")
public class FileUploadController {

    // 文件存储根目录，可通过 application.properties 配置
    @Value("${file.upload-dir:/data/upload}")
    private String uploadDir;

    /**
     * 上传文件并返回重命名后的路径（仅支持 txt, pdf, 图片文件）
     * @param file 前端上传的文件
     * @return 文件路径/URL字符串
     */
    @PostMapping("/upload")
    public ResponseEntity<String> upload(@RequestParam("file") MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body("文件不能为空");
        }

        // 检查类型
        String originalFilename = file.getOriginalFilename();
        String ext = "";
        if (originalFilename != null && originalFilename.contains(".")) {
            ext = originalFilename.substring(originalFilename.lastIndexOf(".")).toLowerCase(Locale.ROOT);
        }
        // 支持的类型：txt, pdf, 图片
        boolean isAllowed = ext.equals(".txt") || ext.equals(".pdf")
                || ext.equals(".png") || ext.equals(".jpg") || ext.equals(".jpeg") || ext.equals(".gif") || ext.equals(".bmp");
        if (!isAllowed) {
            return ResponseEntity.badRequest().body("不支持的文件类型: " + ext);
        }

        // 随机16位十六进制名 AB12-CD34-EF56-7890
        String randomHex = UUID.randomUUID().toString().replaceAll("-", "").substring(0, 16).toUpperCase();
        String hexName = randomHex.substring(0, 4) + "-" +
                randomHex.substring(4, 8) + "-" +
                randomHex.substring(8, 12) + "-" +
                randomHex.substring(12, 16);

        String newName = hexName + ext;
        File dest = new File(uploadDir, newName);
        dest.getParentFile().mkdirs();
        file.transferTo(dest);

        String path = dest.getAbsolutePath();

        // 可选：入库 attachment 表（略）

        // 返回文件路径（可前端 reference 字段直接引用）
        return ResponseEntity.ok(path);
    }
}