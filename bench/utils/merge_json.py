# 把几个编辑指令的json合并到一起 - 后面应该没用了，后面再有就是删图之后了
import os
import json

def merge_json_files(input_dir, output_file, image_root="."):
    """
    合并文件夹中的所有JSON文件，检查图像路径是否存在，并将id重新从1开始编号
    
    参数:
        input_dir: 存放JSON文件的文件夹路径
        output_file: 合并后的JSON文件输出路径
        image_root: 图像路径的根目录（用于拼接相对路径）
    """
    merged_data = []  # 存储所有合并后的JSON数据
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(input_dir):
        # 只处理JSON文件
        if filename.lower().endswith(".json"):
            file_path = os.path.join(input_dir, filename)
            
            # 读取JSON文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 检查读取的数据是否为列表格式
            if not isinstance(json_data, list):
                print(f"警告: {filename} 内容不是列表格式，已跳过")
                continue
            
            # 处理每个条目并检查图像
            for item in json_data:
                img_rel_path = item["input_image"][0]
                full_img_path = os.path.join(image_root, img_rel_path)

                if not os.path.exists(full_img_path):
                    old_id = item.get("id", "未知ID")
                    print(f"警告: 图像不存在 - {filename}, 原始: {old_id}, 路径:", full_img_path)
                    continue

                merged_data.append(item)
                
    # 重新编号id（从1开始）
    for new_id, item in enumerate(merged_data, start=1):
        item["id"] = new_id
    
    # 将合并后的数据写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n合并完成！共 {len(merged_data)} 条数据，已重新编号id（1-{len(merged_data)}），已保存至 {output_file}")

# 配置参数（请根据实际情况修改）
INPUT_DIRECTORY = "/home/ma-user/work/CIE/bench/json"  # 存放JSON文件的文件夹路径
OUTPUT_FILE = "instruction.json"  # 合并后的输出文件路径
IMAGE_ROOT_DIR = "."  # 图像路径的根目录（如果图像路径是相对路径，需要指定此参数）

if __name__ == "__main__":
    # 确保输入文件夹存在
    if not os.path.exists(INPUT_DIRECTORY):
        print(f"错误: 输入文件夹 {INPUT_DIRECTORY} 不存在")
    else:
        merge_json_files(INPUT_DIRECTORY, OUTPUT_FILE, IMAGE_ROOT_DIR)