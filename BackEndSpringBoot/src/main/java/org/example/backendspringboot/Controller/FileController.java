package org.example.backendspringboot.Controller;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.net.URLDecoder;

@RestController
@RequestMapping("/uploads")
public class FileController {

    /**
     * 例如：/uploads/E:/AiWHU/data/8EC9-D8C2-D258-433B.pdf
     * 取出 PathVariable，直接作为本地路径（可适当限制安全）
     */
    @GetMapping("**")
    public ResponseEntity<Resource> getAnyFile(HttpServletRequest request) {
        // 取真实path部分：/uploads/E:/AiWHU/data/xxx.pdf ==> E:/AiWHU/data/xxx.pdf
        String servletPath = request.getRequestURI(); // eg. /uploads/E:/AiWHU/data/xxx.pdf
        String prefix = "/uploads/";
        int idx = servletPath.indexOf(prefix);
        if (idx < 0) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(null);
        }

        String localPath = servletPath.substring(idx + prefix.length());
        try {
            localPath = URLDecoder.decode(localPath, "UTF-8"); // 防止中文路径
        } catch (Exception e) {}

        File file = new File(localPath);
        if (!file.exists() || !file.isFile()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(null);
        }

        Resource resource = new FileSystemResource(file);

        MediaType contentType = MediaType.APPLICATION_OCTET_STREAM;
        String lower = localPath.toLowerCase();
        if (lower.endsWith(".pdf")) contentType = MediaType.APPLICATION_PDF;
        else if (lower.endsWith(".png")) contentType = MediaType.IMAGE_PNG;
        else if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) contentType = MediaType.IMAGE_JPEG;

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(contentType);
        headers.setContentDisposition(ContentDisposition.inline().filename(file.getName()).build());

        return ResponseEntity.ok().headers(headers).body(resource);
    }
}