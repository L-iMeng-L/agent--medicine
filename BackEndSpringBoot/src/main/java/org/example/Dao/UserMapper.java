package org.example.Dao;
import org.apache.ibatis.annotations.Mapper;
import org.example.backendspringboot.UserLogin;
import java.util.List;
@Mapper
public interface UserMapper {
    List<UserLogin> selectAllUsers();
}
