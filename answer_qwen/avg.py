import os
import json

def calculate_final_score_average(folder_path):
    # 初始化变量：存储总分和有效文件数量
    total_score = 0.0
    valid_file_count = 0
    error_files = []  # 记录读取失败的文件（如格式错误、缺少字段）

    # 遍历文件夹内所有文件
    for filename in os.listdir(folder_path):
        # 仅处理后缀为.json的文件
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            try:
                # 读取JSON文件
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 提取final_score字段，确保为数值类型
                score = data.get("final_score")
                if score is None:
                    error_files.append(f"{filename} - 缺少'final_score'字段")
                    continue
                if not isinstance(score, (int, float)):
                    error_files.append(f"{filename} - 'final_score'不是数值（当前类型：{type(score).__name__}）")
                    continue
                
                # 累加分数和计数
                total_score += score
                valid_file_count += 1

            except json.JSONDecodeError:
                error_files.append(f"{filename} - JSON格式错误（文件损坏或内容非法）")
            except Exception as e:
                error_files.append(f"{filename} - 其他错误：{str(e)}")

    # 计算平均值
    if valid_file_count == 0:
        print("未找到有效数据，无法计算平均值。")
        average = 0.0
    else:
        average = total_score / valid_file_count
        # 打印结果
        print(f"=== 计算结果 ===")
        print(f"有效JSON文件数量：{valid_file_count}")
        print(f"final_score总分：{total_score:.2f}")
        print(f"final_score平均值：{average:.2f}")

    # 打印错误文件（若有）
    if error_files:
        print(f"\n=== 读取失败的文件（共{len(error_files)}个）===")
        for err in error_files:
            print(f"- {err}")

    return average

# --------------------------
# 请修改这里的文件夹路径！！！
# --------------------------
target_folder = r"IF/seedream4-0"  # 示例：r"D:\data\json_files"
calculate_final_score_average(target_folder)