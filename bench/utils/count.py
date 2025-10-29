# 统计类别数量
import json

def count_class_ids(json_path):
    # 初始化计数器（class_id为1-9，字符串类型，对应JSON中的格式）
    class_counts = {i: 0 for i in range(1, 10)}
    
    # 读取JSON文件
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)  # 假设JSON根结构是列表
    
    # 遍历每个条目统计
    for item in data:
        class_id = item.get('class_id')  # 获取class_id
        if class_id in class_counts:  # 只统计1-9范围内的class_id
            class_counts[class_id] += 1
    
    return class_counts

if __name__ == "__main__":
    json_path = "../instruction.json"  # 替换为你的JSON文件路径
    counts = count_class_ids(json_path)
    
    # 打印统计结果
    print("class_id统计结果：")
    for class_id, count in counts.items():
        print(f"class_id {class_id}: {count} 个")

    # # 保存结果到JSON文件（可选）
    # with open("class_counts.json", 'w', encoding='utf-8') as f:
    #     json.dump(counts, f, ensure_ascii=False, indent=2)