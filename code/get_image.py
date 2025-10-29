import requests
import os
from datetime import datetime
from typing import List

def generate_edited_images_multi(image_paths: List[str], prompt: str, api_key: str, save_dir):
    """
    在单次请求中上传多张图像，生成编辑后的图像并保存
    
    参数:
        image_paths: 原始图像的本地路径列表（单次请求中的多张图像）
        prompt: 文本描述要求（适用于所有图像）
        api_key: 你的API密钥
        save_dir: 生成图像的保存目录
    """
    
    # API端点URL
    url = "https://api.302ai.cn/v1/images/edits?response_format=url"
    
    # 请求头（注意：multipart/form-data的边界由requests自动处理，无需手动指定）
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    
    # 准备文件列表（关键：多张图像都放在files列表中，且字段名都是'image'）
    files = []
    for img_path in image_paths:
        # 每张图像都以'image'为字段名，按顺序添加到files列表
        files.append(
            ('image', (os.path.basename(img_path), open(img_path, 'rb'), 'image/*'))
        )
    
    # 表单数据（所有图像共用同一个prompt和参数）
    data = {
        'prompt': prompt,
        'model': 'gpt-image-1',
        'size': '1024x1024',  # 可选：auto/1024x1024/1536x1024/1024x1536
        'quality': 'medium',    # 可选：high/medium/low/auto
        'n': 3,  # 生成的图像数量，建议与输入图像数量一致
        'output_format': 'png'
    }
    get_urls = []
    try:
        # 发送单次POST请求（包含所有图像）
        print(f"Sending request with {len(image_paths)} images...")
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # 检查请求是否成功
        print("Request successful!")
        # 解析响应
        result = response.json()
        if 'data' in result and len(result['data']) > 0:
            saved_paths = []
            # 遍历返回的每张生成图像
            for i, img_data in enumerate(result['data']):
                if 'url' in img_data:
                    get_urls.append(img_data['url'])  # 保存url

                    # 下载生成的图像, 保存url，下载失败跳过
                    try:  # 尝试下载图像
                        print(f"Downloading image {i+1}/{len(result['data'])}...")
                        img_response = requests.get(img_data['url'])
                        img_response.raise_for_status()
                    except:
                        print(f"Failed to download image {i+1}/{len(result['data'])}. Skipping...")
                        continue
                    
                    # 生成文件名（包含原始图像名和索引，便于对应）
                    original_name = os.path.basename(image_paths[i])
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(save_dir, original_name)
                    
                    # 保存图像
                    with open(save_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    print(f"image {i+1}/{len(image_paths)} save: {save_path}")
                    saved_paths.append(save_path)
                else:
                    print(f"image {i+1} no URL return")
            
            return saved_paths, get_urls
        else:
            print("no img return")
            print("re:", result)
            return [], []
            
    except Exception as e:
        print(f"faile: {str(e)}")
        if 'response' in locals():
            print("respons:", response.text)
        return [], []
    finally:
        # 关闭所有打开的文件
        for file_tuple in files:
            if hasattr(file_tuple[1][1], 'close'):
                file_tuple[1][1].close()

# 使用示例
if __name__ == "__main__":
    # 配置参数
    YOUR_API_KEY = "sk-bJqiUpwkiNoOwV0S4hUZUf8iwcijQh5XKGB3VjBEtlOshSzD"  # 替换为你的API密钥
    import json
    with open("/home/ma-user/work/CIE/bench/instruction.json", 'r', encoding='utf-8') as f:
        infos = json.load(f)
    # index = 0
    for entry in infos:
        # index+=1
        # if index>1:
        #     break
        filename = os.path.basename(entry["input_image"][0])
        image_path =  os.path.join("/home/ma-user/work/CIE/bench/image", filename)
        IMAGE_PATHS = [
           image_path
        ]
        PROMPT = entry["input_prompt"]  # 适用于所有输入图像的提示
        
        output_path = os.path.join("/home/ma-user/work/CIE/outputs_images/gpt-image-1", filename)
        if os.path.exists(output_path):
            print(f"{output_path} has exist, skipping")
            continue
        print(f"process {entry['id']}/{len(infos)}: {image_path}")
        saved_paths, urls = generate_edited_images_multi(IMAGE_PATHS, PROMPT, YOUR_API_KEY, output_path)
        print("path:", saved_paths)
        print("url:", urls)