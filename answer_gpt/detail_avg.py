import os
import json

def calculate_final_score_average(folder_path, info_file_path):
    # 初始化class分组数据（1-9），新增class_avg存储每个类别的单独平均分
    class_ids = range(1, 10)
    class_data = {cid: {'total': 0.0, 'count': 0, 'class_avg': 0.0} for cid in class_ids}
    
    # 定义每3个类别为一组（共3组）
    group_definition = {
        1: [1, 2, 3],   # 第1组包含class 1、2、3
        2: [4, 5, 6],   # 第2组包含class 4、5、6
        3: [7, 8, 9]    # 第3组包含class 7、8、9
    }
    
    # 前缀映射：图像前缀 -> class_id
    prefix_to_class = {}
    # 错误记录
    info_errors = []
    score_errors = []

    # --------------------------
    # 处理信息JSON文件，建立前缀与class_id的映射
    # --------------------------
    try:
        with open(info_file_path, "r", encoding="utf-8") as f:
            info_data = json.load(f)
            info_items = [info_data] if isinstance(info_data, dict) else info_data

            for idx, item in enumerate(info_items):
                if "class_id" not in item:
                    info_errors.append(f"信息条目[{idx}] - 缺少'class_id'字段")
                    continue
                if "input_image" not in item:
                    info_errors.append(f"信息条目[{idx}] - 缺少'input_image'字段")
                    continue

                class_id = item["class_id"]
                if not isinstance(class_id, int) or class_id not in class_ids:
                    info_errors.append(f"信息条目[{idx}] - class_id无效（需为1-9的整数，当前值：{class_id}）")
                    continue

                input_image = item["input_image"]
                if not isinstance(input_image, list) or len(input_image) == 0:
                    info_errors.append(f"信息条目[{idx}] - 'input_image'不是非空列表")
                    continue
                img_path = input_image[0]
                img_filename = os.path.basename(img_path)
                img_prefix = os.path.splitext(img_filename)[0]

                if img_prefix in prefix_to_class:
                    info_errors.append(f"信息条目[{idx}] - 前缀'{img_prefix}'重复（已存在于其他条目）")
                else:
                    prefix_to_class[img_prefix] = class_id

    except json.JSONDecodeError:
        info_errors.append("信息文件 - JSON格式错误（文件损坏或内容非法）")
    except Exception as e:
        info_errors.append(f"信息文件 - 处理错误：{str(e)}")

    # --------------------------
    # 处理分数JSON文件，按class_id分组累加并计算单独平均分
    # --------------------------
    total_overall = 0.0  # 整体总分
    count_overall = 0    # 整体有效文件数

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            score_prefix = os.path.splitext(filename)[0]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                score = data.get("final_score")
                if score is None:
                    score_errors.append(f"{filename} - 缺少'final_score'字段")
                    continue
                if not isinstance(score, (int, float)):
                    score_errors.append(f"{filename} - 'final_score'不是数值（当前类型：{type(score).__name__}）")
                    continue

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

    # 计算每个类别的单独平均分（在所有分数处理完成后）
    for cid in class_ids:
        count = class_data[cid]['count']
        total = class_data[cid]['total']
        class_data[cid]['class_avg'] = total / count if count > 0 else 0.0

    # --------------------------
    # 计算每3个类别一组的结果（基于类别平均分的平均）
    # --------------------------
    group_data = {}
    for group_id, classes in group_definition.items():
        # 收集组内有有效数据的类别的平均分（排除count=0的类别）
        valid_class_avgs = []
        for cid in classes:
            if class_data[cid]['count'] > 0:  # 仅包含有有效数据的类别
                valid_class_avgs.append(class_data[cid]['class_avg'])
        
        # 计算组平均分：有效类别平均分的平均值
        if len(valid_class_avgs) > 0:
            group_avg = sum(valid_class_avgs) / len(valid_class_avgs)
        else:
            group_avg = 0.0  # 组内所有类别均无有效数据
        
        group_data[group_id] = {
            'classes': classes,
            'valid_classes': [cid for cid in classes if class_data[cid]['count'] > 0],  # 有效类别
            'class_avgs': {cid: class_data[cid]['class_avg'] for cid in classes},  # 所有类别的平均分（含无效）
            'group_avg': group_avg
        }

    # --------------------------
    # 输出结果
    # --------------------------
    # 1. 各class_id单独结果
    print("=== 各class_id单独平均值结果 ===")
    for cid in class_ids:
        total = class_data[cid]['total']
        count = class_data[cid]['count']
        avg = class_data[cid]['class_avg']
        print(f"class {cid}：有效文件数={count}，总分={total:.2f}，平均值={avg:.2f}")

    # 2. 每3个类别一组的结果（基于类别平均分的平均）
    print("\n=== 每3个类别一组的平均值结果（组内类别平均分的平均） ===")
    for group_id, data in group_data.items():
        classes = data['classes']
        valid_classes = data['valid_classes']
        class_avgs = data['class_avgs']
        group_avg = data['group_avg']
        
        # print(f"第{group_id}组（包含class {classes}）：")
        # # 打印组内每个类别的平均分
        # for cid in classes:
        #     status = "（有效数据）" if cid in valid_classes else "（无有效数据）"
        #     print(f"  class {cid}的平均分：{class_avgs[cid]:.2f} {status}")
        # # 打印组平均分（仅基于有效类别的平均分）
        # print(f"  组内有效类别数：{len(valid_classes)}/{len(classes)}")
        print(f"  第{group_id}组（包含class {classes}）, 组平均分（有效类别平均分的平均）：{group_avg:.2f}")

    # 3. 整体结果
    print("=== 整体平均值结果 ===")
    if count_overall == 0:
        print("未找到有效数据，无法计算平均值。")
        overall_avg = 0.0
    else:
        overall_avg = total_overall / count_overall
        print(f"有效文件总数：{count_overall}")
        print(f"final_score总分：{total_overall:.2f}")
        print(f"final_score平均值：{overall_avg:.2f}\n")

    # 4. 错误信息
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
TYPE = ["IF", "VC", "VQ"]
for ty in TYPE:
    target_folder = rf"{ty}/seedream4-0"  # 分数JSON文件所在文件夹
    info_file_path = r"/home/ma-user/work/CIE/bench/instruction.json"  # 含class_id的信息JSON文件路径
    print("当前计算分数的目标文件夹为：", target_folder)
    calculate_final_score_average(target_folder, info_file_path)