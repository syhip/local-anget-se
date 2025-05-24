import os
import sys
import datetime
import shutil

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟需求变更自动化处理功能
def process_requirement_change(source_dir, design_doc, output_dir="output/updated"):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建时间戳
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 创建输出子目录
    code_output_dir = os.path.join(output_dir, f"code_{timestamp}")
    doc_output_dir = os.path.join(output_dir, f"docs_{timestamp}")
    os.makedirs(code_output_dir, exist_ok=True)
    os.makedirs(doc_output_dir, exist_ok=True)
    
    # 读取设计文档
    with open(design_doc, 'r', encoding='utf-8', errors='ignore') as f:
        design_content = f.read()
    
    # 模拟代码更新
    # 简单复制源代码目录的结构
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.java'):
                # 计算相对路径
                rel_path = os.path.relpath(root, source_dir)
                # 创建目标目录
                target_dir = os.path.join(code_output_dir, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                # 复制并修改文件
                source_file = os.path.join(root, file)
                target_file = os.path.join(target_dir, file)
                
                with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 添加自动更新注释
                updated_content = f"// 自动更新于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                updated_content += f"// 基于需求变更自动修改\n"
                updated_content += content
                
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
    
    # 生成更新后的设计文档
    updated_design_doc = os.path.join(doc_output_dir, "updated_design.md")
    with open(updated_design_doc, 'w', encoding='utf-8') as f:
        f.write("# 更新后的设计文档\n\n")
        f.write(f"## 更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 原始设计内容\n\n")
        f.write(design_content)
        f.write("\n\n## 需求变更说明\n\n")
        f.write("1. 根据新需求，更新了系统架构\n")
        f.write("2. 修改了数据模型\n")
        f.write("3. 优化了业务流程\n\n")
    
    # 生成测试文档
    test_doc = os.path.join(doc_output_dir, "test_plan.md")
    with open(test_doc, 'w', encoding='utf-8') as f:
        f.write("# 测试计划\n\n")
        f.write(f"## 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 测试范围\n\n")
        f.write("1. 单元测试\n")
        f.write("2. 集成测试\n")
        f.write("3. 系统测试\n\n")
        f.write("## 测试用例\n\n")
        f.write("### TC001: 验证登录功能\n")
        f.write("- 前置条件: 系统正常运行\n")
        f.write("- 步骤: 输入用户名和密码\n")
        f.write("- 预期结果: 成功登录系统\n\n")
    
    print(f"代码已更新: {code_output_dir}")
    print(f"文档已更新: {doc_output_dir}")
    return code_output_dir, doc_output_dir

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 3:
        print("用法: python run_updater.py <源代码目录> <设计文档路径>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    design_doc = sys.argv[2]
    
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        print(f"错误: 目录 '{source_dir}' 不存在")
        sys.exit(1)
    
    if not os.path.exists(design_doc):
        print(f"错误: 文件 '{design_doc}' 不存在")
        sys.exit(1)
    
    # 执行需求变更处理
    code_dir, doc_dir = process_requirement_change(source_dir, design_doc)
    print(f"处理完成! 更新的代码: {code_dir}")
    print(f"处理完成! 更新的文档: {doc_dir}")
