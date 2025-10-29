import os
import json
from collections import Counter, defaultdict

def find_zero_scores_in_folders():
    # 定义要检查的文件夹
    folders = ["IF/step1x-edit", "VC/step1x-edit", "VQ/step1x-edit"]

    # 存储所有final_score为0的文件信息
    all_zero_files = {}
    error_messages = []
    # 按错误类型分组存储文件路径
    error_to_files = defaultdict(list)

    for folder in folders:
        print(f"\n{'='*60}")
        print(f"检查文件夹: {folder}")
        print('='*60)

        zero_count = 0
        total_count = 0

        if not os.path.exists(folder):
            print(f"警告: 文件夹 {folder} 不存在")
            continue

        # 遍历文件夹中的所有JSON文件
        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                total_count += 1
                file_path = os.path.join(folder, filename)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # 检查final_score是否为0
                    score = data.get("final_score")
                    if score == 0 or score == 0.0:
                        zero_count += 1
                        error_msg = data.get("error", "无error字段")
                        all_zero_files[file_path] = error_msg
                        error_messages.append(error_msg)
                        # 记录每种错误对应的文件
                        error_to_files[error_msg].append(file_path)

                except Exception as e:
                    print(f"读取文件出错 {file_path}: {str(e)}")

        print(f"总文件数: {total_count}")
        print(f"final_score为0的文件数: {zero_count}")
        print(f"比例: {zero_count/total_count*100:.2f}%" if total_count > 0 else "N/A")

    # 统计结果
    print(f"\n{'='*60}")
    print("总体统计")
    print('='*60)
    print(f"总共找到 {len(all_zero_files)} 个final_score为0的文件\n")

    # 分析error信息
    print(f"{'='*60}")
    print("Error信息分析 - 按类型显示所有文件")
    print('='*60)

    # 统计不同error的出现次数
    error_counter = Counter(error_messages)

    print(f"\n发现 {len(error_counter)} 种不同的error类型:\n")

    for idx, (error, count) in enumerate(error_counter.most_common(), 1):
        print(f"\n{'='*80}")
        print(f"错误类型 {idx}: 出现次数 {count}")
        print(f"Error内容: {error}")
        print('='*80)

        # 获取该错误类型对应的所有文件
        files_with_this_error = error_to_files[error]

        # 对于第一种"无error字段"的情况,只显示统计信息
        if error == "无error字段":
            print(f"(这是正常情况,说明final_score为0但没有发生错误)")
            print(f"共 {len(files_with_this_error)} 个文件,不详细列出\n")
        else:
            # 对于其他错误类型,显示所有文件名
            print(f"受影响的文件列表:")
            for file_idx, file_path in enumerate(files_with_this_error, 1):
                # 只显示文件名,不显示完整路径
                filename = os.path.basename(file_path)
                folder = os.path.dirname(file_path)
                print(f"  {file_idx}. [{folder}] {filename}")
            print()

    return all_zero_files

if __name__ == "__main__":
    find_zero_scores_in_folders()
