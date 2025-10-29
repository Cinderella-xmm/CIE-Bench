# 有些原始图被删了，把被删了的json和txt也删掉
# 要删question的， answer的

import os

def find_unmatched_files(image_folder, question_folder):
    """
    找出question文件夹中，不存在对应原始图的json和txt文件
    
    参数:
        image_folder: 原始图片所在文件夹路径
        question_folder: 存放json和txt文件的question文件夹路径
    """
    # 步骤1：收集所有原始图片的"主文件名"（不含扩展名，统一小写，避免大小写差异）
    image_basenames = set()
    # 常见图片扩展名（可根据实际情况补充）
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff')
    
    for filename in os.listdir(image_folder):
        # 过滤非图片文件
        if filename.lower().endswith(image_extensions):
            # 提取主文件名（不含扩展名），转为小写
            basename = os.path.splitext(filename)[0].lower()
            image_basenames.add(basename)
    
    # 步骤2：收集question文件夹中所有json和txt文件的"主文件名"及完整路径
    question_files = {}  # 格式：{主文件名: {'.json': 路径, '.txt': 路径}}
    target_extensions = ('.json', '.txt')
    
    for filename in os.listdir(question_folder):
        # 过滤非json/txt文件
        if filename.lower().endswith(target_extensions):
            # 提取主文件名和扩展名
            basename = os.path.splitext(filename)[0].lower()
            ext = os.path.splitext(filename)[1].lower()
            full_path = os.path.join(question_folder, filename)
            
            # 记录到字典中
            if basename not in question_files:
                question_files[basename] = {}
            question_files[basename][ext] = full_path
    
    # 步骤3：找出question中存在但原始图中不存在的文件
    unmatched_files = []
    for basename, ext_paths in question_files.items():
        if basename not in image_basenames:
            # 该主文件名对应的原始图不存在，收集其下的json和txt
            for ext, path in ext_paths.items():
                unmatched_files.append(path)
    
    # 输出结果
    print(f"\n==== 不匹配文件检查结果 ====")
    print(f"原始图文件夹中有效图片数量: {len(image_basenames)} 张")
    print(f"question文件夹中json/txt文件涉及的主文件名数量: {len(question_files)} 个")
    print(f"不存在对应原始图的json/txt文件数量: {len(unmatched_files)} 个")
    
    if unmatched_files:
        print("\n不存在对应原始图的文件路径：")
        for path in sorted(unmatched_files):
            print(f"- {path}")
            # os.remove(path)
    else:
        print("\n所有json和txt文件都有对应的原始图！")

# 配置参数（请根据实际情况修改）
IMAGE_FOLDER = "/home/ma-user/work/CIE/bench/image"  # 原始图片所在文件夹路径
QUESTION_FOLDER = "/home/ma-user/work/CIE/bench/questions_all/VQ"  # question文件夹路径（存放json和txt）

if __name__ == "__main__":
    find_unmatched_files(IMAGE_FOLDER, QUESTION_FOLDER)