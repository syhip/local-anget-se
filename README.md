# 本地大模型辅助系统

## 项目概述

本项目是一个基于本地大模型的辅助系统，旨在帮助用户自动处理设计文档和代码，解决问题并自动化维护工作。系统具有以下核心功能：

1. **文档转换模块**：将Word、Excel、PDF等格式文档转换为Markdown格式，便于大模型处理
2. **错误分析与报告生成模块**：根据系统日志自动定位问题并生成标准调查报告
3. **需求变更自动化处理模块**：根据需求变更自动修改设计文档和代码，生成测试文档和部署流程

系统设计为完全离线运行，适用于Windows环境，支持一键部署和运行。

## 目录结构

```
local-llm-assistant/
├── system_architecture.md        # 系统整体架构设计
├── modules/                      # 功能模块
│   ├── document_conversion/      # 文档转换模块
│   │   ├── document_conversion_module.py
│   │   └── document_conversion_comparison.md
│   ├── error_report/             # 错误分析与报告生成模块
│   │   └── error_report_module.py
│   └── auto_update/              # 需求变更自动化处理模块
│       ├── auto_update_module.py
│       └── auto_update_module_design.md
├── test_data/                    # 测试数据
│   ├── source_code/              # 源代码样本
│   ├── documents/                # 文档样本
│   │   ├── pdf/
│   │   ├── word/
│   │   └── excel/
│   ├── logs/                     # 日志样本
│   └── test_cases/               # 测试用例
├── test_reports/                 # 测试报告
│   ├── test_execution_report.md  # 测试执行报告
│   └── test_analysis_report.md   # 测试分析报告
└── README.md                     # 项目说明文档
```

## 环境要求

- **操作系统**：Windows 10 或更高版本
- **Python**：3.8 或更高版本
- **内存**：至少 8GB RAM（推荐 16GB 以上）
- **存储**：至少 10GB 可用空间
- **CPU**：4核或更高（推荐8核以上）
- **GPU**：可选，但推荐用于加速大模型推理

## 安装指南

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/local-llm-assistant.git
cd local-llm-assistant
```

### 2. 创建虚拟环境

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 下载模型（如果需要）

```bash
python scripts/download_models.py
```

## 使用指南

### 文档转换模块

文档转换模块支持将Word、Excel、PDF等格式转换为Markdown格式，便于大模型处理。

```bash
python -m modules.document_conversion.run --input path/to/document --output path/to/output
```

参数说明：
- `--input`：输入文档路径，支持单个文件或目录
- `--output`：输出目录，默认为`output/markdown`
- `--format`：指定输出格式，默认为`markdown`
- `--engine`：指定转换引擎，可选`markitdown`（默认）、`marker`或`python`

示例：
```bash
# 转换单个PDF文件
python -m modules.document_conversion.run --input test_data/documents/pdf/japanese_financial_holding_groups.pdf

# 批量转换目录下所有文档
python -m modules.document_conversion.run --input test_data/documents/ --output output/batch_convert
```

### 错误分析与报告生成模块

错误分析模块可以分析系统日志，自动定位问题并生成标准调查报告。

```bash
python -m modules.error_report.run --log path/to/logfile --output path/to/report
```

参数说明：
- `--log`：日志文件路径，支持单个文件或目录
- `--output`：输出报告路径，默认为`output/reports`
- `--format`：报告格式，可选`markdown`（默认）、`html`、`pdf`或`json`
- `--template`：报告模板，可选`japanese`（默认）或`standard`

示例：
```bash
# 分析单个日志文件并生成报告
python -m modules.error_report.run --log test_data/logs/application_logs/sample_java_log.log

# 生成PDF格式报告
python -m modules.error_report.run --log test_data/logs/application_logs/sample_java_log.log --format pdf
```

### 需求变更自动化处理模块

需求变更模块可以根据需求变更自动修改设计文档和代码，生成测试文档和部署流程。

```bash
python -m modules.auto_update.run --source path/to/source --design path/to/design --requirement path/to/requirement
```

参数说明：
- `--source`：源代码目录
- `--design`：设计文档路径
- `--requirement`：需求变更描述文件
- `--output`：输出目录，默认为`output/updated`
- `--generate-test`：是否生成测试文档，默认为`True`
- `--generate-deploy`：是否生成部署文档，默认为`True`

示例：
```bash
# 根据需求变更更新代码和文档
python -m modules.auto_update.run --source test_data/source_code/bank_manage --design test_data/documents/word/financial_system_design_doc_ja.md --requirement examples/new_feature.md
```

## 测试指南

本项目包含完整的测试用例和测试数据，可以用于验证系统功能。

### 运行单元测试

```bash
python -m unittest discover tests
```

### 运行集成测试

```bash
python tests/integration_test.py
```

### 自定义测试

您可以使用提供的测试数据和测试用例进行自定义测试：

1. 文档转换测试：
   - 测试数据位于`test_data/documents/`
   - 测试用例说明位于`test_data/test_cases/document_conversion_tests/`

2. 错误分析测试：
   - 测试数据位于`test_data/logs/`
   - 测试用例说明位于`test_data/test_cases/error_analysis_tests/`

3. 需求变更测试：
   - 测试数据位于`test_data/source_code/`和`test_data/documents/`
   - 测试用例说明位于`test_data/test_cases/auto_update_tests/`

## 性能测试

性能测试可以评估系统在处理大量数据时的表现：

```bash
python tests/performance_test.py --module document_conversion --size large
python tests/performance_test.py --module error_report --size large
python tests/performance_test.py --module auto_update --size large
```

## 常见问题

### Q: 系统支持哪些文档格式？
A: 系统支持Word (.doc, .docx)、Excel (.xls, .xlsx)、PDF (.pdf)、PowerPoint (.ppt, .pptx)和文本文件(.txt)等格式。

### Q: 如何处理大型文档？
A: 对于超过50MB的大型文档，建议使用`--chunk-size`参数进行分块处理，例如：
```bash
python -m modules.document_conversion.run --input large_document.pdf --chunk-size 10
```

### Q: 系统能处理多语言文档吗？
A: 是的，系统对日文有特别优化，同时也支持英文、中文等多种语言。

### Q: 如何自定义错误报告模板？
A: 您可以在`modules/error_report/templates/`目录下创建自定义模板，然后通过`--template`参数指定。

## 贡献指南

欢迎贡献代码或提出建议！请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参见 [LICENSE](LICENSE) 文件。

## 联系方式

如有任何问题或建议，请通过以下方式联系我们：

- 项目仓库：[GitHub Issues](https://github.com/yourusername/local-llm-assistant/issues)
- 电子邮件：your.email@example.com

---

感谢您使用本地大模型辅助系统！希望它能为您的工作带来便利。
