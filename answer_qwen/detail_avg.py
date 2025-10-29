import os
import json

def calculate_final_score_average(folder_path, info_file_path):
    # 初始化class分组数据（1-9）
    class_ids = range(1, 10)
    class_data = {cid: {'total': 0.0, 'count': 0} for cid in class_ids}
    # 前缀映射：图像前缀 -> class_id（从单独信息文件提取）
    prefix_to_class = {}
    # 错误记录：信息文件错误、分数文件错误
    info_errors = []
    score_errors = []  # 复用原逻辑的错误记录思路

    # --------------------------
    # 新增：处理单独的信息JSON文件，建立前缀与class_id的映射
    # --------------------------
    try:
        with open(info_file_path, "r", encoding="utf-8") as f:
            # 假设信息文件可能是单个对象或对象列表（兼容两种格式）
            info_data = json.load(f)
            # 统一转为列表处理（如果是单个对象）
            info_items = [info_data] if isinstance(info_data, dict) else info_data

            for idx, item in enumerate(info_items):
                # 检查必要字段
                if "class_id" not in item:
                    info_errors.append(f"信息条目[{idx}] - 缺少'class_id'字段")
                    continue
                if "input_image" not in item:
                    info_errors.append(f"信息条目[{idx}] - 缺少'input_image'字段")
                    continue

                # 验证class_id有效性
                class_id = item["class_id"]
                if not isinstance(class_id, int) or class_id not in class_ids:
                    info_errors.append(f"信息条目[{idx}] - class_id无效（需为1-9的整数，当前值：{class_id}）")
                    continue

                # 提取input_image[0]的前缀
                input_image = item["input_image"]
                if not isinstance(input_image, list) or len(input_image) == 0:
                    info_errors.append(f"信息条目[{idx}] - 'input_image'不是非空列表")
                    continue
                img_path = input_image[0]
                img_filename = os.path.basename(img_path)  # 取图像文件名（如"1718655347.8155239.jpg"）
                img_prefix = os.path.splitext(img_filename)[0]  # 提取前缀

                # 检查前缀重复
                if img_prefix in prefix_to_class:
                    info_errors.append(f"信息条目[{idx}] - 前缀'{img_prefix}'重复（已存在于其他条目）")
                else:
                    prefix_to_class[img_prefix] = class_id

    except json.JSONDecodeError:
        info_errors.append("信息文件 - JSON格式错误（文件损坏或内容非法）")
    except Exception as e:
        info_errors.append(f"信息文件 - 处理错误：{str(e)}")

    # --------------------------
    # 原逻辑：处理分数JSON文件（target_folder中的文件）
    # 新增：按class_id分组累加
    # --------------------------
    total_overall = 0.0  # 整体总分
    count_overall = 0    # 整体有效文件数

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            # 提取分数文件前缀（去除.json扩展名）
            score_prefix = os.path.splitext(filename)[0]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 提取final_score（保留原校验逻辑）
                score = data.get("final_score")
                if score is None:
                    score_errors.append(f"{filename} - 缺少'final_score'字段")
                    continue
                if not isinstance(score, (int, float)):
                    score_errors.append(f"{filename} - 'final_score'不是数值（当前类型：{type(score).__name__}）")
                    continue

                # 新增：通过前缀匹配class_id
                if score_prefix not in prefix_to_class:
                    score_errors.append(f"{filename} - 前缀'{score_prefix}'无匹配的class_id（信息文件中未找到）")
                    continue
                class_id = prefix_to_class[score_prefix]

                # 累加至对应class和整体
                class_data[class_id]['total'] += score
                class_data[class_id]['count'] += 1
                total_overall += score
                count_overall += 1

            except json.JSONDecodeError:
                score_errors.append(f"{filename} - JSON格式错误（文件损坏或内容非法）")
            except Exception as e:
                score_errors.append(f"{filename} - 其他错误：{str(e)}")

    # --------------------------
    # 输出结果（修改原输出逻辑）
    # --------------------------
    # 1. 各class_id结果
    print("=== 各class_id平均值结果 ===")
    for cid in class_ids:
        total = class_data[cid]['total']
        count = class_data[cid]['count']
        avg = total / count if count > 0 else 0.0
        print(f"class {cid}：有效文件数={count}，总分={total:.2f}，平均值={avg:.2f}")

    # 2. 整体结果
    print("\n=== 整体平均值结果 ===")
    if count_overall == 0:
        print("未找到有效数据，无法计算平均值。")
        overall_avg = 0.0
    else:
        overall_avg = total_overall / count_overall
        print(f"有效文件总数：{count_overall}")
        print(f"final_score总分：{total_overall:.2f}")
        print(f"final_score平均值：{overall_avg:.2f}")

    # 3. 错误信息
    if info_errors:
        print(f"\n=== 信息文件错误（共{len(info_errors)}个）===")
        for err in info_errors:
            print(f"- {err}")
    if score_errors:
        print(f"\n=== 分数文件错误（共{len(score_errors)}个）===")
        for err in score_errors:
            print(f"- {err}")

    return overall_avg

# --------------------------
# 请修改以下两个路径！！！
# --------------------------
target_folder = r"VQ/seedream4-0"  # 分数JSON文件所在文件夹
info_file_path = r"/home/ma-user/work/CIE/bench/instruction.json"  # 单独的信息JSON文件路径（含class_id的文件）
calculate_final_score_average(target_folder, info_file_path)