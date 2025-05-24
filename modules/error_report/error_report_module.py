"""
错误报告生成模块 - 基于日本障害報告書标准

该模块实现了自动化的系统错误日志分析和标准日本风格障害报告书生成功能。
支持解析常见Java系统日志格式（Log4j、Logback等），并生成符合日本IT行业标准的障害报告书。

作者: Manus AI
日期: 2025-05-23
"""

import os
import re
import json
import logging
import datetime
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class LogFormat(Enum):
    """日志格式枚举"""
    LOG4J = "LOG4J"
    LOGBACK = "LOGBACK"
    JUL = "JUL"  # Java Util Logging
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

@dataclass
class LogEntry:
    """日志条目类"""
    timestamp: datetime.datetime
    level: LogLevel
    logger_name: str
    message: str
    exception: Optional[str] = None
    thread: Optional[str] = None
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    line_number: Optional[int] = None
    raw_line: str = ""
    
    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.level.value} {self.logger_name} - {self.message}"

@dataclass
class ErrorEvent:
    """错误事件类，表示一个完整的错误事件"""
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    error_type: str = "未知错误"
    error_message: str = ""
    affected_components: List[str] = field(default_factory=list)
    root_cause: str = "原因分析中"
    impact: str = "影响范围分析中"
    resolution: str = "解决方案分析中"
    related_logs: List[LogEntry] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[datetime.timedelta]:
        """计算错误持续时间"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None
    
    def __str__(self) -> str:
        duration_str = f", 持续时间: {self.duration}" if self.duration else ""
        return f"错误事件: {self.error_type} ({self.start_time}{duration_str})"

@dataclass
class ErrorReport:
    """错误报告类，表示一份完整的障害报告书"""
    title: str = "システム障害報告書"
    overview: str = ""
    error_start_time: Optional[datetime.datetime] = None
    error_end_time: Optional[datetime.datetime] = None
    error_content: str = ""
    affected_scope: str = ""
    root_cause: str = ""
    temporary_measures: str = ""
    permanent_solution: str = ""
    timeline: List[Dict[str, str]] = field(default_factory=list)
    error_events: List[ErrorEvent] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "title": self.title,
            "overview": self.overview,
            "error_start_time": self.error_start_time.isoformat() if self.error_start_time else None,
            "error_end_time": self.error_end_time.isoformat() if self.error_end_time else None,
            "error_content": self.error_content,
            "affected_scope": self.affected_scope,
            "root_cause": self.root_cause,
            "temporary_measures": self.temporary_measures,
            "permanent_solution": self.permanent_solution,
            "timeline": self.timeline
        }
        return result
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md_lines = [
            f"# {self.title}",
            "",
            "## 概要",
            "",
            self.overview,
            "",
            "## 障害発生日",
            "",
            f"{self.error_start_time.strftime('%Y年%m月%d日 %H時%M分')}頃" if self.error_start_time else "不明",
            "",
            "## 障害復旧日",
            "",
            f"{self.error_end_time.strftime('%Y年%m月%d日 %H時%M分')}頃" if self.error_end_time else "不明",
            "",
            "## 障害内容",
            "",
            self.error_content,
            "",
            "## 障害範囲",
            "",
            self.affected_scope,
            "",
            "## 発生原因",
            "",
            self.root_cause,
            "",
            "## 一時対応",
            "",
            self.temporary_measures,
            "",
            "## 根本対処",
            "",
            self.permanent_solution,
            "",
            "## 対応経緯",
            ""
        ]
        
        # 添加时间线
        for entry in self.timeline:
            time_str = entry.get("time", "")
            action = entry.get("action", "")
            md_lines.append(f"* {time_str}  \n  {action}")
        
        return "\n".join(md_lines)
    
    def to_html(self) -> str:
        """转换为HTML格式"""
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset=\"UTF-8\">",
            f"    <title>{self.title}</title>",
            "    <style>",
            "        body { font-family: 'Noto Sans CJK JP', sans-serif; margin: 20px; }",
            "        h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }",
            "        h2 { color: #555; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px; }",
            "        .timeline { margin-left: 20px; }",
            "        .timeline-item { margin-bottom: 10px; }",
            "        .timeline-time { font-weight: bold; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <h1>{self.title}</h1>",
            "",
            "    <h2>概要</h2>",
            f"    <p>{self.overview}</p>",
            "",
            "    <h2>障害発生日</h2>",
            f"    <p>{self.error_start_time.strftime('%Y年%m月%d日 %H時%M分')}頃</p>" if self.error_start_time else "    <p>不明</p>",
            "",
            "    <h2>障害復旧日</h2>",
            f"    <p>{self.error_end_time.strftime('%Y年%m月%d日 %H時%M分')}頃</p>" if self.error_end_time else "    <p>不明</p>",
            "",
            "    <h2>障害内容</h2>",
            f"    <p>{self.error_content}</p>",
            "",
            "    <h2>障害範囲</h2>",
            f"    <p>{self.affected_scope}</p>",
            "",
            "    <h2>発生原因</h2>",
            f"    <p>{self.root_cause}</p>",
            "",
            "    <h2>一時対応</h2>",
            f"    <p>{self.temporary_measures}</p>",
            "",
            "    <h2>根本対処</h2>",
            f"    <p>{self.permanent_solution}</p>",
            "",
            "    <h2>対応経緯</h2>",
            "    <div class=\"timeline\">"
        ]
        
        # 添加时间线
        for entry in self.timeline:
            time_str = entry.get("time", "")
            action = entry.get("action", "")
            html_lines.append(f"        <div class=\"timeline-item\">")
            html_lines.append(f"            <div class=\"timeline-time\">{time_str}</div>")
            html_lines.append(f"            <div class=\"timeline-action\">{action}</div>")
            html_lines.append(f"        </div>")
        
        html_lines.extend([
            "    </div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_lines)
    
    def to_pdf(self, output_path: str) -> str:
        """
        转换为PDF格式并保存
        
        Args:
            output_path: PDF输出路径
            
        Returns:
            输出的PDF文件路径
        """
        try:
            # 使用WeasyPrint生成PDF（支持CJK字符）
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            # 生成HTML内容
            html_content = self.to_html()
            
            # 创建临时HTML文件
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
                f.write(html_content)
                temp_html_path = f.name
            
            # 配置字体
            font_config = FontConfiguration()
            css = CSS(string='''
                @font-face {
                    font-family: 'Noto Sans CJK JP';
                    src: url('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');
                }
                body {
                    font-family: 'Noto Sans CJK JP', 'WenQuanYi Zen Hei', sans-serif;
                }
            ''', font_config=font_config)
            
            # 生成PDF
            HTML(filename=temp_html_path).write_pdf(
                output_path,
                stylesheets=[css],
                font_config=font_config
            )
            
            # 删除临时文件
            os.unlink(temp_html_path)
            
            logger.info(f"PDF报告已保存到: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"生成PDF时出错: {str(e)}")
            # 如果WeasyPrint失败，尝试使用xhtml2pdf
            try:
                import xhtml2pdf.pisa as pisa
                
                # 生成HTML内容
                html_content = self.to_html()
                
                # 创建PDF
                with open(output_path, "wb") as f:
                    pisa.CreatePDF(html_content, dest=f)
                
                logger.info(f"PDF报告已保存到: {output_path}（使用xhtml2pdf）")
                return output_path
            
            except Exception as e2:
                logger.error(f"使用xhtml2pdf生成PDF时出错: {str(e2)}")
                raise Exception(f"无法生成PDF: {str(e)} / {str(e2)}")

class LogParser:
    """日志解析器类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化日志解析器
        
        Args:
            config: 配置字典，可包含以下键:
                - log_format: 日志格式（LOG4J, LOGBACK, JUL, CUSTOM）
                - custom_pattern: 自定义日志正则表达式模式
                - custom_datetime_format: 自定义日期时间格式
                - timezone: 时区
        """
        self.config = config or {}
        self.log_format = self.config.get("log_format", LogFormat.UNKNOWN)
        self.custom_pattern = self.config.get("custom_pattern", "")
        self.custom_datetime_format = self.config.get("custom_datetime_format", "")
        self.timezone = self.config.get("timezone", datetime.timezone.utc)
        
        # 预编译正则表达式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译日志格式的正则表达式模式"""
        # Log4j 默认格式: 2025-05-23 14:03:39,123 ERROR com.example.MyClass - Error message
        self.log4j_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s+'  # 时间戳
            r'(\w+)\s+'  # 日志级别
            r'(\S+)\s+-\s+'  # 日志名称
            r'(.*?)$'  # 消息
        )
        
        # Logback 默认格式: 2025-05-23 14:03:39.123 [thread-1] ERROR com.example.MyClass - Error message
        self.logback_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+'  # 时间戳
            r'\[([^\]]+)\]\s+'  # 线程名
            r'(\w+)\s+'  # 日志级别
            r'(\S+)\s+-\s+'  # 日志名称
            r'(.*?)$'  # 消息
        )
        
        # JUL 默认格式: May 23, 2025 2:03:39 PM com.example.MyClass severe Error message
        self.jul_pattern = re.compile(
            r'(\w{3}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+(?:AM|PM))\s+'  # 时间戳
            r'(\S+)\s+'  # 日志名称
            r'(\w+)\s+'  # 日志级别
            r'(.*?)$'  # 消息
        )
        
        # 自定义格式
        if self.custom_pattern:
            self.custom_regex = re.compile(self.custom_pattern)
    
    def _parse_log4j_line(self, line: str) -> Optional[LogEntry]:
        """解析Log4j格式的日志行"""
        match = self.log4j_pattern.match(line)
        if not match:
            return None
        
        timestamp_str, level_str, logger_name, message = match.groups()
        
        try:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            level = LogLevel(level_str)
        except (ValueError, KeyError):
            timestamp = datetime.datetime.now()
            level = LogLevel.UNKNOWN
        
        # 检查是否包含异常堆栈
        exception = None
        if "Exception" in line or "Error" in line:
            # 这里简化处理，实际应该检查后续行是否为堆栈信息
            exception = message
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            logger_name=logger_name,
            message=message,
            exception=exception,
            raw_line=line
        )
    
    def _parse_logback_line(self, line: str) -> Optional[LogEntry]:
        """解析Logback格式的日志行"""
        match = self.logback_pattern.match(line)
        if not match:
            return None
        
        timestamp_str, thread, level_str, logger_name, message = match.groups()
        
        try:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            level = LogLevel(level_str)
        except (ValueError, KeyError):
            timestamp = datetime.datetime.now()
            level = LogLevel.UNKNOWN
        
        # 检查是否包含异常堆栈
        exception = None
        if "Exception" in line or "Error" in line:
            # 这里简化处理，实际应该检查后续行是否为堆栈信息
            exception = message
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            logger_name=logger_name,
            message=message,
            exception=exception,
            thread=thread,
            raw_line=line
        )
    
    def _parse_jul_line(self, line: str) -> Optional[LogEntry]:
        """解析JUL格式的日志行"""
        match = self.jul_pattern.match(line)
        if not match:
            return None
        
        timestamp_str, logger_name, level_str, message = match.groups()
        
        try:
            timestamp = datetime.datetime.strptime(timestamp_str, "%b %d, %Y %I:%M:%S %p")
            # JUL使用不同的级别名称
            level_map = {
                "SEVERE": LogLevel.ERROR,
                "WARNING": LogLevel.WARNING,
                "INFO": LogLevel.INFO,
                "CONFIG": LogLevel.INFO,
                "FINE": LogLevel.DEBUG,
                "FINER": LogLevel.DEBUG,
                "FINEST": LogLevel.DEBUG
            }
            level = level_map.get(level_str, LogLevel.UNKNOWN)
        except (ValueError, KeyError):
            timestamp = datetime.datetime.now()
            level = LogLevel.UNKNOWN
        
        # 检查是否包含异常堆栈
        exception = None
        if "Exception" in line or "Error" in line:
            # 这里简化处理，实际应该检查后续行是否为堆栈信息
            exception = message
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            logger_name=logger_name,
            message=message,
            exception=exception,
            raw_line=line
        )
    
    def _parse_custom_line(self, line: str) -> Optional[LogEntry]:
        """解析自定义格式的日志行"""
        if not self.custom_pattern:
            return None
        
        match = self.custom_regex.match(line)
        if not match:
            return None
        
        # 假设自定义模式至少包含时间戳、级别、日志名称和消息
        # 具体字段需要根据实际情况调整
        groups = match.groupdict()
        
        timestamp_str = groups.get("timestamp", "")
        level_str = groups.get("level", "")
        logger_name = groups.get("logger", "")
        message = groups.get("message", "")
        thread = groups.get("thread", None)
        exception = groups.get("exception", None)
        
        try:
            if self.custom_datetime_format:
                timestamp = datetime.datetime.strptime(timestamp_str, self.custom_datetime_format)
            else:
                # 尝试常见的日期时间格式
                for fmt in ["%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%d %H:%M:%S.%f", "%b %d, %Y %I:%M:%S %p"]:
                    try:
                        timestamp = datetime.datetime.strptime(timestamp_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    timestamp = datetime.datetime.now()
            
            try:
                level = LogLevel(level_str)
            except ValueError:
                # 尝试映射常见的日志级别名称
                level_map = {
                    "SEVERE": LogLevel.ERROR,
                    "WARNING": LogLevel.WARNING,
                    "WARN": LogLevel.WARNING,
                    "INFO": LogLevel.INFO,
                    "CONFIG": LogLevel.INFO,
                    "FINE": LogLevel.DEBUG,
                    "FINER": LogLevel.DEBUG,
                    "FINEST": LogLevel.DEBUG,
                    "DEBUG": LogLevel.DEBUG,
                    "ERROR": LogLevel.ERROR,
                    "FATAL": LogLevel.FATAL,
                    "CRITICAL": LogLevel.CRITICAL
                }
                level = level_map.get(level_str, LogLevel.UNKNOWN)
        except (ValueError, KeyError):
            timestamp = datetime.datetime.now()
            level = LogLevel.UNKNOWN
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            logger_name=logger_name,
            message=message,
            exception=exception,
            thread=thread,
            raw_line=line
        )
    
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        解析单行日志
        
        Args:
            line: 日志行文本
            
        Returns:
            LogEntry或None（如果无法解析）
        """
        if not line or line.isspace():
            return None
        
        # 根据指定的日志格式尝试解析
        if self.log_format == LogFormat.LOG4J:
            return self._parse_log4j_line(line)
        elif self.log_format == LogFormat.LOGBACK:
            return self._parse_logback_line(line)
        elif self.log_format == LogFormat.JUL:
            return self._parse_jul_line(line)
        elif self.log_format == LogFormat.CUSTOM:
            return self._parse_custom_line(line)
        
        # 如果未指定格式或指定为UNKNOWN，尝试所有格式
        parsers = [
            self._parse_log4j_line,
            self._parse_logback_line,
            self._parse_jul_line
        ]
        
        if self.custom_pattern:
            parsers.append(self._parse_custom_line)
        
        for parser in parsers:
            entry = parser(line)
            if entry:
                return entry
        
        # 如果所有格式都无法解析，返回None
        return None
    
    def parse_file(self, file_path: str) -> List[LogEntry]:
        """
        解析日志文件
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            LogEntry列表
        """
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = self.parse_line(line.strip())
                    if entry:
                        entries.append(entry)
        except Exception as e:
            logger.error(f"解析日志文件时出错: {str(e)}")
        
        return entries
    
    def parse_text(self, text: str) -> List[LogEntry]:
        """
        解析日志文本
        
        Args:
            text: 日志文本
            
        Returns:
            LogEntry列表
        """
        entries = []
        
        for line in text.splitlines():
            entry = self.parse_line(line.strip())
            if entry:
                entries.append(entry)
        
        return entries

class ErrorAnalyzer:
    """错误分析器类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化错误分析器
        
        Args:
            config: 配置字典，可包含以下键:
                - error_patterns: 错误模式字典，键为错误类型，值为正则表达式模式
                - component_patterns: 组件模式字典，键为组件名称，值为正则表达式模式
                - resolution_templates: 解决方案模板字典，键为错误类型，值为解决方案模板
                - impact_templates: 影响模板字典，键为错误类型，值为影响模板
        """
        self.config = config or {}
        
        # 错误模式
        self.error_patterns = self.config.get("error_patterns", {})
        if not self.error_patterns:
            # 默认错误模式
            self.error_patterns = {
                "数据库连接错误": r"(?i)(database|connection|sql|jdbc).*?(error|exception|timeout|refused)",
                "网络超时": r"(?i)(network|connection|timeout|socket).*?(timeout|refused|reset)",
                "内存溢出": r"(?i)(out\s+of\s+memory|java\.lang\.OutOfMemoryError)",
                "空指针异常": r"(?i)(null\s+pointer|NullPointerException)",
                "权限错误": r"(?i)(permission|access|denied|unauthorized)",
                "配置错误": r"(?i)(configuration|config|property|setting).*?(error|missing|invalid)",
                "IO错误": r"(?i)(io|input|output|file).*?(error|exception|failed)",
                "类加载错误": r"(?i)(class|classloader|NoClassDefFoundError|ClassNotFoundException)",
                "并发错误": r"(?i)(concurrent|deadlock|race\s+condition|ConcurrentModificationException)",
                "内部服务器错误": r"(?i)(internal\s+server\s+error|500|server\s+error)",
                "API错误": r"(?i)(api|rest|http|endpoint).*?(error|exception|failed|4\d\d)",
                "认证错误": r"(?i)(authentication|login|credential).*?(error|failed|invalid)",
                "会话过期": r"(?i)(session|token).*?(expired|timeout|invalid)"
            }
        
        # 组件模式
        self.component_patterns = self.config.get("component_patterns", {})
        if not self.component_patterns:
            # 默认组件模式
            self.component_patterns = {
                "数据库": r"(?i)(database|sql|jdbc|oracle|mysql|postgresql|mongodb)",
                "网络": r"(?i)(network|http|https|tcp|udp|socket|connection)",
                "文件系统": r"(?i)(file|directory|path|io)",
                "内存管理": r"(?i)(memory|heap|gc|garbage\s+collector)",
                "认证系统": r"(?i)(auth|authentication|login|credential|password)",
                "API服务": r"(?i)(api|rest|endpoint|controller)",
                "缓存": r"(?i)(cache|redis|memcached)",
                "消息队列": r"(?i)(queue|kafka|rabbitmq|jms|activemq)",
                "前端界面": r"(?i)(ui|interface|frontend|browser|javascript)",
                "后端服务": r"(?i)(backend|service|server)",
                "日志系统": r"(?i)(log|logger|logging)",
                "配置系统": r"(?i)(config|configuration|property|setting)",
                "安全模块": r"(?i)(security|encryption|ssl|tls)"
            }
        
        # 解决方案模板
        self.resolution_templates = self.config.get("resolution_templates", {})
        if not self.resolution_templates:
            # 默认解决方案模板
            self.resolution_templates = {
                "数据库连接错误": "1. 检查数据库服务器状态\n2. 验证连接字符串和凭据\n3. 确认网络连接\n4. 检查数据库连接池配置\n5. 增加连接超时设置",
                "网络超时": "1. 检查网络连接状态\n2. 验证目标服务器是否可达\n3. 调整超时设置\n4. 实施重试机制\n5. 检查防火墙设置",
                "内存溢出": "1. 增加JVM堆内存设置\n2. 检查内存泄漏\n3. 优化大对象处理\n4. 调整GC策略\n5. 实施内存监控",
                "空指针异常": "1. 添加空值检查\n2. 使用Optional类型\n3. 修复空值来源\n4. 完善错误处理\n5. 增加日志记录",
                "权限错误": "1. 检查用户权限设置\n2. 验证访问控制列表\n3. 更新安全策略\n4. 检查文件/资源权限\n5. 实施适当的权限管理",
                "配置错误": "1. 检查配置文件\n2. 验证配置值\n3. 提供默认配置\n4. 实施配置验证\n5. 改进配置管理",
                "IO错误": "1. 检查文件系统权限\n2. 验证路径是否存在\n3. 确保磁盘空间充足\n4. 处理文件锁定问题\n5. 实施IO异常处理",
                "类加载错误": "1. 检查类路径\n2. 验证依赖项\n3. 解决版本冲突\n4. 检查JAR文件完整性\n5. 调整类加载器配置",
                "并发错误": "1. 实施适当的锁机制\n2. 使用线程安全集合\n3. 避免死锁条件\n4. 优化并发访问\n5. 使用并发工具类",
                "内部服务器错误": "1. 检查服务器日志\n2. 验证应用配置\n3. 重启服务\n4. 增加错误处理\n5. 实施服务监控",
                "API错误": "1. 检查API参数\n2. 验证API版本\n3. 测试API端点\n4. 实施API监控\n5. 改进错误处理",
                "认证错误": "1. 检查认证凭据\n2. 验证认证流程\n3. 更新认证机制\n4. 实施安全日志\n5. 增强认证安全性",
                "会话过期": "1. 调整会话超时设置\n2. 实施会话续期机制\n3. 改进会话管理\n4. 添加会话状态检查\n5. 实施安全会话处理"
            }
        
        # 影响模板
        self.impact_templates = self.config.get("impact_templates", {})
        if not self.impact_templates:
            # 默认影响模板
            self.impact_templates = {
                "数据库连接错误": "无法访问数据库，导致依赖数据库的功能无法正常工作。用户可能无法查询或保存数据。",
                "网络超时": "系统无法与外部服务通信，导致依赖这些服务的功能暂时不可用。",
                "内存溢出": "系统内存不足，可能导致应用崩溃或性能严重下降。",
                "空指针异常": "特定功能执行失败，可能导致用户操作中断或数据处理不完整。",
                "权限错误": "用户无法访问特定资源或执行特定操作，影响正常业务流程。",
                "配置错误": "系统配置不正确，可能导致功能异常或性能问题。",
                "IO错误": "文件读写操作失败，可能导致数据丢失或功能不可用。",
                "类加载错误": "系统无法加载必要的类，导致特定功能或整个应用无法启动。",
                "并发错误": "多用户同时操作时出现数据不一致或处理错误，影响系统稳定性。",
                "内部服务器错误": "服务器内部错误，导致请求处理失败，用户可能遇到操作中断。",
                "API错误": "API调用失败，导致依赖该API的功能不可用。",
                "认证错误": "用户无法成功登录或认证，无法访问系统功能。",
                "会话过期": "用户会话已过期，需要重新登录才能继续操作。"
            }
        
        # 编译正则表达式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译错误和组件模式的正则表达式"""
        self.error_regex = {}
        for error_type, pattern in self.error_patterns.items():
            self.error_regex[error_type] = re.compile(pattern)
        
        self.component_regex = {}
        for component, pattern in self.component_patterns.items():
            self.component_regex[component] = re.compile(pattern)
    
    def identify_error_type(self, log_entry: LogEntry) -> str:
        """
        识别错误类型
        
        Args:
            log_entry: 日志条目
            
        Returns:
            错误类型
        """
        # 组合消息和异常信息进行匹配
        text = f"{log_entry.message} {log_entry.exception or ''}"
        
        for error_type, regex in self.error_regex.items():
            if regex.search(text):
                return error_type
        
        # 如果没有匹配的错误类型，根据日志级别返回通用错误类型
        if log_entry.level in [LogLevel.ERROR, LogLevel.FATAL, LogLevel.CRITICAL]:
            return "系统错误"
        elif log_entry.level in [LogLevel.WARN, LogLevel.WARNING]:
            return "系统警告"
        else:
            return "未知问题"
    
    def identify_affected_components(self, log_entry: LogEntry) -> List[str]:
        """
        识别受影响的组件
        
        Args:
            log_entry: 日志条目
            
        Returns:
            受影响组件列表
        """
        # 组合消息、异常信息和日志名称进行匹配
        text = f"{log_entry.logger_name} {log_entry.message} {log_entry.exception or ''}"
        
        components = []
        for component, regex in self.component_regex.items():
            if regex.search(text):
                components.append(component)
        
        # 如果没有匹配的组件，根据日志名称推断
        if not components:
            logger_parts = log_entry.logger_name.split('.')
            if len(logger_parts) > 1:
                # 使用包名的第二部分作为组件名（通常是功能模块）
                components.append(logger_parts[1].capitalize())
            else:
                components.append("未知组件")
        
        return components
    
    def get_resolution_template(self, error_type: str) -> str:
        """
        获取解决方案模板
        
        Args:
            error_type: 错误类型
            
        Returns:
            解决方案模板
        """
        return self.resolution_templates.get(error_type, "1. 分析错误日志\n2. 确定根本原因\n3. 实施修复措施\n4. 测试验证\n5. 监控系统")
    
    def get_impact_template(self, error_type: str) -> str:
        """
        获取影响模板
        
        Args:
            error_type: 错误类型
            
        Returns:
            影响模板
        """
        return self.impact_templates.get(error_type, "系统部分功能可能受到影响，具体影响范围需要进一步评估。")
    
    def analyze_error_events(self, log_entries: List[LogEntry]) -> List[ErrorEvent]:
        """
        分析日志条目，识别错误事件
        
        Args:
            log_entries: 日志条目列表
            
        Returns:
            错误事件列表
        """
        if not log_entries:
            return []
        
        # 按时间排序
        sorted_entries = sorted(log_entries, key=lambda e: e.timestamp)
        
        # 识别错误事件
        error_events = []
        current_event = None
        
        for entry in sorted_entries:
            # 只关注错误和警告级别的日志
            if entry.level not in [LogLevel.ERROR, LogLevel.FATAL, LogLevel.CRITICAL, LogLevel.WARN, LogLevel.WARNING]:
                continue
            
            # 识别错误类型和受影响组件
            error_type = self.identify_error_type(entry)
            affected_components = self.identify_affected_components(entry)
            
            # 如果没有当前事件或者当前事件与此条目相差超过30分钟，创建新事件
            if (not current_event or 
                (entry.timestamp - current_event.start_time).total_seconds() > 1800):
                
                # 如果有当前事件，设置结束时间并添加到列表
                if current_event:
                    # 使用最后一个相关日志的时间作为结束时间
                    current_event.end_time = current_event.related_logs[-1].timestamp
                    error_events.append(current_event)
                
                # 创建新事件
                current_event = ErrorEvent(
                    start_time=entry.timestamp,
                    error_type=error_type,
                    error_message=entry.message,
                    affected_components=affected_components,
                    root_cause="分析中...",
                    impact=self.get_impact_template(error_type),
                    resolution=self.get_resolution_template(error_type),
                    related_logs=[entry]
                )
            else:
                # 更新当前事件
                current_event.related_logs.append(entry)
                
                # 如果是同类型错误，更新组件列表
                if error_type == current_event.error_type:
                    for component in affected_components:
                        if component not in current_event.affected_components:
                            current_event.affected_components.append(component)
        
        # 添加最后一个事件
        if current_event:
            current_event.end_time = current_event.related_logs[-1].timestamp
            error_events.append(current_event)
        
        return error_events
    
    def analyze_root_cause(self, error_event: ErrorEvent) -> str:
        """
        分析错误事件的根本原因
        
        Args:
            error_event: 错误事件
            
        Returns:
            根本原因描述
        """
        # 这里可以实现更复杂的根本原因分析逻辑
        # 当前简单实现，根据错误类型和相关日志推断
        
        if not error_event.related_logs:
            return "无法确定根本原因，缺少相关日志信息。"
        
        # 提取异常信息
        exceptions = [log.exception for log in error_event.related_logs if log.exception]
        
        if exceptions:
            # 使用最常见的异常作为根本原因
            from collections import Counter
            common_exception = Counter(exceptions).most_common(1)[0][0]
            return f"根据日志分析，错误原因可能是: {common_exception}"
        
        # 如果没有明确的异常信息，根据错误类型提供通用原因
        cause_templates = {
            "数据库连接错误": "数据库连接失败，可能是由于数据库服务不可用、网络问题或凭据错误导致。",
            "网络超时": "网络连接超时，可能是由于网络拥塞、目标服务不可用或防火墙限制导致。",
            "内存溢出": "系统内存不足，可能是由于内存泄漏、大数据处理或JVM配置不当导致。",
            "空指针异常": "程序尝试访问空对象，可能是由于数据验证不足或初始化问题导致。",
            "权限错误": "权限不足，可能是由于用户权限配置错误或安全策略限制导致。",
            "配置错误": "配置参数错误，可能是由于配置文件缺失、格式错误或值无效导致。",
            "IO错误": "输入/输出操作失败，可能是由于文件系统权限、磁盘空间不足或路径错误导致。",
            "类加载错误": "无法加载类，可能是由于类路径配置错误、依赖缺失或版本冲突导致。",
            "并发错误": "并发访问问题，可能是由于锁竞争、死锁或资源争用导致。",
            "内部服务器错误": "服务器内部错误，可能是由于应用配置错误、资源不足或代码缺陷导致。",
            "API错误": "API调用失败，可能是由于参数错误、API版本不兼容或服务不可用导致。",
            "认证错误": "认证失败，可能是由于凭据错误、认证服务不可用或会话过期导致。",
            "会话过期": "用户会话已过期，可能是由于超时设置、服务器重启或会话无效导致。"
        }
        
        return cause_templates.get(error_event.error_type, "需要进一步分析日志以确定根本原因。")

class ReportGenerator:
    """报告生成器类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化报告生成器
        
        Args:
            config: 配置字典，可包含以下键:
                - report_title: 报告标题
                - company_name: 公司名称
                - system_name: 系统名称
                - report_template: 报告模板路径
                - output_dir: 输出目录
        """
        self.config = config or {}
        self.report_title = self.config.get("report_title", "システム障害報告書")
        self.company_name = self.config.get("company_name", "")
        self.system_name = self.config.get("system_name", "")
        self.report_template = self.config.get("report_template", "")
        self.output_dir = self.config.get("output_dir", "")
        
        # 确保输出目录存在
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_overview(self, error_events: List[ErrorEvent]) -> str:
        """
        生成概述
        
        Args:
            error_events: 错误事件列表
            
        Returns:
            概述文本
        """
        if not error_events:
            return "本障害報告書は、システムで発生した障害についてまとめた文書です。"
        
        # 使用第一个错误事件的信息
        first_event = error_events[0]
        
        system_part = f"{self.system_name}における" if self.system_name else ""
        date_part = first_event.start_time.strftime("%Y年%m月%d日")
        
        if len(error_events) == 1:
            error_type = first_event.error_type
            return f"本障害報告書は{date_part}に発生した{system_part}{error_type}についてまとめた文書になります。ご利用中のお客さまにおかれましては、大変ご迷惑をおかけしました。"
        else:
            return f"本障害報告書は{date_part}に発生した{system_part}複数の障害についてまとめた文書になります。ご利用中のお客さまにおかれましては、大変ご迷惑をおかけしました。"
    
    def generate_error_content(self, error_events: List[ErrorEvent]) -> str:
        """
        生成障害内容
        
        Args:
            error_events: 错误事件列表
            
        Returns:
            障害内容文本
        """
        if not error_events:
            return "障害の詳細は調査中です。"
        
        # 如果只有一个错误事件，使用其详细信息
        if len(error_events) == 1:
            event = error_events[0]
            return f"{event.error_type}が発生し、{', '.join(event.affected_components)}に影響がありました。具体的には、{event.error_message}"
        
        # 如果有多个错误事件，汇总信息
        content_parts = []
        for i, event in enumerate(error_events, 1):
            content_parts.append(f"{i}. {event.error_type}: {event.error_message}")
        
        return "以下の障害が発生しました：\n\n" + "\n\n".join(content_parts)
    
    def generate_affected_scope(self, error_events: List[ErrorEvent]) -> str:
        """
        生成障害范围
        
        Args:
            error_events: 错误事件列表
            
        Returns:
            障害范围文本
        """
        if not error_events:
            return "障害の影響範囲は調査中です。"
        
        # 收集所有受影响的组件
        all_components = set()
        for event in error_events:
            all_components.update(event.affected_components)
        
        # 如果只有一个错误事件，使用其影响描述
        if len(error_events) == 1:
            return f"{', '.join(all_components)}。{error_events[0].impact}"
        
        # 如果有多个错误事件，汇总信息
        scope_parts = [f"影響を受けたコンポーネント: {', '.join(all_components)}"]
        for i, event in enumerate(error_events, 1):
            scope_parts.append(f"{i}. {event.error_type}: {event.impact}")
        
        return "\n\n".join(scope_parts)
    
    def generate_root_cause(self, error_events: List[ErrorEvent]) -> str:
        """
        生成发生原因
        
        Args:
            error_events: 错误事件列表
            
        Returns:
            发生原因文本
        """
        if not error_events:
            return "原因は調査中です。"
        
        # 如果只有一个错误事件，使用其根本原因
        if len(error_events) == 1:
            return error_events[0].root_cause
        
        # 如果有多个错误事件，汇总信息
        cause_parts = []
        for i, event in enumerate(error_events, 1):
            cause_parts.append(f"{i}. {event.error_type}: {event.root_cause}")
        
        return "\n\n".join(cause_parts)
    
    def generate_temporary_measures(self, error_events: List[ErrorEvent]) -> str:
        """
        生成一时对应
        
        Args:
            error_events: 错误事件列表
            
        Returns:
            一时对应文本
        """
        # 通用的临时措施
        common_measures = [
            "エラーが発生したサービスを再起動しました。",
            "影響を受けたユーザーに通知しました。",
            "監視を強化しました。"
        ]
        
        if not error_events:
            return "\n".join(common_measures)
        
        # 如果有错误事件，添加特定措施
        specific_measures = []
        for event in error_events:
            if "数据库" in event.affected_components or "データベース" in event.affected_components:
                specific_measures.append("データベース接続を再確立しました。")
            
            if "网络" in event.affected_components or "ネットワーク" in event.affected_components:
                specific_measures.append("ネットワーク設定を確認し、接続を復旧しました。")
            
            if "内存" in event.affected_components or "メモリ" in event.affected_components:
                specific_measures.append("メモリリソースを増加しました。")
            
            if "API" in event.affected_components:
                specific_measures.append("APIサービスを再起動しました。")
        
        # 去重
        all_measures = list(set(common_measures + specific_measures))
        return "\n".join(all_measures)
    
    def generate_permanent_solution(self, error_events: List[ErrorEvent]) -> str:
        """
        生成根本对处
        
        Args:
            error_events: 错误事件列表
            
        Returns:
            根本对处文本
        """
        if not error_events:
            return "* 詳細な原因分析を行い、適切な対策を実施します。\n* 監視体制を強化します。"
        
        # 收集所有解决方案
        all_solutions = []
        for event in error_events:
            solutions = event.resolution.split("\n")
            all_solutions.extend(solutions)
        
        # 去重并格式化
        unique_solutions = list(set(all_solutions))
        formatted_solutions = [f"* {solution.lstrip('123456789. ')}" for solution in unique_solutions if solution.strip()]
        
        return "\n".join(formatted_solutions)
    
    def generate_timeline(self, error_events: List[ErrorEvent]) -> List[Dict[str, str]]:
        """
        生成时间线
        
        Args:
            error_events: 错误事件列表
            
        Returns:
            时间线条目列表
        """
        if not error_events:
            return []
        
        timeline = []
        
        # 按时间排序所有日志条目
        all_logs = []
        for event in error_events:
            all_logs.extend(event.related_logs)
        
        sorted_logs = sorted(all_logs, key=lambda log: log.timestamp)
        
        # 提取关键日志作为时间线条目
        for log in sorted_logs:
            if log.level in [LogLevel.ERROR, LogLevel.FATAL, LogLevel.CRITICAL]:
                timeline.append({
                    "time": log.timestamp.strftime("%Y年%m月%d日 %H時%M分"),
                    "action": f"エラーが発生: {log.message}"
                })
            elif log.level in [LogLevel.WARN, LogLevel.WARNING]:
                timeline.append({
                    "time": log.timestamp.strftime("%Y年%m月%d日 %H時%M分"),
                    "action": f"警告が発生: {log.message}"
                })
        
        # 添加错误事件的开始和结束
        for event in error_events:
            timeline.append({
                "time": event.start_time.strftime("%Y年%m月%d日 %H時%M分"),
                "action": f"{event.error_type}が発生"
            })
            
            if event.end_time:
                timeline.append({
                    "time": event.end_time.strftime("%Y年%m月%d日 %H時%M分"),
                    "action": f"{event.error_type}が復旧"
                })
        
        # 按时间排序并去重
        timeline = sorted(timeline, key=lambda item: item["time"])
        
        # 去重（相同时间和动作的条目只保留一个）
        unique_timeline = []
        seen = set()
        for item in timeline:
            key = f"{item['time']}_{item['action']}"
            if key not in seen:
                seen.add(key)
                unique_timeline.append(item)
        
        return unique_timeline
    
    def generate_report(self, error_events: List[ErrorEvent]) -> ErrorReport:
        """
        生成错误报告
        
        Args:
            error_events: 错误事件列表
            
        Returns:
            ErrorReport对象
        """
        # 确定报告的开始和结束时间
        if error_events:
            start_times = [event.start_time for event in error_events]
            end_times = [event.end_time for event in error_events if event.end_time]
            
            error_start_time = min(start_times) if start_times else None
            error_end_time = max(end_times) if end_times else None
        else:
            error_start_time = None
            error_end_time = None
        
        # 生成报告各部分内容
        overview = self.generate_overview(error_events)
        error_content = self.generate_error_content(error_events)
        affected_scope = self.generate_affected_scope(error_events)
        root_cause = self.generate_root_cause(error_events)
        temporary_measures = self.generate_temporary_measures(error_events)
        permanent_solution = self.generate_permanent_solution(error_events)
        timeline = self.generate_timeline(error_events)
        
        # 创建报告对象
        report = ErrorReport(
            title=self.report_title,
            overview=overview,
            error_start_time=error_start_time,
            error_end_time=error_end_time,
            error_content=error_content,
            affected_scope=affected_scope,
            root_cause=root_cause,
            temporary_measures=temporary_measures,
            permanent_solution=permanent_solution,
            timeline=timeline,
            error_events=error_events
        )
        
        return report
    
    def save_report(self, report: ErrorReport, output_format: str = "markdown", output_path: str = None) -> str:
        """
        保存报告
        
        Args:
            report: ErrorReport对象
            output_format: 输出格式（markdown, html, pdf, json）
            output_path: 输出路径，如果为None则使用默认路径
            
        Returns:
            保存的文件路径
        """
        # 确定输出路径
        if not output_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_report_{timestamp}"
            
            if output_format == "markdown":
                filename += ".md"
            elif output_format == "html":
                filename += ".html"
            elif output_format == "pdf":
                filename += ".pdf"
            elif output_format == "json":
                filename += ".json"
            else:
                filename += ".txt"
            
            output_path = os.path.join(self.output_dir or ".", filename)
        
        # 根据格式生成内容并保存
        try:
            if output_format == "markdown":
                content = report.to_markdown()
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            elif output_format == "html":
                content = report.to_html()
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            elif output_format == "pdf":
                report.to_pdf(output_path)
            
            elif output_format == "json":
                content = report.to_json()
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            else:
                content = report.to_markdown()
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            logger.info(f"报告已保存到: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"保存报告时出错: {str(e)}")
            raise

class ErrorReportingSystem:
    """错误报告系统类，集成日志解析、错误分析和报告生成"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化错误报告系统
        
        Args:
            config: 配置字典，可包含日志解析器、错误分析器和报告生成器的配置
        """
        self.config = config or {}
        
        # 创建子模块
        self.log_parser = LogParser(self.config.get("log_parser_config", {}))
        self.error_analyzer = ErrorAnalyzer(self.config.get("error_analyzer_config", {}))
        self.report_generator = ReportGenerator(self.config.get("report_generator_config", {}))
    
    def process_log_file(self, log_file_path: str, output_format: str = "markdown", output_path: str = None) -> str:
        """
        处理日志文件并生成报告
        
        Args:
            log_file_path: 日志文件路径
            output_format: 输出格式
            output_path: 输出路径
            
        Returns:
            生成的报告文件路径
        """
        # 解析日志
        log_entries = self.log_parser.parse_file(log_file_path)
        
        if not log_entries:
            logger.warning(f"未在日志文件中找到有效条目: {log_file_path}")
            # 创建一个空报告
            report = self.report_generator.generate_report([])
        else:
            # 分析错误事件
            error_events = self.error_analyzer.analyze_error_events(log_entries)
            
            # 分析根本原因
            for event in error_events:
                event.root_cause = self.error_analyzer.analyze_root_cause(event)
            
            # 生成报告
            report = self.report_generator.generate_report(error_events)
        
        # 保存报告
        return self.report_generator.save_report(report, output_format, output_path)
    
    def process_log_text(self, log_text: str, output_format: str = "markdown", output_path: str = None) -> str:
        """
        处理日志文本并生成报告
        
        Args:
            log_text: 日志文本
            output_format: 输出格式
            output_path: 输出路径
            
        Returns:
            生成的报告文件路径
        """
        # 解析日志
        log_entries = self.log_parser.parse_text(log_text)
        
        if not log_entries:
            logger.warning("未在日志文本中找到有效条目")
            # 创建一个空报告
            report = self.report_generator.generate_report([])
        else:
            # 分析错误事件
            error_events = self.error_analyzer.analyze_error_events(log_entries)
            
            # 分析根本原因
            for event in error_events:
                event.root_cause = self.error_analyzer.analyze_root_cause(event)
            
            # 生成报告
            report = self.report_generator.generate_report(error_events)
        
        # 保存报告
        return self.report_generator.save_report(report, output_format, output_path)

# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="错误报告生成工具")
    parser.add_argument("input", help="输入日志文件路径")
    parser.add_argument("-o", "--output", help="输出报告路径")
    parser.add_argument("-f", "--format", choices=["markdown", "html", "pdf", "json"], default="markdown", help="输出格式")
    parser.add_argument("-t", "--title", default="システム障害報告書", help="报告标题")
    parser.add_argument("-c", "--company", default="", help="公司名称")
    parser.add_argument("-s", "--system", default="", help="系统名称")
    parser.add_argument("-l", "--log-format", choices=["log4j", "logback", "jul", "custom"], help="日志格式")
    parser.add_argument("-p", "--pattern", help="自定义日志正则表达式模式")
    parser.add_argument("-d", "--datetime-format", help="自定义日期时间格式")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建配置
    config = {
        "log_parser_config": {},
        "report_generator_config": {
            "report_title": args.title,
            "company_name": args.company,
            "system_name": args.system
        }
    }
    
    # 设置日志格式
    if args.log_format:
        config["log_parser_config"]["log_format"] = LogFormat[args.log_format.upper()]
    
    # 设置自定义模式
    if args.pattern:
        config["log_parser_config"]["custom_pattern"] = args.pattern
    
    # 设置自定义日期时间格式
    if args.datetime_format:
        config["log_parser_config"]["custom_datetime_format"] = args.datetime_format
    
    # 创建错误报告系统
    system = ErrorReportingSystem(config)
    
    # 处理日志文件
    output_path = system.process_log_file(args.input, args.format, args.output)
    
    print(f"报告已生成: {output_path}")
