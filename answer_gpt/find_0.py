import os
import json

def find_zero_final_score(folder_path):
    # 存储符合条件的文件（final_score为0）
    zero_score_files = []
    # 记录处理失败的文件（用于排查问题）
    error_files = []

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 只处理.json后缀的文件
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            try:
                # 读取JSON文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 检查是否存在final_score字段
                score = data.get("final_score")
                if score is None:
                    error_files.append(f"{filename} - 缺少'final_score'字段")
                    continue
                
                # 检查字段是否为数值类型（避免字符串等无效类型）
                if not isinstance(score, (int, float)):
                    error_files.append(f"{file_path} - 'final_score'不是数值（当前类型：{type(score).__name__}）")
                    continue
                
                # 判断是否为0（包括整数0和浮点数0.0）
                if score == 0:
                    zero_score_files.append(file_path)

            except json.JSONDecodeError:
                error_files.append(f"{file_path} - JSON格式错误（文件损坏或内容非法）")
            except Exception as e:
                error_files.append(f"{file_path} - 其他错误：{str(e)}")

    # 输出结果
    print("=== 筛选结果 ===")
    if zero_score_files:
        print(f"共找到 {len(zero_score_files)} 个文件的final_score为0：")
        for file in zero_score_files:
            print(f"- {file}")
    else:
        print("未找到final_score为0的文件")

    # 输出错误信息（若有）
    if error_files:
        print(f"\n=== 处理失败的文件（共{len(error_files)}个）===")
        for err in error_files:
            print(f"- {err}")

    return zero_score_files

# --------------------------
# 请修改为你的文件夹路径！！！
# --------------------------
target_folder = r"VC/Bagel"  # 示例：r"D:\data\json_files"
find_zero_final_score(target_folder)