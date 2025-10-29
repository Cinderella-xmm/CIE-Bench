import json
import os
import requests
import base64
import argparse
from pathlib import Path
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


def load_json_data(json_path):
    """加载 JSON 数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def process_image_with_gpt(image_path, instruction, output_path, api_key, model="gpt-image-1", max_retries=3, wait_on_rate_limit=True):
    """
    使用GPT API处理单张图片

    Args:
        image_path: 输入图片路径
        instruction: 编辑指令
        output_path: 输出图片路径
        api_key: API密钥
        model: 模型名称
        max_retries: 最大重试次数
        wait_on_rate_limit: 遇到限流时是否等待重试

    Returns:
        tuple: (bool成功与否, str错误信息)
    """
    url = "https://api.302.ai/v1/images/edits"

    for attempt in range(max_retries):
        try:
            # 打开图片文件
            with open(image_path, "rb") as img_file:
                files = {
                    "image": img_file
                }

                data = {
                    "model": model,
                    "prompt": instruction,
                    "size": "1024x1024"
                }

                headers = {
                    "Authorization": f"Bearer {api_key}"
                }

                # 发送请求
                response = requests.post(url, headers=headers, data=data, files=files, timeout=120)

                # 检测限流 (HTTP 429)
                if response.status_code == 429:
                    if wait_on_rate_limit and attempt < max_retries - 1:
                        wait_time = 30 * (attempt + 1)  # 递增等待：30秒、60秒、90秒
                        tqdm.write(f"⚠️  遇到限流，等待 {wait_time} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    return False, "API限流 (429 Too Many Requests)"

                result = response.json()

            # 检查结果
            if "data" in result:
                img_data = result["data"][0]["b64_json"]
                image_bytes = base64.b64decode(img_data)

                # 保存图片
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                return True, None
            else:
                error_msg = result.get('error', {}).get('message', str(result))

                # 检测错误信息中的限流关键词
                if any(keyword in str(error_msg).lower() for keyword in ['rate limit', 'quota', 'too many']):
                    if wait_on_rate_limit and attempt < max_retries - 1:
                        wait_time = 30 * (attempt + 1)
                        tqdm.write(f"⚠️  遇到限流，等待 {wait_time} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    return False, f"API限流: {error_msg}"

                if attempt < max_retries - 1:
                    time.sleep(1)  # 重试前等待1秒
                    continue
                return False, f"API错误: {error_msg}"

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False, str(e)

    return False, "达到最大重试次数"


def process_single_task(item, image_base_dir, output_dir, args, pbar, stats_lock, stats):
    """
    处理单个任务（线程安全）

    Args:
        item: JSON数据项
        image_base_dir: 图片基础目录
        output_dir: 输出目录
        args: 参数
        pbar: 进度条对象
        stats_lock: 统计锁
        stats: 统计字典
    """
    try:
        # 获取数据
        image_id = item.get('id', 'unknown')
        image_path_raw = item.get('input_image')
        instruction = item.get('input_prompt')
        class_id = item.get('class_id', 0)

        # 处理 image_path
        if isinstance(image_path_raw, list):
            image_path = image_path_raw[0] if image_path_raw else None
        else:
            image_path = image_path_raw

        # 构建完整的图片路径
        if image_path and not os.path.isabs(image_path):
            if image_path.startswith('image/'):
                image_path = image_path[6:]
            full_image_path = os.path.join(image_base_dir, image_path)
        else:
            full_image_path = image_path if image_path else None

        # 检查图片是否存在
        if not full_image_path or not os.path.exists(full_image_path):
            with stats_lock:
                stats['failed'].append({
                    'id': image_id,
                    'reason': 'Image not found',
                    'path': full_image_path
                })
            pbar.update(1)
            return

        # 检查指令是否存在
        if not instruction:
            with stats_lock:
                stats['failed'].append({
                    'id': image_id,
                    'reason': 'Empty instruction'
                })
            pbar.update(1)
            return

        # 获取原始图片文件名
        original_filename = os.path.basename(full_image_path)
        output_filename = original_filename
        output_path = os.path.join(output_dir, output_filename)

        # 如果已经存在且不强制重新处理，则跳过
        if os.path.exists(output_path) and not args.force:
            with stats_lock:
                stats['skipped'] += 1
                stats['success'] += 1
            pbar.update(1)
            return

        # 调用GPT API处理
        success, error = process_image_with_gpt(
            full_image_path,
            instruction,
            output_path,
            args.api_key,
            args.model
        )

        with stats_lock:
            if success:
                stats['success'] += 1
                if args.verbose:
                    tqdm.write(f"✅ ID {image_id}: {output_filename}")
            else:
                stats['failed'].append({
                    'id': image_id,
                    'reason': error,
                    'image': image_path
                })
                if args.verbose:
                    tqdm.write(f"❌ ID {image_id}: {error}")

        pbar.update(1)

    except Exception as e:
        with stats_lock:
            stats['failed'].append({
                'id': image_id,
                'reason': str(e),
                'image': image_path
            })
        pbar.update(1)


def process_dataset(json_file, image_base_dir, output_dir, args):
    """
    使用多线程并发处理CIE Bench数据集

    Args:
        json_file: instruction.json 文件路径
        image_base_dir: 图片基础目录
        output_dir: 输出目录
        args: 其他参数
    """
    print(f"\n{'='*60}")
    print(f"处理 JSON 文件: {json_file}")
    print(f"图片目录: {image_base_dir}")
    print(f"输出目录: {output_dir}")
    print(f"API模型: {args.model}")
    print(f"并发线程数: {args.workers}")
    print(f"{'='*60}")

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 加载 JSON 数据
    data = load_json_data(json_file)
    print(f"共 {len(data)} 条编辑任务\n")

    # 如果指定了ID范围，进行过滤
    if args.start_id is not None or args.end_id is not None:
        start = args.start_id if args.start_id is not None else 1
        end = args.end_id if args.end_id is not None else len(data)
        data = [item for item in data if start <= item['id'] <= end]
        print(f"处理ID范围: {start} - {end}, 共 {len(data)} 条\n")

    # 统计信息（线程安全）
    stats = {
        'total': len(data),
        'success': 0,
        'failed': [],
        'skipped': 0
    }
    stats_lock = threading.Lock()

    # 创建进度条
    pbar = tqdm(total=len(data), desc="处理进度")

    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for item in data:
            future = executor.submit(
                process_single_task,
                item, image_base_dir, output_dir, args, pbar, stats_lock, stats
            )
            futures.append(future)

        # 等待所有任务完成
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                tqdm.write(f"任务执行异常: {str(e)}")

    pbar.close()

    # 打印总体统计信息
    print("\n" + "="*60)
    print("处理完成! 统计信息:")
    print("="*60)
    print(f"总计: {stats['total']} 张图片")
    print(f"成功: {stats['success']} 张")
    print(f"跳过: {stats['skipped']} 张 (已存在)")
    print(f"失败: {len(stats['failed'])} 张")
    if stats['total'] > 0:
        print(f"成功率: {stats['success']/stats['total']*100:.1f}%")

    # 保存失败列表（如果有失败）
    if stats['failed']:
        failed_log = os.path.join(output_dir, 'failed_list.json')
        with open(failed_log, 'w', encoding='utf-8') as f:
            json.dump(stats['failed'], f, indent=2, ensure_ascii=False)
        print(f"\n失败列表: {failed_log}")

    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description='批量处理图像编辑 - CIE Bench数据集 (GPT API 并发版本)')

    # JSON 文件
    parser.add_argument('--json-file', type=str,
                        default="/home/ma-user/work/CIE/bench/instruction.json",
                        help='instruction.json 文件路径')

    # 图片目录
    parser.add_argument('--image-dir', type=str,
                        default="/home/ma-user/work/CIE/bench/image",
                        help='图片目录')

    # 输出目录
    parser.add_argument('--output-dir', type=str,
                        default='/home/ma-user/work/CIE/outputs_images/gpt-image-1',
                        help='输出目录 (默认: /home/ma-user/work/CIE/outputs_images/gpt-image-1)')

    # API配置
    parser.add_argument('--api-key', type=str,
                        default="sk-bJqiUpwkiNoOwV0S4hUZUf8iwcijQh5XKGB3VjBEtlOshSzD",
                        help='API密钥')
    parser.add_argument('--model', type=str,
                        default="gpt-image-1",
                        help='模型名称')

    # 并发控制
    parser.add_argument('--workers', type=int, default=10,
                        help='并发线程数 (默认: 10, 推荐5-20)')

    # 处理范围控制
    parser.add_argument('--start-id', type=int, default=None,
                        help='起始ID (包含)')
    parser.add_argument('--end-id', type=int, default=None,
                        help='结束ID (包含)')

    # 其他选项
    parser.add_argument('--force', action='store_true',
                        help='强制重新处理已存在的文件')
    parser.add_argument('--verbose', action='store_true',
                        help='显示详细输出')

    args = parser.parse_args()

    # 检查文件是否存在
    if not os.path.exists(args.json_file):
        print(f"错误: JSON 文件不存在: {args.json_file}")
        return

    if not os.path.exists(args.image_dir):
        print(f"错误: 图片目录不存在: {args.image_dir}")
        return

    print(f"JSON文件: {args.json_file}")
    print(f"图片目录: {args.image_dir}")
    print(f"输出目录: {args.output_dir}")
    print(f"API模型: {args.model}")
    print(f"并发线程数: {args.workers}")

    # 处理数据集
    process_dataset(args.json_file, args.image_dir, args.output_dir, args)


if __name__ == '__main__':
    main()