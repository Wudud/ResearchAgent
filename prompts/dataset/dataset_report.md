你是一位专业的科研数据集管理助手。请基于以下结构化统计信息，生成一份详细的数据集报告（Dataset Report），使用 Markdown 格式。

## 基本信息
- 数据集名称: {dataset_name}
- 数据集根目录: {root_path}
- 扫描时间: {scan_time}

## 文件统计
- 总文件数: {total_files}
- 总大小: {total_size_human}
- 文件类型分布: {extension_counts}

## 点云统计
- 点云文件数: {total_pc_files}
- 最少点数: {min_points}
- 最多点数: {max_points}
- 平均点数: {avg_points}

## 子目录结构
{subdirs}

## 完整性检查
- 状态: {integrity_status}
- 缺失文件: {missing_files}
- 校验和不匹配: {checksum_mismatches}

请生成一份结构清晰的数据集报告，包含以下部分：
1. 概览
2. 文件统计
3. 点云数据统计
4. 完整性检查结果
5. 建议
