# 本地大模型辅助系统

## 项目概述

本地大模型辅助系统是一个基于开源大模型（如ChatGLM、Gemini等）的完全离线运行的智能辅助工具，专为处理设计文档和代码文件而设计。系统能够自动根据设计文档和代码来解决问题，帮助运维人员通过报错信息自动定位问题，并在需求变更时自动修改设计书和代码。

## 主要功能

1. **文档转换**：将Word、Excel、PDF等格式文档转换为Markdown格式
2. **错误分析与报告生成**：根据系统报错日志自动定位问题并生成调查报告
3. **需求变更自动化处理**：根据需求变更自动修改设计文档和代码，生成测试文档和部署流程

## 系统要求

- 操作系统：Windows 10/11
- Python版本：3.8+（已在Python 3.12上测试通过）
- 基本Python库：numpy, pandas, matplotlib, beautifulsoup4, requests等

## 快速开始

### 环境准备

```bash
# 安装必要的依赖
pip install numpy pandas matplotlib
pip install beautifulsoup4 requests
pip install python-docx PyPDF2 openpyxl
```

### 创建必要的目录结构

```bash
# 确保输出目录存在
mkdir output
mkdir output\reports
mkdir output\converted
mkdir output\updated
```

### 运行文档转换模块

```bash
python run_converter.py test_data/documents/pdf/japanese_financial_holding_groups.pdf
```

### 运行错误分析模块

```bash
python run_analyzer.py test_data/logs/sample_java_log.log
```

### 运行需求变更自动化处理模块

```bash
python run_updater.py test_data/source_code/bank_manage test_data/documents/word/financial_system_design_doc_ja.md
```

## 文件结构

```
local-llm-assistant/
├── modules/                  # 功能模块目录
│   ├── document_conversion/  # 文档转换模块
│   ├── error_report/         # 错误分析与报告生成模块
│   └── auto_update/          # 需求变更自动化处理模块
├── test_data/                # 测试数据
│   ├── source_code/          # 源代码样例
│   ├── documents/            # 文档样例
│   └── logs/                 # 日志样例
├── output/                   # 输出目录
│   ├── reports/              # 生成的报告
│   ├── converted/            # 转换后的文档
│   └── updated/              # 更新后的代码和文档
├── run_converter.py          # 文档转换模块运行脚本
├── run_analyzer.py           # 错误分析模块运行脚本
├── run_updater.py            # 需求变更自动化处理模块运行脚本
└── README.md                 # 项目说明文档
```

## 简化运行脚本说明

为了简化系统运行并避免复杂的依赖问题，我们提供了三个独立的运行脚本：

1. **run_converter.py**：文档转换模块的简化运行脚本
2. **run_analyzer.py**：错误分析模块的简化运行脚本
3. **run_updater.py**：需求变更自动化处理模块的简化运行脚本

这些脚本避免了复杂的模块导入和依赖问题，可以在大多数环境中顺利运行。

## 常见问题

### Q: 运行脚本时出现"ModuleNotFoundError"错误
A: 请确保已安装所有必要的依赖库。可以使用以下命令安装：
```bash
pip install numpy pandas matplotlib beautifulsoup4 requests python-docx PyPDF2 openpyxl
```

### Q: 在PowerShell中激活虚拟环境时出现权限错误
A: 这是由于PowerShell的执行策略限制。您可以选择以下方法之一解决：
1. 使用命令提示符(CMD)而不是PowerShell
2. 在PowerShell中运行 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`
3. 不使用虚拟环境，直接在全局Python环境中安装依赖并运行系统

### Q: 找不到输入文件
A: 请确保文件路径正确，并且文件确实存在。可以使用绝对路径来避免路径问题。

## 联系与支持

如有任何问题或需要进一步的支持，请通过GitHub Issues提交问题。
