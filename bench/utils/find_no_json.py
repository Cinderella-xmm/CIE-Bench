# 找到原图中没有与之对应的编辑指令 - 后面应该没用了
import os
import json

def find_unreferenced_images(image_folder, json_file, image_root="."):
    """
    找出没有被JSON条目引用的图片
    
    参数:
        image_folder: 存放所有图片的文件夹路径（例如 "./image"）
        json_file: 合并后的有效JSON文件路径（例如 "instruction.json"）
        image_root: JSON中图片路径的根目录（需与合并时的IMAGE_ROOT_DIR一致）
    """
    # 步骤1：收集所有图片的路径（相对路径，与JSON中引用格式一致）
    all_image_paths = set()
    # 常见图片格式（可根据实际情况补充）
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    
    # 遍历图片文件夹，获取所有图片的相对路径
    for root, _, files in os.walk(image_folder):
        for file in files:
            if file.lower().endswith(image_extensions):
                # 计算图片相对于image_root的路径（与JSON中引用的格式对齐）
                full_img_path = os.path.join(root, file)
                rel_img_path = os.path.relpath(full_img_path, image_root)
                # 统一路径分隔符（避免Windows和Linux差异）
                rel_img_path = rel_img_path.replace(os.sep, '/')
                all_image_paths.add(rel_img_path)
    
    # 步骤2：收集JSON中所有被引用的图片路径
    referenced_image_paths = set()
    if not os.path.exists(json_file):
        print(f"错误：JSON文件 {json_file} 不存在")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    for item in json_data:
        if "input_image" in item and isinstance(item["input_image"], list) and len(item["input_image"]) > 0:
            img_path = item["input_image"][0].replace(os.sep, '/')  # 统一路径分隔符
            referenced_image_paths.add(img_path)
    
    # 步骤3：找出未被引用的图片（存在于所有图片中，但不在引用列表中）
    unreferenced = all_image_paths - referenced_image_paths
    
    # 输出结果
    print(f"\n==== 图片引用检查结果 ====")
    print(f"总图片数量: {len(all_image_paths)} 张")
    print(f"被JSON引用的图片数量: {len(referenced_image_paths)} 张")
    print(f"未被引用的图片数量: {len(unreferenced)} 张")
    
    if unreferenced:
        print("\n未被任何JSON条目引用的图片路径：")
        for path in sorted(unreferenced):
            print(f"- {path}")
    else:
        print("\n所有图片都有对应的JSON条目！")

# 配置参数（请根据实际情况修改）
IMAGE_FOLDER = "/home/ma-user/work/CIE/bench/image"  # 存放912张图片的文件夹路径（例如 "./image"）
JSON_FILE = "instruction.json"  # 合并后的有效JSON文件路径
IMAGE_ROOT_DIR = "."  # 必须与合并时的IMAGE_ROOT_DIR一致（图片路径的根目录）

if __name__ == "__main__":
    find_unreferenced_images(IMAGE_FOLDER, JSON_FILE, IMAGE_ROOT_DIR)