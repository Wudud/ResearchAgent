你是一位专业的科研数据集管理者。请基于以下信息，生成一份符合 HuggingFace Dataset Card 规范的 Markdown 文档。

## 数据集信息

- 数据集名称: {dataset_name}
- 版本: {version}
- 根目录: {root_path}
- 创建日期: {creation_date}

## 文件统计
- 总文件数: {total_files}
- 总大小: {total_size_human}
- 文件类型: {extension_counts}

## 点云信息
- 点云文件数: {total_pc_files}
- PLY 文件: {ply_files}
- PCD 文件: {pcd_files}
- 点数范围: {min_points} - {max_points}
- 平均点数: {avg_points}

## 目录结构
{subdirs}

请生成一份完整的 Dataset Card，包含以下标准章节：
1. Dataset Description（数据集描述）
2. Dataset Structure（数据集结构）
3. Data Instances（数据实例信息）
4. Data Fields（数据字段说明）
5. Data Splits（数据划分，如无可省略）
6. Dataset Creation（数据集创建，包括采集方法、标注方法等）
7. Considerations for Using the Data（使用注意事项）
8. Additional Information（其他信息）
