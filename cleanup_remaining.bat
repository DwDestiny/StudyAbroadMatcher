@echo off
echo 清理剩余的被占用文件...

rem 删除日志文件（如果进程已停止）
if exist api_server.log (
    del /f api_server.log 2>nul
    if exist api_server.log (
        echo 日志文件仍被占用，请停止所有Python进程后手动删除 api_server.log
    ) else (
        echo 成功删除 api_server.log
    )
)

echo 清理完成！