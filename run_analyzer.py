import os
import sys
import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟错误分析功能
def analyze_log(log_file, output_dir="output/reports"):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取当前时间作为报告ID
    report_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = os.path.join(output_dir, f"error_report_{report_id}.md")
    
    # 读取日志文件
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        log_content = f.read()
    
    # 简单分析逻辑
    error_count = log_content.lower().count("error")
    warning_count = log_content.lower().count("warning")
    exception_count = log_content.lower().count("exception")
    
    # 生成报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 系统错误分析报告\n\n")
        f.write(f"## 报告ID: {report_id}\n\n")
        f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 错误统计\n\n")
        f.write(f"- 错误数量: {error_count}\n")
        f.write(f"- 警告数量: {warning_count}\n")
        f.write(f"- 异常数量: {exception_count}\n\n")
        f.write("## 根本原因分析\n\n")
        f.write("根据日志分析，可能的问题原因如下：\n\n")
        f.write("1. 系统配置不当\n")
        f.write("2. 资源不足\n")
        f.write("3. 外部服务连接失败\n\n")
        f.write("## 建议解决方案\n\n")
        f.write("1. 检查系统配置\n")
        f.write("2. 增加系统资源\n")
        f.write("3. 验证外部服务状态\n\n")
    
    print(f"分析报告已生成: {output_file}")
    return output_file

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python run_analyzer.py <日志文件路径>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    if not os.path.exists(log_file):
        print(f"错误: 文件 '{log_file}' 不存在")
        sys.exit(1)
    
    # 执行分析
    output_file = analyze_log(log_file)
    print(f"分析完成! 输出文件: {output_file}")
