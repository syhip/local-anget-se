"""
自动化需求变更与文档代码同步模块 - 实现

该模块实现了根据需求变更自动更新设计文档和Java代码，并生成测试文档和部署流程的功能。
支持结构化需求输入，通过AST分析和修改Java代码，同步更新设计文档，并生成符合日本标准的测试仕様書。

作者: Manus AI
日期: 2025-05-23
"""

import os
import re
import json
import yaml
import logging
import datetime
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from enum import Enum
from dataclasses import dataclass, field
import difflib
import javalang  # 用于Java代码解析
import markdown  # 用于Markdown解析
import jinja2    # 用于模板渲染

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """变更类型枚举"""
    ADD_FEATURE = "add_feature"       # 添加新功能
    MODIFY_FEATURE = "modify_feature" # 修改现有功能
    FIX_BUG = "fix_bug"               # 修复Bug
    REFACTOR = "refactor"             # 重构代码
    OPTIMIZE = "optimize"             # 优化性能
    OTHER = "other"                   # 其他变更

@dataclass
class RequirementChange:
    """需求变更类"""
    change_type: ChangeType
    feature_name: str
    description: str
    affected_components: List[str]
    design_doc_sections: List[str]
    requirements: List[str]
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequirementChange':
        """从字典创建需求变更对象"""
        try:
            change_type = ChangeType(data.get("change_type", "other"))
        except ValueError:
            change_type = ChangeType.OTHER
            
        return cls(
            change_type=change_type,
            feature_name=data.get("feature_name", ""),
            description=data.get("description", ""),
            affected_components=data.get("affected_components", []),
            design_doc_sections=data.get("design_doc_sections", []),
            requirements=data.get("requirements", []),
            additional_info=data.get("additional_info", {})
        )
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'RequirementChange':
        """从YAML字符串创建需求变更对象"""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RequirementChange':
        """从JSON字符串创建需求变更对象"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "change_type": self.change_type.value,
            "feature_name": self.feature_name,
            "description": self.description,
            "affected_components": self.affected_components,
            "design_doc_sections": self.design_doc_sections,
            "requirements": self.requirements,
            "additional_info": self.additional_info
        }
    
    def to_yaml(self) -> str:
        """转换为YAML字符串"""
        return yaml.dump(self.to_dict(), allow_unicode=True)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

@dataclass
class JavaCodeElement:
    """Java代码元素类"""
    element_type: str  # class, interface, method, field, etc.
    name: str
    package: Optional[str] = None
    modifiers: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    javadoc: Optional[str] = None
    parent: Optional['JavaCodeElement'] = None
    children: List['JavaCodeElement'] = field(default_factory=list)
    source_code: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    
    def get_full_name(self) -> str:
        """获取完整名称（包括包名）"""
        if self.package and self.element_type in ["class", "interface", "enum"]:
            return f"{self.package}.{self.name}"
        return self.name
    
    def get_signature(self) -> str:
        """获取元素签名"""
        if self.element_type == "method":
            # 简化的方法签名
            return f"{' '.join(self.modifiers)} {self.name}()"
        elif self.element_type in ["class", "interface", "enum"]:
            return f"{' '.join(self.modifiers)} {self.element_type} {self.name}"
        elif self.element_type == "field":
            return f"{' '.join(self.modifiers)} {self.name}"
        return self.name
    
    def add_child(self, child: 'JavaCodeElement') -> None:
        """添加子元素"""
        child.parent = self
        self.children.append(child)
    
    def find_child_by_name(self, name: str) -> Optional['JavaCodeElement']:
        """根据名称查找子元素"""
        for child in self.children:
            if child.name == name:
                return child
        return None
    
    def find_children_by_type(self, element_type: str) -> List['JavaCodeElement']:
        """根据类型查找子元素"""
        return [child for child in self.children if child.element_type == element_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "element_type": self.element_type,
            "name": self.name,
            "package": self.package,
            "modifiers": self.modifiers,
            "annotations": self.annotations,
            "javadoc": self.javadoc,
            "children": [child.to_dict() for child in self.children],
            "source_code": self.source_code,
            "start_position": self.start_position,
            "end_position": self.end_position
        }

@dataclass
class DocumentSection:
    """文档章节类"""
    title: str
    content: str
    level: int  # 标题级别，如1表示#，2表示##
    children: List['DocumentSection'] = field(default_factory=list)
    parent: Optional['DocumentSection'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child: 'DocumentSection') -> None:
        """添加子章节"""
        child.parent = self
        self.children.append(child)
    
    def find_section_by_title(self, title: str) -> Optional['DocumentSection']:
        """根据标题查找章节"""
        if self.title == title:
            return self
        
        for child in self.children:
            result = child.find_section_by_title(title)
            if result:
                return result
        
        return None
    
    def find_sections_by_pattern(self, pattern: str) -> List['DocumentSection']:
        """根据正则表达式模式查找章节"""
        result = []
        
        if re.search(pattern, self.title):
            result.append(self)
        
        for child in self.children:
            result.extend(child.find_sections_by_pattern(pattern))
        
        return result
    
    def to_markdown(self) -> str:
        """转换为Markdown字符串"""
        lines = []
        
        # 添加标题
        lines.append(f"{'#' * self.level} {self.title}")
        lines.append("")
        
        # 添加内容
        if self.content:
            lines.append(self.content)
            lines.append("")
        
        # 添加子章节
        for child in self.children:
            lines.append(child.to_markdown())
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata
        }

@dataclass
class TestCase:
    """测试用例类"""
    id: str
    category: str  # 大項目
    sub_category: str  # 中項目
    item: str  # 小項目
    conditions: List[str]  # テスト条件
    steps: List[str]  # テスト手順
    expected_results: List[str]  # 期待結果
    actual_results: Optional[str] = None  # 実施結果
    status: str = "未実施"  # 状態
    notes: Optional[str] = None  # 備考
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "category": self.category,
            "sub_category": self.sub_category,
            "item": self.item,
            "conditions": self.conditions,
            "steps": self.steps,
            "expected_results": self.expected_results,
            "actual_results": self.actual_results,
            "status": self.status,
            "notes": self.notes
        }

@dataclass
class TestSpecification:
    """测试仕様書类"""
    title: str
    version: str
    created_date: datetime.datetime
    updated_date: datetime.datetime
    author: str
    test_cases: List[TestCase] = field(default_factory=list)
    description: Optional[str] = None
    scope: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    
    def add_test_case(self, test_case: TestCase) -> None:
        """添加测试用例"""
        self.test_cases.append(test_case)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "version": self.version,
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat(),
            "author": self.author,
            "description": self.description,
            "scope": self.scope,
            "prerequisites": self.prerequisites,
            "test_cases": [tc.to_dict() for tc in self.test_cases]
        }
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        lines = []
        
        # 标题和元数据
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"- バージョン: {self.version}")
        lines.append(f"- 作成日: {self.created_date.strftime('%Y年%m月%d日')}")
        lines.append(f"- 更新日: {self.updated_date.strftime('%Y年%m月%d日')}")
        lines.append(f"- 作成者: {self.author}")
        lines.append("")
        
        # 描述和范围
        if self.description:
            lines.append("## 概要")
            lines.append("")
            lines.append(self.description)
            lines.append("")
        
        if self.scope:
            lines.append("## 範囲")
            lines.append("")
            lines.append(self.scope)
            lines.append("")
        
        # 前提条件
        if self.prerequisites:
            lines.append("## 前提条件")
            lines.append("")
            for prereq in self.prerequisites:
                lines.append(f"- {prereq}")
            lines.append("")
        
        # 测试用例
        lines.append("## テストケース")
        lines.append("")
        
        # 表头
        lines.append("| ID | 大項目 | 中項目 | 小項目 | テスト条件 | テスト手順 | 期待結果 | 実施結果 | 状態 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        
        # 测试用例行
        for tc in self.test_cases:
            conditions = "<br>".join(tc.conditions)
            steps = "<br>".join(tc.steps)
            expected = "<br>".join(tc.expected_results)
            actual = tc.actual_results or ""
            
            lines.append(f"| {tc.id} | {tc.category} | {tc.sub_category} | {tc.item} | {conditions} | {steps} | {expected} | {actual} | {tc.status} |")
        
        return "\n".join(lines)

class JavaCodeParser:
    """Java代码解析器类"""
    
    def __init__(self):
        """初始化Java代码解析器"""
        pass
    
    def parse_file(self, file_path: str) -> JavaCodeElement:
        """
        解析Java文件
        
        Args:
            file_path: Java文件路径
            
        Returns:
            JavaCodeElement对象
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            return self.parse_source(source_code)
        except Exception as e:
            logger.error(f"解析Java文件时出错: {str(e)}")
            raise
    
    def parse_source(self, source_code: str) -> JavaCodeElement:
        """
        解析Java源代码
        
        Args:
            source_code: Java源代码字符串
            
        Returns:
            JavaCodeElement对象
        """
        try:
            # 使用javalang解析Java源代码
            tree = javalang.parse.parse(source_code)
            
            # 创建根元素（包）
            root = JavaCodeElement(
                element_type="package",
                name=tree.package.name if tree.package else "default",
                package=None,
                source_code=source_code
            )
            
            # 解析类、接口和枚举
            for path, node in tree.filter(javalang.tree.TypeDeclaration):
                if isinstance(node, javalang.tree.ClassDeclaration):
                    class_element = self._parse_class(node, root.name, source_code)
                    root.add_child(class_element)
                elif isinstance(node, javalang.tree.InterfaceDeclaration):
                    interface_element = self._parse_interface(node, root.name, source_code)
                    root.add_child(interface_element)
                elif isinstance(node, javalang.tree.EnumDeclaration):
                    enum_element = self._parse_enum(node, root.name, source_code)
                    root.add_child(enum_element)
            
            return root
        except Exception as e:
            logger.error(f"解析Java源代码时出错: {str(e)}")
            raise
    
    def _parse_class(self, node: javalang.tree.ClassDeclaration, package_name: str, source_code: str) -> JavaCodeElement:
        """解析类声明"""
        class_element = JavaCodeElement(
            element_type="class",
            name=node.name,
            package=package_name,
            modifiers=[m for m in node.modifiers],
            annotations=self._parse_annotations(node.annotations),
            javadoc=self._extract_javadoc(node, source_code),
            source_code=self._extract_node_source(node, source_code),
            start_position=node.position.line if node.position else None,
            end_position=self._find_end_position(node, source_code)
        )
        
        # 解析字段
        for field_node in node.fields:
            for declarator in field_node.declarators:
                field_element = JavaCodeElement(
                    element_type="field",
                    name=declarator.name,
                    modifiers=[m for m in field_node.modifiers],
                    annotations=self._parse_annotations(field_node.annotations),
                    javadoc=self._extract_javadoc(field_node, source_code),
                    source_code=self._extract_node_source(field_node, source_code)
                )
                class_element.add_child(field_element)
        
        # 解析方法
        for method_node in node.methods:
            method_element = self._parse_method(method_node, source_code)
            class_element.add_child(method_element)
        
        # 解析构造函数
        for constructor_node in node.constructors:
            constructor_element = JavaCodeElement(
                element_type="constructor",
                name=constructor_node.name,
                modifiers=[m for m in constructor_node.modifiers],
                annotations=self._parse_annotations(constructor_node.annotations),
                javadoc=self._extract_javadoc(constructor_node, source_code),
                source_code=self._extract_node_source(constructor_node, source_code)
            )
            class_element.add_child(constructor_element)
        
        # 解析内部类
        for inner_class_node in [n for n in node.body if isinstance(n, javalang.tree.ClassDeclaration)]:
            inner_class_element = self._parse_class(inner_class_node, package_name, source_code)
            class_element.add_child(inner_class_element)
        
        return class_element
    
    def _parse_interface(self, node: javalang.tree.InterfaceDeclaration, package_name: str, source_code: str) -> JavaCodeElement:
        """解析接口声明"""
        interface_element = JavaCodeElement(
            element_type="interface",
            name=node.name,
            package=package_name,
            modifiers=[m for m in node.modifiers],
            annotations=self._parse_annotations(node.annotations),
            javadoc=self._extract_javadoc(node, source_code),
            source_code=self._extract_node_source(node, source_code),
            start_position=node.position.line if node.position else None,
            end_position=self._find_end_position(node, source_code)
        )
        
        # 解析常量
        for field_node in node.fields:
            for declarator in field_node.declarators:
                field_element = JavaCodeElement(
                    element_type="field",
                    name=declarator.name,
                    modifiers=[m for m in field_node.modifiers],
                    annotations=self._parse_annotations(field_node.annotations),
                    javadoc=self._extract_javadoc(field_node, source_code),
                    source_code=self._extract_node_source(field_node, source_code)
                )
                interface_element.add_child(field_element)
        
        # 解析方法
        for method_node in node.methods:
            method_element = self._parse_method(method_node, source_code)
            interface_element.add_child(method_element)
        
        return interface_element
    
    def _parse_enum(self, node: javalang.tree.EnumDeclaration, package_name: str, source_code: str) -> JavaCodeElement:
        """解析枚举声明"""
        enum_element = JavaCodeElement(
            element_type="enum",
            name=node.name,
            package=package_name,
            modifiers=[m for m in node.modifiers],
            annotations=self._parse_annotations(node.annotations),
            javadoc=self._extract_javadoc(node, source_code),
            source_code=self._extract_node_source(node, source_code),
            start_position=node.position.line if node.position else None,
            end_position=self._find_end_position(node, source_code)
        )
        
        # 解析枚举常量
        for constant in node.body.constants:
            constant_element = JavaCodeElement(
                element_type="enum_constant",
                name=constant.name,
                annotations=self._parse_annotations(constant.annotations),
                source_code=self._extract_node_source(constant, source_code)
            )
            enum_element.add_child(constant_element)
        
        # 解析方法
        for method_node in [n for n in node.body.declarations if isinstance(n, javalang.tree.MethodDeclaration)]:
            method_element = self._parse_method(method_node, source_code)
            enum_element.add_child(method_element)
        
        return enum_element
    
    def _parse_method(self, node: javalang.tree.MethodDeclaration, source_code: str) -> JavaCodeElement:
        """解析方法声明"""
        method_element = JavaCodeElement(
            element_type="method",
            name=node.name,
            modifiers=[m for m in node.modifiers],
            annotations=self._parse_annotations(node.annotations),
            javadoc=self._extract_javadoc(node, source_code),
            source_code=self._extract_node_source(node, source_code),
            start_position=node.position.line if node.position else None,
            end_position=self._find_end_position(node, source_code)
        )
        
        return method_element
    
    def _parse_annotations(self, annotations: List[Any]) -> List[str]:
        """解析注解"""
        result = []
        for annotation in annotations:
            if hasattr(annotation, 'name'):
                result.append(f"@{annotation.name}")
            elif hasattr(annotation, 'type') and hasattr(annotation.type, 'name'):
                result.append(f"@{annotation.type.name}")
        return result
    
    def _extract_javadoc(self, node: Any, source_code: str) -> Optional[str]:
        """提取Javadoc注释"""
        if not hasattr(node, 'position') or not node.position:
            return None
        
        line = node.position.line
        if line <= 1:
            return None
        
        # 向上查找Javadoc注释
        lines = source_code.splitlines()
        javadoc_lines = []
        
        i = line - 2  # 从声明的前一行开始向上查找
        while i >= 0:
            if re.match(r'\s*/\*\*', lines[i]):
                # 找到Javadoc开始
                while i < line - 1:
                    javadoc_lines.append(lines[i])
                    if re.search(r'\*/', lines[i]):
                        break
                    i += 1
                break
            elif not re.match(r'\s*$', lines[i]):
                # 如果遇到非空行且不是Javadoc，则停止查找
                break
            i -= 1
        
        if not javadoc_lines:
            return None
        
        return '\n'.join(javadoc_lines)
    
    def _extract_node_source(self, node: Any, source_code: str) -> Optional[str]:
        """提取节点的源代码"""
        if not hasattr(node, 'position') or not node.position:
            return None
        
        start_line = node.position.line
        end_line = self._find_end_position(node, source_code)
        
        if not end_line or end_line < start_line:
            return None
        
        lines = source_code.splitlines()
        return '\n'.join(lines[start_line-1:end_line])
    
    def _find_end_position(self, node: Any, source_code: str) -> Optional[int]:
        """查找节点的结束位置"""
        # 这是一个简化的实现，实际上需要更复杂的逻辑来准确找到结束位置
        # 在实际项目中，可能需要使用更高级的解析器或者自定义逻辑
        
        if not hasattr(node, 'position') or not node.position:
            return None
        
        start_line = node.position.line
        lines = source_code.splitlines()
        
        # 对于类、接口、枚举等，查找匹配的大括号
        if isinstance(node, (javalang.tree.ClassDeclaration, javalang.tree.InterfaceDeclaration, javalang.tree.EnumDeclaration)):
            brace_count = 0
            found_opening = False
            
            for i in range(start_line - 1, len(lines)):
                line = lines[i]
                
                if not found_opening and '{' in line:
                    found_opening = True
                
                if found_opening:
                    brace_count += line.count('{')
                    brace_count -= line.count('}')
                    
                    if brace_count == 0:
                        return i + 1
        
        # 对于方法，查找方法体的结束
        elif isinstance(node, javalang.tree.MethodDeclaration):
            if not node.body:
                # 接口方法或抽象方法
                for i in range(start_line - 1, len(lines)):
                    if ';' in lines[i]:
                        return i + 1
            else:
                brace_count = 0
                found_opening = False
                
                for i in range(start_line - 1, len(lines)):
                    line = lines[i]
                    
                    if not found_opening and '{' in line:
                        found_opening = True
                    
                    if found_opening:
                        brace_count += line.count('{')
                        brace_count -= line.count('}')
                        
                        if brace_count == 0:
                            return i + 1
        
        # 对于字段，查找分号
        elif isinstance(node, javalang.tree.FieldDeclaration):
            for i in range(start_line - 1, len(lines)):
                if ';' in lines[i]:
                    return i + 1
        
        return start_line  # 如果无法确定结束位置，返回开始位置

class JavaCodeModifier:
    """Java代码修改器类"""
    
    def __init__(self, parser: JavaCodeParser = None):
        """
        初始化Java代码修改器
        
        Args:
            parser: Java代码解析器，如果为None则创建新的解析器
        """
        self.parser = parser or JavaCodeParser()
    
    def add_method(self, source_code: str, class_name: str, method_code: str) -> str:
        """
        向类中添加方法
        
        Args:
            source_code: 源代码
            class_name: 类名
            method_code: 方法代码
            
        Returns:
            修改后的源代码
        """
        try:
            # 解析源代码
            root = self.parser.parse_source(source_code)
            
            # 查找类
            class_element = None
            for child in root.children:
                if child.element_type == "class" and child.name == class_name:
                    class_element = child
                    break
            
            if not class_element:
                raise ValueError(f"找不到类: {class_name}")
            
            # 找到类的结束大括号位置
            lines = source_code.splitlines()
            end_line = class_element.end_position
            
            if not end_line or end_line <= 0 or end_line > len(lines):
                raise ValueError(f"无法确定类的结束位置: {class_name}")
            
            # 在结束大括号前插入方法
            result_lines = lines[:end_line-1]
            
            # 确保方法前有空行
            if result_lines and result_lines[-1].strip():
                result_lines.append("")
            
            # 添加方法代码
            result_lines.extend(method_code.splitlines())
            
            # 确保方法后有空行
            if not method_code.endswith("\n"):
                result_lines.append("")
            
            # 添加剩余的代码
            result_lines.extend(lines[end_line-1:])
            
            return "\n".join(result_lines)
        
        except Exception as e:
            logger.error(f"添加方法时出错: {str(e)}")
            raise
    
    def modify_method(self, source_code: str, class_name: str, method_name: str, new_method_code: str) -> str:
        """
        修改类中的方法
        
        Args:
            source_code: 源代码
            class_name: 类名
            method_name: 方法名
            new_method_code: 新的方法代码
            
        Returns:
            修改后的源代码
        """
        try:
            # 解析源代码
            root = self.parser.parse_source(source_code)
            
            # 查找类
            class_element = None
            for child in root.children:
                if child.element_type == "class" and child.name == class_name:
                    class_element = child
                    break
            
            if not class_element:
                raise ValueError(f"找不到类: {class_name}")
            
            # 查找方法
            method_element = None
            for child in class_element.children:
                if child.element_type == "method" and child.name == method_name:
                    method_element = child
                    break
            
            if not method_element:
                raise ValueError(f"找不到方法: {method_name}")
            
            # 替换方法代码
            lines = source_code.splitlines()
            start_line = method_element.start_position
            end_line = method_element.end_position
            
            if not start_line or not end_line or start_line <= 0 or end_line <= 0 or start_line > len(lines) or end_line > len(lines):
                raise ValueError(f"无法确定方法的位置: {method_name}")
            
            # 构建结果
            result_lines = lines[:start_line-1]
            result_lines.extend(new_method_code.splitlines())
            result_lines.extend(lines[end_line:])
            
            return "\n".join(result_lines)
        
        except Exception as e:
            logger.error(f"修改方法时出错: {str(e)}")
            raise
    
    def add_field(self, source_code: str, class_name: str, field_code: str) -> str:
        """
        向类中添加字段
        
        Args:
            source_code: 源代码
            class_name: 类名
            field_code: 字段代码
            
        Returns:
            修改后的源代码
        """
        try:
            # 解析源代码
            root = self.parser.parse_source(source_code)
            
            # 查找类
            class_element = None
            for child in root.children:
                if child.element_type == "class" and child.name == class_name:
                    class_element = child
                    break
            
            if not class_element:
                raise ValueError(f"找不到类: {class_name}")
            
            # 找到类的开始大括号位置
            lines = source_code.splitlines()
            start_line = class_element.start_position
            
            if not start_line or start_line <= 0 or start_line > len(lines):
                raise ValueError(f"无法确定类的开始位置: {class_name}")
            
            # 找到类的开始大括号
            brace_line = start_line
            while brace_line < len(lines) and '{' not in lines[brace_line-1]:
                brace_line += 1
            
            if brace_line >= len(lines):
                raise ValueError(f"无法找到类的开始大括号: {class_name}")
            
            # 在开始大括号后插入字段
            result_lines = lines[:brace_line]
            
            # 确保字段前有空行
            if result_lines and not lines[brace_line-1].strip().endswith("{"):
                result_lines.append("")
            
            # 添加字段代码
            result_lines.extend(field_code.splitlines())
            
            # 确保字段后有空行
            if not field_code.endswith("\n"):
                result_lines.append("")
            
            # 添加剩余的代码
            result_lines.extend(lines[brace_line:])
            
            return "\n".join(result_lines)
        
        except Exception as e:
            logger.error(f"添加字段时出错: {str(e)}")
            raise
    
    def add_import(self, source_code: str, import_statement: str) -> str:
        """
        添加导入语句
        
        Args:
            source_code: 源代码
            import_statement: 导入语句
            
        Returns:
            修改后的源代码
        """
        try:
            lines = source_code.splitlines()
            
            # 查找最后一个导入语句的位置
            last_import_line = -1
            package_line = -1
            
            for i, line in enumerate(lines):
                if re.match(r'\s*package\s+', line):
                    package_line = i
                elif re.match(r'\s*import\s+', line):
                    last_import_line = i
            
            # 如果没有导入语句，在包声明后添加
            if last_import_line == -1:
                if package_line == -1:
                    # 如果没有包声明，在文件开头添加
                    result_lines = [import_statement]
                    result_lines.extend(lines)
                else:
                    # 在包声明后添加
                    result_lines = lines[:package_line+1]
                    result_lines.append("")
                    result_lines.append(import_statement)
                    result_lines.extend(lines[package_line+1:])
            else:
                # 在最后一个导入语句后添加
                result_lines = lines[:last_import_line+1]
                result_lines.append(import_statement)
                result_lines.extend(lines[last_import_line+1:])
            
            return "\n".join(result_lines)
        
        except Exception as e:
            logger.error(f"添加导入语句时出错: {str(e)}")
            raise
    
    def add_annotation(self, source_code: str, class_name: str, method_name: Optional[str], annotation: str) -> str:
        """
        添加注解
        
        Args:
            source_code: 源代码
            class_name: 类名
            method_name: 方法名，如果为None则添加到类
            annotation: 注解
            
        Returns:
            修改后的源代码
        """
        try:
            # 解析源代码
            root = self.parser.parse_source(source_code)
            
            # 查找类
            class_element = None
            for child in root.children:
                if child.element_type == "class" and child.name == class_name:
                    class_element = child
                    break
            
            if not class_element:
                raise ValueError(f"找不到类: {class_name}")
            
            lines = source_code.splitlines()
            
            if method_name:
                # 查找方法
                method_element = None
                for child in class_element.children:
                    if child.element_type == "method" and child.name == method_name:
                        method_element = child
                        break
                
                if not method_element:
                    raise ValueError(f"找不到方法: {method_name}")
                
                # 在方法声明前添加注解
                start_line = method_element.start_position
                
                if not start_line or start_line <= 0 or start_line > len(lines):
                    raise ValueError(f"无法确定方法的位置: {method_name}")
                
                # 找到方法声明的实际位置（考虑已有注解和Javadoc）
                actual_start = start_line - 1
                while actual_start > 0:
                    line = lines[actual_start-1]
                    if re.match(r'\s*@', line) or re.match(r'\s*/\*\*', line) or re.match(r'\s*\*', line):
                        actual_start -= 1
                    else:
                        break
                
                # 构建结果
                result_lines = lines[:actual_start]
                result_lines.append(annotation)
                result_lines.extend(lines[actual_start:])
            else:
                # 在类声明前添加注解
                start_line = class_element.start_position
                
                if not start_line or start_line <= 0 or start_line > len(lines):
                    raise ValueError(f"无法确定类的位置: {class_name}")
                
                # 找到类声明的实际位置（考虑已有注解和Javadoc）
                actual_start = start_line - 1
                while actual_start > 0:
                    line = lines[actual_start-1]
                    if re.match(r'\s*@', line) or re.match(r'\s*/\*\*', line) or re.match(r'\s*\*', line):
                        actual_start -= 1
                    else:
                        break
                
                # 构建结果
                result_lines = lines[:actual_start]
                result_lines.append(annotation)
                result_lines.extend(lines[actual_start:])
            
            return "\n".join(result_lines)
        
        except Exception as e:
            logger.error(f"添加注解时出错: {str(e)}")
            raise
    
    def update_javadoc(self, source_code: str, class_name: str, method_name: Optional[str], new_javadoc: str) -> str:
        """
        更新Javadoc注释
        
        Args:
            source_code: 源代码
            class_name: 类名
            method_name: 方法名，如果为None则更新类的Javadoc
            new_javadoc: 新的Javadoc注释
            
        Returns:
            修改后的源代码
        """
        try:
            # 解析源代码
            root = self.parser.parse_source(source_code)
            
            # 查找类
            class_element = None
            for child in root.children:
                if child.element_type == "class" and child.name == class_name:
                    class_element = child
                    break
            
            if not class_element:
                raise ValueError(f"找不到类: {class_name}")
            
            lines = source_code.splitlines()
            
            if method_name:
                # 查找方法
                method_element = None
                for child in class_element.children:
                    if child.element_type == "method" and child.name == method_name:
                        method_element = child
                        break
                
                if not method_element:
                    raise ValueError(f"找不到方法: {method_name}")
                
                # 更新方法的Javadoc
                start_line = method_element.start_position
                
                if not start_line or start_line <= 0 or start_line > len(lines):
                    raise ValueError(f"无法确定方法的位置: {method_name}")
                
                # 查找现有Javadoc
                javadoc_start = -1
                javadoc_end = -1
                
                for i in range(start_line-2, -1, -1):
                    if i < 0:
                        break
                    
                    line = lines[i]
                    if re.match(r'\s*/\*\*', line):
                        javadoc_start = i
                        break
                    elif not re.match(r'\s*$', line) and not re.match(r'\s*@', line):
                        # 如果遇到非空行且不是注解，则停止查找
                        break
                
                if javadoc_start >= 0:
                    # 找到Javadoc的结束位置
                    for i in range(javadoc_start, start_line):
                        if re.search(r'\*/', lines[i]):
                            javadoc_end = i
                            break
                
                # 构建结果
                if javadoc_start >= 0 and javadoc_end >= 0:
                    # 替换现有Javadoc
                    result_lines = lines[:javadoc_start]
                    result_lines.extend(new_javadoc.splitlines())
                    result_lines.extend(lines[javadoc_end+1:])
                else:
                    # 添加新的Javadoc
                    actual_start = start_line - 1
                    while actual_start > 0:
                        line = lines[actual_start-1]
                        if re.match(r'\s*@', line):
                            actual_start -= 1
                        else:
                            break
                    
                    result_lines = lines[:actual_start]
                    result_lines.extend(new_javadoc.splitlines())
                    result_lines.extend(lines[actual_start:])
            else:
                # 更新类的Javadoc
                start_line = class_element.start_position
                
                if not start_line or start_line <= 0 or start_line > len(lines):
                    raise ValueError(f"无法确定类的位置: {class_name}")
                
                # 查找现有Javadoc
                javadoc_start = -1
                javadoc_end = -1
                
                for i in range(start_line-2, -1, -1):
                    if i < 0:
                        break
                    
                    line = lines[i]
                    if re.match(r'\s*/\*\*', line):
                        javadoc_start = i
                        break
                    elif not re.match(r'\s*$', line) and not re.match(r'\s*@', line):
                        # 如果遇到非空行且不是注解，则停止查找
                        break
                
                if javadoc_start >= 0:
                    # 找到Javadoc的结束位置
                    for i in range(javadoc_start, start_line):
                        if re.search(r'\*/', lines[i]):
                            javadoc_end = i
                            break
                
                # 构建结果
                if javadoc_start >= 0 and javadoc_end >= 0:
                    # 替换现有Javadoc
                    result_lines = lines[:javadoc_start]
                    result_lines.extend(new_javadoc.splitlines())
                    result_lines.extend(lines[javadoc_end+1:])
                else:
                    # 添加新的Javadoc
                    actual_start = start_line - 1
                    while actual_start > 0:
                        line = lines[actual_start-1]
                        if re.match(r'\s*@', line):
                            actual_start -= 1
                        else:
                            break
                    
                    result_lines = lines[:actual_start]
                    result_lines.extend(new_javadoc.splitlines())
                    result_lines.extend(lines[actual_start:])
            
            return "\n".join(result_lines)
        
        except Exception as e:
            logger.error(f"更新Javadoc时出错: {str(e)}")
            raise

class MarkdownDocumentParser:
    """Markdown文档解析器类"""
    
    def __init__(self):
        """初始化Markdown文档解析器"""
        pass
    
    def parse_file(self, file_path: str) -> DocumentSection:
        """
        解析Markdown文件
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            DocumentSection对象
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_content(content)
        except Exception as e:
            logger.error(f"解析Markdown文件时出错: {str(e)}")
            raise
    
    def parse_content(self, content: str) -> DocumentSection:
        """
        解析Markdown内容
        
        Args:
            content: Markdown内容
            
        Returns:
            DocumentSection对象
        """
        try:
            # 创建根节点
            root = DocumentSection(
                title="Root",
                content="",
                level=0
            )
            
            # 按行解析
            lines = content.splitlines()
            current_section = root
            section_stack = [root]
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # 检查是否是标题行
                header_match = re.match(r'^(#+)\s+(.+)$', line)
                if header_match:
                    level = len(header_match.group(1))
                    title = header_match.group(2).strip()
                    
                    # 创建新章节
                    new_section = DocumentSection(
                        title=title,
                        content="",
                        level=level
                    )
                    
                    # 调整章节层级
                    while len(section_stack) > 1 and section_stack[-1].level >= level:
                        section_stack.pop()
                    
                    # 添加到父章节
                    parent = section_stack[-1]
                    parent.add_child(new_section)
                    
                    # 更新当前章节和栈
                    current_section = new_section
                    section_stack.append(new_section)
                    
                    i += 1
                else:
                    # 收集章节内容
                    content_lines = []
                    while i < len(lines):
                        line = lines[i]
                        
                        # 如果遇到新标题，则停止收集内容
                        if re.match(r'^#+\s+', line):
                            break
                        
                        content_lines.append(line)
                        i += 1
                    
                    # 更新章节内容
                    if content_lines:
                        current_section.content = "\n".join(content_lines).strip()
            
            return root
        except Exception as e:
            logger.error(f"解析Markdown内容时出错: {str(e)}")
            raise

class MarkdownDocumentModifier:
    """Markdown文档修改器类"""
    
    def __init__(self, parser: MarkdownDocumentParser = None):
        """
        初始化Markdown文档修改器
        
        Args:
            parser: Markdown文档解析器，如果为None则创建新的解析器
        """
        self.parser = parser or MarkdownDocumentParser()
    
    def update_section_content(self, content: str, section_title: str, new_content: str) -> str:
        """
        更新章节内容
        
        Args:
            content: Markdown内容
            section_title: 章节标题
            new_content: 新的章节内容
            
        Returns:
            修改后的Markdown内容
        """
        try:
            # 解析文档
            root = self.parser.parse_content(content)
            
            # 查找章节
            section = root.find_section_by_title(section_title)
            if not section:
                raise ValueError(f"找不到章节: {section_title}")
            
            # 更新章节内容
            section.content = new_content
            
            # 重新生成Markdown
            return root.to_markdown()
        except Exception as e:
            logger.error(f"更新章节内容时出错: {str(e)}")
            raise
    
    def add_section(self, content: str, parent_title: str, new_section_title: str, new_section_content: str, level: int) -> str:
        """
        添加章节
        
        Args:
            content: Markdown内容
            parent_title: 父章节标题，如果为None则添加到根节点
            new_section_title: 新章节标题
            new_section_content: 新章节内容
            level: 新章节级别
            
        Returns:
            修改后的Markdown内容
        """
        try:
            # 解析文档
            root = self.parser.parse_content(content)
            
            # 查找父章节
            parent = root
            if parent_title:
                parent = root.find_section_by_title(parent_title)
                if not parent:
                    raise ValueError(f"找不到父章节: {parent_title}")
            
            # 创建新章节
            new_section = DocumentSection(
                title=new_section_title,
                content=new_section_content,
                level=level
            )
            
            # 添加到父章节
            parent.add_child(new_section)
            
            # 重新生成Markdown
            return root.to_markdown()
        except Exception as e:
            logger.error(f"添加章节时出错: {str(e)}")
            raise
    
    def update_table(self, content: str, section_title: str, table_index: int, new_rows: List[List[str]]) -> str:
        """
        更新表格
        
        Args:
            content: Markdown内容
            section_title: 章节标题
            table_index: 表格索引（从0开始）
            new_rows: 新的表格行
            
        Returns:
            修改后的Markdown内容
        """
        try:
            # 解析文档
            root = self.parser.parse_content(content)
            
            # 查找章节
            section = root.find_section_by_title(section_title)
            if not section:
                raise ValueError(f"找不到章节: {section_title}")
            
            # 解析章节内容中的表格
            tables = self._extract_tables(section.content)
            if table_index >= len(tables):
                raise ValueError(f"表格索引超出范围: {table_index}")
            
            # 更新表格
            table = tables[table_index]
            header_row = table[0]
            
            # 构建新表格
            new_table = [header_row]
            new_table.extend(new_rows)
            
            # 替换原表格
            section.content = self._replace_table(section.content, table_index, new_table)
            
            # 重新生成Markdown
            return root.to_markdown()
        except Exception as e:
            logger.error(f"更新表格时出错: {str(e)}")
            raise
    
    def add_table_rows(self, content: str, section_title: str, table_index: int, new_rows: List[List[str]]) -> str:
        """
        添加表格行
        
        Args:
            content: Markdown内容
            section_title: 章节标题
            table_index: 表格索引（从0开始）
            new_rows: 新的表格行
            
        Returns:
            修改后的Markdown内容
        """
        try:
            # 解析文档
            root = self.parser.parse_content(content)
            
            # 查找章节
            section = root.find_section_by_title(section_title)
            if not section:
                raise ValueError(f"找不到章节: {section_title}")
            
            # 解析章节内容中的表格
            tables = self._extract_tables(section.content)
            if table_index >= len(tables):
                raise ValueError(f"表格索引超出范围: {table_index}")
            
            # 更新表格
            table = tables[table_index]
            
            # 构建新表格
            new_table = table.copy()
            new_table.extend(new_rows)
            
            # 替换原表格
            section.content = self._replace_table(section.content, table_index, new_table)
            
            # 重新生成Markdown
            return root.to_markdown()
        except Exception as e:
            logger.error(f"添加表格行时出错: {str(e)}")
            raise
    
    def _extract_tables(self, content: str) -> List[List[List[str]]]:
        """提取内容中的表格"""
        tables = []
        lines = content.splitlines()
        
        i = 0
        while i < len(lines):
            # 查找表格开始
            if i < len(lines) and re.match(r'\s*\|.*\|\s*$', lines[i]):
                table_lines = []
                
                # 收集表格行
                while i < len(lines) and re.match(r'\s*\|.*\|\s*$', lines[i]):
                    table_lines.append(lines[i])
                    i += 1
                
                # 解析表格
                if len(table_lines) >= 2:  # 至少有标题行和分隔行
                    table = []
                    
                    for j, line in enumerate(table_lines):
                        # 跳过分隔行
                        if j == 1 and re.match(r'\s*\|[\s\-:]*\|\s*$', line):
                            continue
                        
                        # 解析行
                        cells = []
                        for cell in line.split('|')[1:-1]:  # 去掉首尾的|
                            cells.append(cell.strip())
                        
                        table.append(cells)
                    
                    tables.append(table)
            else:
                i += 1
        
        return tables
    
    def _replace_table(self, content: str, table_index: int, new_table: List[List[str]]) -> str:
        """替换内容中的表格"""
        lines = content.splitlines()
        result_lines = []
        
        table_count = 0
        i = 0
        
        while i < len(lines):
            # 查找表格开始
            if i < len(lines) and re.match(r'\s*\|.*\|\s*$', lines[i]):
                if table_count == table_index:
                    # 跳过原表格
                    while i < len(lines) and re.match(r'\s*\|.*\|\s*$', lines[i]):
                        i += 1
                    
                    # 添加新表格
                    for j, row in enumerate(new_table):
                        if j == 1:
                            # 添加分隔行
                            separator = '| ' + ' | '.join(['---'] * len(row)) + ' |'
                            result_lines.append(separator)
                        
                        # 添加数据行
                        row_str = '| ' + ' | '.join(row) + ' |'
                        result_lines.append(row_str)
                else:
                    # 保留其他表格
                    while i < len(lines) and re.match(r'\s*\|.*\|\s*$', lines[i]):
                        result_lines.append(lines[i])
                        i += 1
                
                table_count += 1
            else:
                result_lines.append(lines[i])
                i += 1
        
        return '\n'.join(result_lines)

class TestCaseGenerator:
    """测试用例生成器类"""
    
    def __init__(self):
        """初始化测试用例生成器"""
        pass
    
    def generate_test_cases(self, requirement_change: RequirementChange, java_code_elements: List[JavaCodeElement]) -> List[TestCase]:
        """
        根据需求变更和Java代码元素生成测试用例
        
        Args:
            requirement_change: 需求变更
            java_code_elements: Java代码元素列表
            
        Returns:
            测试用例列表
        """
        test_cases = []
        
        # 根据变更类型生成不同的测试用例
        if requirement_change.change_type == ChangeType.ADD_FEATURE:
            test_cases.extend(self._generate_add_feature_test_cases(requirement_change, java_code_elements))
        elif requirement_change.change_type == ChangeType.MODIFY_FEATURE:
            test_cases.extend(self._generate_modify_feature_test_cases(requirement_change, java_code_elements))
        elif requirement_change.change_type == ChangeType.FIX_BUG:
            test_cases.extend(self._generate_fix_bug_test_cases(requirement_change, java_code_elements))
        else:
            test_cases.extend(self._generate_generic_test_cases(requirement_change, java_code_elements))
        
        return test_cases
    
    def _generate_add_feature_test_cases(self, requirement_change: RequirementChange, java_code_elements: List[JavaCodeElement]) -> List[TestCase]:
        """生成添加功能的测试用例"""
        test_cases = []
        
        # 为每个新方法生成测试用例
        for element in java_code_elements:
            if element.element_type == "method":
                # 基本功能测试
                test_cases.append(TestCase(
                    id=f"TC-{element.name}-001",
                    category=requirement_change.feature_name,
                    sub_category="基本機能",
                    item=f"{element.name}の正常動作",
                    conditions=["正常なパラメータを使用"],
                    steps=[
                        f"{element.name}メソッドを呼び出す",
                        "正常なパラメータを渡す"
                    ],
                    expected_results=[
                        "正常に処理が完了すること",
                        "期待される結果が返されること"
                    ]
                ))
                
                # 边界值测试
                test_cases.append(TestCase(
                    id=f"TC-{element.name}-002",
                    category=requirement_change.feature_name,
                    sub_category="境界値",
                    item=f"{element.name}の境界値",
                    conditions=["境界値のパラメータを使用"],
                    steps=[
                        f"{element.name}メソッドを呼び出す",
                        "境界値のパラメータを渡す"
                    ],
                    expected_results=[
                        "正常に処理が完了すること",
                        "境界値が正しく処理されること"
                    ]
                ))
                
                # 异常测试
                test_cases.append(TestCase(
                    id=f"TC-{element.name}-003",
                    category=requirement_change.feature_name,
                    sub_category="例外処理",
                    item=f"{element.name}の例外処理",
                    conditions=["無効なパラメータを使用"],
                    steps=[
                        f"{element.name}メソッドを呼び出す",
                        "無効なパラメータを渡す"
                    ],
                    expected_results=[
                        "適切な例外が発生すること",
                        "エラーメッセージが正しいこと"
                    ]
                ))
        
        # 为每个需求生成测试用例
        for i, req in enumerate(requirement_change.requirements):
            test_cases.append(TestCase(
                id=f"TC-REQ-{i+1:03d}",
                category=requirement_change.feature_name,
                sub_category="要件確認",
                item=f"要件「{req[:30]}...」の確認",
                conditions=["要件に関連する条件を設定"],
                steps=[
                    "要件に関連する機能を実行",
                    "結果を確認"
                ],
                expected_results=[
                    f"要件「{req}」が満たされていること"
                ]
            ))
        
        return test_cases
    
    def _generate_modify_feature_test_cases(self, requirement_change: RequirementChange, java_code_elements: List[JavaCodeElement]) -> List[TestCase]:
        """生成修改功能的测试用例"""
        test_cases = []
        
        # 为每个修改的方法生成测试用例
        for element in java_code_elements:
            if element.element_type == "method":
                # 修改后的功能测试
                test_cases.append(TestCase(
                    id=f"TC-{element.name}-001",
                    category=requirement_change.feature_name,
                    sub_category="変更後の機能",
                    item=f"{element.name}の変更後の動作",
                    conditions=["変更に関連するパラメータを使用"],
                    steps=[
                        f"{element.name}メソッドを呼び出す",
                        "変更に関連するパラメータを渡す"
                    ],
                    expected_results=[
                        "変更後の仕様通りに動作すること",
                        "変更前の機能に影響がないこと"
                    ]
                ))
                
                # 回归测试
                test_cases.append(TestCase(
                    id=f"TC-{element.name}-002",
                    category=requirement_change.feature_name,
                    sub_category="回帰テスト",
                    item=f"{element.name}の変更による影響",
                    conditions=["変更前の機能に関連するパラメータを使用"],
                    steps=[
                        f"{element.name}メソッドを呼び出す",
                        "変更前の機能に関連するパラメータを渡す"
                    ],
                    expected_results=[
                        "変更前の機能が正常に動作すること",
                        "変更による副作用がないこと"
                    ]
                ))
        
        # 为每个需求生成测试用例
        for i, req in enumerate(requirement_change.requirements):
            test_cases.append(TestCase(
                id=f"TC-REQ-{i+1:03d}",
                category=requirement_change.feature_name,
                sub_category="要件確認",
                item=f"要件「{req[:30]}...」の確認",
                conditions=["要件に関連する条件を設定"],
                steps=[
                    "要件に関連する機能を実行",
                    "結果を確認"
                ],
                expected_results=[
                    f"要件「{req}」が満たされていること"
                ]
            ))
        
        return test_cases
    
    def _generate_fix_bug_test_cases(self, requirement_change: RequirementChange, java_code_elements: List[JavaCodeElement]) -> List[TestCase]:
        """生成修复Bug的测试用例"""
        test_cases = []
        
        # 为每个修复的方法生成测试用例
        for element in java_code_elements:
            if element.element_type == "method":
                # Bug修复验证
                test_cases.append(TestCase(
                    id=f"TC-{element.name}-001",
                    category=requirement_change.feature_name,
                    sub_category="バグ修正",
                    item=f"{element.name}のバグ修正確認",
                    conditions=["バグが発生する条件を再現"],
                    steps=[
                        f"{element.name}メソッドを呼び出す",
                        "バグが発生するパラメータを渡す"
                    ],
                    expected_results=[
                        "バグが修正されていること",
                        "正常に処理が完了すること"
                    ]
                ))
                
                # 回归测试
                test_cases.append(TestCase(
                    id=f"TC-{element.name}-002",
                    category=requirement_change.feature_name,
                    sub_category="回帰テスト",
                    item=f"{element.name}の修正による影響",
                    conditions=["正常な機能に関連するパラメータを使用"],
                    steps=[
                        f"{element.name}メソッドを呼び出す",
                        "正常な機能に関連するパラメータを渡す"
                    ],
                    expected_results=[
                        "正常な機能が影響を受けていないこと",
                        "修正による副作用がないこと"
                    ]
                ))
        
        # 为每个需求生成测试用例
        for i, req in enumerate(requirement_change.requirements):
            test_cases.append(TestCase(
                id=f"TC-REQ-{i+1:03d}",
                category=requirement_change.feature_name,
                sub_category="要件確認",
                item=f"要件「{req[:30]}...」の確認",
                conditions=["要件に関連する条件を設定"],
                steps=[
                    "要件に関連する機能を実行",
                    "結果を確認"
                ],
                expected_results=[
                    f"要件「{req}」が満たされていること"
                ]
            ))
        
        return test_cases
    
    def _generate_generic_test_cases(self, requirement_change: RequirementChange, java_code_elements: List[JavaCodeElement]) -> List[TestCase]:
        """生成通用测试用例"""
        test_cases = []
        
        # 为每个方法生成测试用例
        for element in java_code_elements:
            if element.element_type == "method":
                # 基本功能测试
                test_cases.append(TestCase(
                    id=f"TC-{element.name}-001",
                    category=requirement_change.feature_name,
                    sub_category="基本機能",
                    item=f"{element.name}の動作確認",
                    conditions=["通常の条件を設定"],
                    steps=[
                        f"{element.name}メソッドを呼び出す",
                        "適切なパラメータを渡す"
                    ],
                    expected_results=[
                        "正常に処理が完了すること",
                        "期待される結果が返されること"
                    ]
                ))
        
        # 为每个需求生成测试用例
        for i, req in enumerate(requirement_change.requirements):
            test_cases.append(TestCase(
                id=f"TC-REQ-{i+1:03d}",
                category=requirement_change.feature_name,
                sub_category="要件確認",
                item=f"要件「{req[:30]}...」の確認",
                conditions=["要件に関連する条件を設定"],
                steps=[
                    "要件に関連する機能を実行",
                    "結果を確認"
                ],
                expected_results=[
                    f"要件「{req}」が満たされていること"
                ]
            ))
        
        return test_cases

class DeploymentGuideGenerator:
    """部署指南生成器类"""
    
    def __init__(self):
        """初始化部署指南生成器"""
        pass
    
    def generate_deployment_guide(self, requirement_change: RequirementChange, affected_files: List[str]) -> str:
        """
        生成部署指南
        
        Args:
            requirement_change: 需求变更
            affected_files: 受影响的文件列表
            
        Returns:
            部署指南Markdown内容
        """
        now = datetime.datetime.now()
        
        lines = []
        
        # 标题和元数据
        lines.append(f"# 部署指南: {requirement_change.feature_name}")
        lines.append("")
        lines.append(f"- 変更タイプ: {requirement_change.change_type.value}")
        lines.append(f"- 作成日: {now.strftime('%Y年%m月%d日')}")
        lines.append("")
        
        # 变更描述
        lines.append("## 変更内容")
        lines.append("")
        lines.append(requirement_change.description)
        lines.append("")
        
        # 受影响的文件
        lines.append("## 影響を受けるファイル")
        lines.append("")
        for file in affected_files:
            lines.append(f"- `{file}`")
        lines.append("")
        
        # 部署步骤
        lines.append("## デプロイ手順")
        lines.append("")
        
        # 根据变更类型生成不同的部署步骤
        if requirement_change.change_type == ChangeType.ADD_FEATURE:
            lines.extend(self._generate_add_feature_steps(requirement_change, affected_files))
        elif requirement_change.change_type == ChangeType.MODIFY_FEATURE:
            lines.extend(self._generate_modify_feature_steps(requirement_change, affected_files))
        elif requirement_change.change_type == ChangeType.FIX_BUG:
            lines.extend(self._generate_fix_bug_steps(requirement_change, affected_files))
        else:
            lines.extend(self._generate_generic_steps(requirement_change, affected_files))
        
        # 回滚计划
        lines.append("## ロールバック計画")
        lines.append("")
        lines.append("デプロイに問題が発生した場合は、以下の手順でロールバックを行ってください：")
        lines.append("")
        lines.append("1. 前バージョンのバックアップを使用して、影響を受けるファイルを復元します。")
        lines.append("2. アプリケーションを再起動します。")
        lines.append("3. ロールバックが成功したことを確認します。")
        lines.append("")
        
        # 验证步骤
        lines.append("## 検証手順")
        lines.append("")
        lines.append("デプロイ後、以下の手順で変更が正常に適用されたことを確認してください：")
        lines.append("")
        
        for i, req in enumerate(requirement_change.requirements):
            lines.append(f"{i+1}. 要件「{req}」が満たされていることを確認します。")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_add_feature_steps(self, requirement_change: RequirementChange, affected_files: List[str]) -> List[str]:
        """生成添加功能的部署步骤"""
        steps = []
        
        steps.append("### 準備")
        steps.append("")
        steps.append("1. デプロイ前に、影響を受けるファイルのバックアップを作成します。")
        steps.append("2. テスト環境でデプロイをテストし、問題がないことを確認します。")
        steps.append("")
        
        steps.append("### デプロイ")
        steps.append("")
        steps.append("1. アプリケーションをメンテナンスモードに設定します（必要な場合）。")
        steps.append("2. 以下のファイルを本番環境にコピーします：")
        steps.append("")
        
        # 按文件类型分类
        java_files = [f for f in affected_files if f.endswith(".java")]
        config_files = [f for f in affected_files if f.endswith(".xml") or f.endswith(".properties") or f.endswith(".yml")]
        static_files = [f for f in affected_files if f.endswith(".html") or f.endswith(".css") or f.endswith(".js")]
        other_files = [f for f in affected_files if f not in java_files and f not in config_files and f not in static_files]
        
        if java_files:
            steps.append("   **Javaファイル:**")
            for file in java_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if config_files:
            steps.append("   **設定ファイル:**")
            for file in config_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if static_files:
            steps.append("   **静的ファイル:**")
            for file in static_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if other_files:
            steps.append("   **その他のファイル:**")
            for file in other_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        steps.append("3. アプリケーションをビルドします。")
        steps.append("4. アプリケーションを再起動します。")
        steps.append("5. メンテナンスモードを解除します（設定した場合）。")
        steps.append("")
        
        return steps
    
    def _generate_modify_feature_steps(self, requirement_change: RequirementChange, affected_files: List[str]) -> List[str]:
        """生成修改功能的部署步骤"""
        steps = []
        
        steps.append("### 準備")
        steps.append("")
        steps.append("1. デプロイ前に、影響を受けるファイルのバックアップを作成します。")
        steps.append("2. テスト環境でデプロイをテストし、問題がないことを確認します。")
        steps.append("3. 変更による影響範囲を確認し、関連するテストを実施します。")
        steps.append("")
        
        steps.append("### デプロイ")
        steps.append("")
        steps.append("1. アプリケーションをメンテナンスモードに設定します（必要な場合）。")
        steps.append("2. 以下のファイルを本番環境にコピーします：")
        steps.append("")
        
        # 按文件类型分类
        java_files = [f for f in affected_files if f.endswith(".java")]
        config_files = [f for f in affected_files if f.endswith(".xml") or f.endswith(".properties") or f.endswith(".yml")]
        static_files = [f for f in affected_files if f.endswith(".html") or f.endswith(".css") or f.endswith(".js")]
        other_files = [f for f in affected_files if f not in java_files and f not in config_files and f not in static_files]
        
        if java_files:
            steps.append("   **Javaファイル:**")
            for file in java_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if config_files:
            steps.append("   **設定ファイル:**")
            for file in config_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if static_files:
            steps.append("   **静的ファイル:**")
            for file in static_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if other_files:
            steps.append("   **その他のファイル:**")
            for file in other_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        steps.append("3. アプリケーションをビルドします。")
        steps.append("4. アプリケーションを再起動します。")
        steps.append("5. メンテナンスモードを解除します（設定した場合）。")
        steps.append("6. 変更が正常に適用されたことを確認します。")
        steps.append("")
        
        return steps
    
    def _generate_fix_bug_steps(self, requirement_change: RequirementChange, affected_files: List[str]) -> List[str]:
        """生成修复Bug的部署步骤"""
        steps = []
        
        steps.append("### 準備")
        steps.append("")
        steps.append("1. デプロイ前に、影響を受けるファイルのバックアップを作成します。")
        steps.append("2. テスト環境でデプロイをテストし、バグが修正されたことを確認します。")
        steps.append("3. 修正による副作用がないことを確認します。")
        steps.append("")
        
        steps.append("### デプロイ")
        steps.append("")
        steps.append("1. アプリケーションをメンテナンスモードに設定します（必要な場合）。")
        steps.append("2. 以下のファイルを本番環境にコピーします：")
        steps.append("")
        
        # 按文件类型分类
        java_files = [f for f in affected_files if f.endswith(".java")]
        config_files = [f for f in affected_files if f.endswith(".xml") or f.endswith(".properties") or f.endswith(".yml")]
        static_files = [f for f in affected_files if f.endswith(".html") or f.endswith(".css") or f.endswith(".js")]
        other_files = [f for f in affected_files if f not in java_files and f not in config_files and f not in static_files]
        
        if java_files:
            steps.append("   **Javaファイル:**")
            for file in java_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if config_files:
            steps.append("   **設定ファイル:**")
            for file in config_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if static_files:
            steps.append("   **静的ファイル:**")
            for file in static_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        if other_files:
            steps.append("   **その他のファイル:**")
            for file in other_files:
                steps.append(f"   - `{file}`")
            steps.append("")
        
        steps.append("3. アプリケーションをビルドします。")
        steps.append("4. アプリケーションを再起動します。")
        steps.append("5. メンテナンスモードを解除します（設定した場合）。")
        steps.append("6. バグが修正されたことを確認します。")
        steps.append("")
        
        return steps
    
    def _generate_generic_steps(self, requirement_change: RequirementChange, affected_files: List[str]) -> List[str]:
        """生成通用部署步骤"""
        steps = []
        
        steps.append("### 準備")
        steps.append("")
        steps.append("1. デプロイ前に、影響を受けるファイルのバックアップを作成します。")
        steps.append("2. テスト環境でデプロイをテストし、問題がないことを確認します。")
        steps.append("")
        
        steps.append("### デプロイ")
        steps.append("")
        steps.append("1. アプリケーションをメンテナンスモードに設定します（必要な場合）。")
        steps.append("2. 以下のファイルを本番環境にコピーします：")
        steps.append("")
        
        for file in affected_files:
            steps.append(f"   - `{file}`")
        steps.append("")
        
        steps.append("3. アプリケーションをビルドします。")
        steps.append("4. アプリケーションを再起動します。")
        steps.append("5. メンテナンスモードを解除します（設定した場合）。")
        steps.append("")
        
        return steps

class AutoUpdateSystem:
    """自动更新系统类，集成需求变更、代码修改、文档更新和测试生成"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化自动更新系统
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 创建子模块
        self.java_parser = JavaCodeParser()
        self.java_modifier = JavaCodeModifier(self.java_parser)
        self.markdown_parser = MarkdownDocumentParser()
        self.markdown_modifier = MarkdownDocumentModifier(self.markdown_parser)
        self.test_generator = TestCaseGenerator()
        self.deployment_generator = DeploymentGuideGenerator()
    
    def process_requirement_change(self, requirement_change_input: Union[str, Dict[str, Any], RequirementChange], 
                                  code_dir: str, doc_dir: str, output_dir: str) -> Dict[str, Any]:
        """
        处理需求变更
        
        Args:
            requirement_change_input: 需求变更输入（YAML字符串、JSON字符串、字典或RequirementChange对象）
            code_dir: 代码目录
            doc_dir: 文档目录
            output_dir: 输出目录
            
        Returns:
            处理结果字典
        """
        try:
            # 解析需求变更
            if isinstance(requirement_change_input, str):
                if requirement_change_input.strip().startswith("{"):
                    requirement_change = RequirementChange.from_json(requirement_change_input)
                else:
                    requirement_change = RequirementChange.from_yaml(requirement_change_input)
            elif isinstance(requirement_change_input, dict):
                requirement_change = RequirementChange.from_dict(requirement_change_input)
            elif isinstance(requirement_change_input, RequirementChange):
                requirement_change = requirement_change_input
            else:
                raise ValueError("不支持的需求变更输入类型")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 处理受影响的组件
            affected_files = []
            modified_code_elements = []
            
            for component in requirement_change.affected_components:
                if component.endswith(".java"):
                    # 处理Java文件
                    java_file_path = os.path.join(code_dir, component)
                    if os.path.exists(java_file_path):
                        # 解析Java文件
                        code_element = self.java_parser.parse_file(java_file_path)
                        modified_code_elements.append(code_element)
                        affected_files.append(component)
                        
                        # TODO: 根据需求变更修改Java代码
                        # 这里需要根据实际需求实现代码修改逻辑
            
            # 处理设计文档章节
            for section in requirement_change.design_doc_sections:
                # 查找对应的文档文件
                doc_files = self._find_doc_files(doc_dir, section)
                
                for doc_file in doc_files:
                    # 解析文档
                    doc_path = os.path.join(doc_dir, doc_file)
                    if os.path.exists(doc_path):
                        # TODO: 根据需求变更修改文档
                        # 这里需要根据实际需求实现文档修改逻辑
                        affected_files.append(doc_file)
            
            # 生成测试仕様書
            test_spec = TestSpecification(
                title=f"{requirement_change.feature_name} テスト仕様書",
                version="1.0",
                created_date=datetime.datetime.now(),
                updated_date=datetime.datetime.now(),
                author="自動生成",
                description=requirement_change.description,
                scope=f"{requirement_change.feature_name}の機能テスト",
                prerequisites=["テスト環境が正常に動作していること"]
            )
            
            # 生成测试用例
            test_cases = self.test_generator.generate_test_cases(requirement_change, modified_code_elements)
            for test_case in test_cases:
                test_spec.add_test_case(test_case)
            
            # 保存测试仕様書
            test_spec_path = os.path.join(output_dir, f"{requirement_change.feature_name}_test_spec.md")
            with open(test_spec_path, "w", encoding="utf-8") as f:
                f.write(test_spec.to_markdown())
            
            # 生成部署指南
            deployment_guide = self.deployment_generator.generate_deployment_guide(requirement_change, affected_files)
            deployment_guide_path = os.path.join(output_dir, f"{requirement_change.feature_name}_deployment_guide.md")
            with open(deployment_guide_path, "w", encoding="utf-8") as f:
                f.write(deployment_guide)
            
            # 返回处理结果
            return {
                "requirement_change": requirement_change.to_dict(),
                "affected_files": affected_files,
                "test_spec_path": test_spec_path,
                "deployment_guide_path": deployment_guide_path,
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"处理需求变更时出错: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _find_doc_files(self, doc_dir: str, section_name: str) -> List[str]:
        """查找包含指定章节的文档文件"""
        result = []
        
        # 遍历文档目录
        for root, _, files in os.walk(doc_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, doc_dir)
                    
                    # 读取文件内容
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # 解析文档
                        doc = self.markdown_parser.parse_content(content)
                        
                        # 查找章节
                        if doc.find_section_by_title(section_name):
                            result.append(rel_path)
                    except Exception as e:
                        logger.warning(f"读取文档文件时出错: {str(e)}")
        
        return result

# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="自动化需求变更处理工具")
    parser.add_argument("input", help="需求变更输入文件路径（YAML或JSON格式）")
    parser.add_argument("--code-dir", required=True, help="代码目录")
    parser.add_argument("--doc-dir", required=True, help="文档目录")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 读取需求变更输入
    with open(args.input, "r", encoding="utf-8") as f:
        requirement_change_input = f.read()
    
    # 创建自动更新系统
    system = AutoUpdateSystem()
    
    # 处理需求变更
    result = system.process_requirement_change(
        requirement_change_input=requirement_change_input,
        code_dir=args.code_dir,
        doc_dir=args.doc_dir,
        output_dir=args.output_dir
    )
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
