import os
import base64
import json
import re
import cv2
import numpy as np
from openai import OpenAI
from PIL import Image
from io import BytesIO

class ImageEvaluator:
    def __init__(self, api_key, base_url, prompt_path):
        """初始化评估器"""
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.single_prompt = self._load_single_prompt(prompt_path)
        self.supported_image_formats = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'BMP': 'image/bmp',
            'JPG': 'image/jpg',
            'WEBP': 'image/webp'
        }

    def _load_single_prompt(self, prompt_path):
        """加载统一的prompt模板"""
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"统一prompt文件不存在: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _encode_image(self, image, image_format):
        """将OpenCV图像转换为Base64编码"""
        try:
            # 转换颜色通道并创建PIL图像
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            buffered = BytesIO()
            pil_image.save(buffered, format=image_format)
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"图片编码失败: {str(e)}")
            return None

    def _load_image(self, image_path):
        """加载图片并返回OpenCV图像对象和格式"""
        try:
            # 使用PIL获取图片格式
            pil_image = Image.open(image_path)
            image_format = pil_image.format
            
            # 转换为OpenCV格式
            image = cv2.cvtColor(np.asarray(pil_image), cv2.COLOR_RGB2BGR)
            return image, image_format
        except Exception as e:
            print(f"图片加载失败 {image_path}: {str(e)}")
            return None, None

    def _find_image_path(self, root_path, base_name):
        """根据基础名称查找图片路径"""
        for ext in [f'.{fmt.lower()}' for fmt in self.supported_image_formats.keys()]:
            image_path = os.path.join(root_path, f"{base_name}{ext}")
            if os.path.exists(image_path):
                return image_path
        return None

    def _parse_model_response(self, response_text):
        """解析模型返回的JSON格式回答"""
        try:
            # 提取JSON部分
            json_strings = re.findall(r'\{.*?\}', response_text, re.DOTALL)
            parsed_responses = []
            
            for json_str in json_strings:
                # 清理JSON字符串
                json_str = json_str.replace('\n', '').replace('\r', '')
                try:
                    parsed = json.loads(json_str)
                    parsed_responses.append(parsed)
                except json.JSONDecodeError:
                    continue
                    
            return parsed_responses
        except Exception as e:
            print(f"解析模型回答失败: {str(e)}")
            return []
        
    def evaluate_pair(self, root_path_a, root_path_b, json_file, output_file):
        """评估一组图片(A原始, B编辑后)，返回详细结果"""
        # 获取JSON基础名称
        json_basename = os.path.splitext(os.path.basename(json_file))[0]
        detailed_result = {
            "filename": json_basename,
            "questions": [],  
            "final_score": 0.0,  # 最终加权得分
        }
        
        # 查找对应的图片
        image_a_path = self._find_image_path(root_path_a, json_basename)
        image_b_path = self._find_image_path(root_path_b, json_basename)
        
        print("原图：", image_a_path)
        print("编辑后图像：", image_b_path)

        # 检查图片是否存在
        if not image_a_path:
            print(f"未找到原始图片A: {json_basename} 在 {root_path_a}")
            detailed_result["error"] = "未找到原始图片A"
            return detailed_result
        if not image_b_path:
            print(f"未找到编辑后图片B: {json_basename} 在 {root_path_b}")
            detailed_result["error"] = "未找到编辑后图片B"
            return detailed_result

        # 加载并编码图片
        image_a, format_a = self._load_image(image_a_path)
        image_b, format_b = self._load_image(image_b_path)
        
        if image_a is None or image_b is None or format_a is None or format_b is None:
            detailed_result["error"] = "图片加载失败"
            return detailed_result
            
        # 转换为Base64
        base64_a = self._encode_image(image_a, format_a)
        base64_b = self._encode_image(image_b, format_b)
        
        if not base64_a or not base64_b:
            detailed_result["error"] = "图片编码失败"
            return detailed_result

        # 构建图片URL
        image_url_a = f"data:{self.supported_image_formats[format_a]};base64,{base64_a}"
        image_url_b = f"data:{self.supported_image_formats[format_b]};base64,{base64_b}"

        # 读取JSON中的问题数据
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误 {json_file}: {str(e)}")
            detailed_result["error"] = f"JSON解析错误: {str(e)}"
            return detailed_result
            
        questions = data.get("quality_check_questions", [])
        if not questions:
            print(f"JSON中无问题数据: {json_file}")
            detailed_result["error"] = "JSON中无问题数据"
            return detailed_result

        # 构建问题文本并替换prompt中的占位符
        questions_text = "Please answer all questions regarding the edited image (second image) as follows:\n\n"
        for q in questions:
            questions_text += f"{q['question_id']}: {q['question']}\n"
            questions_text += "Choices: " + ", ".join(q['choices']) + "\n\n"
        
        final_prompt = self.single_prompt.replace("{Questions}", questions_text)

        # 调用模型接口
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": "You are an image quality evaluator. Please assess the edited image based on the given questions."}]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_url_a, "detail": "high"}},
                            {"type": "image_url", "image_url": {"url": image_url_b, "detail": "high"}},
                            {"type": "text", "text": final_prompt}
                        ]
                    }
                ],
                max_tokens=2000,
            )
            model_answer = response.choices[0].message.content.strip()

            txt_save_path = output_file[:-5] + ".txt"
            with open(txt_save_path,'w',encoding='utf-8') as ft:
                ft.write(model_answer)
            # print(f"模型回答 {json_basename}: {model_answer}")

        except Exception as e:
            print(f"接口调用失败 {json_basename}: {str(e)}")
            detailed_result["error"] = f"接口调用失败: {str(e)}"
            return detailed_result
        
        # 解析模型回答
        parsed_answers = self._parse_model_response(model_answer)
        if not parsed_answers:
            detailed_result["error"] = "无法解析模型回答"
            return detailed_result
        
        # 计算加权得分并记录每个问题的详情
        weighted_score = 0.0
        total_weight = 0.0

        for q in questions:
            question_id = q['question_id']
            weight = q.get('weight', 1.0)
            total_weight += weight
            
            # 查找对应的模型回答
            model_response = next(
                (ans for ans in parsed_answers if ans.get('Question', '').startswith(question_id)),
                None
            )
            
            if model_response:
                model_answer_text = model_response.get('answer', '').strip()
                correct_answer = q['answer'].strip()
                is_correct = str(model_answer_text.lower()) == str(correct_answer.lower())
                explanation = model_response.get('explanation', '')
                
                if is_correct:
                    weighted_score += weight
            else:
                model_answer_text = "未找到对应回答"
                explanation = "未找到模型对该问题的解释"
                is_correct = False
            
            # 记录每个问题的详细信息
            detailed_result["questions"].append({
                "question_id": q['question_id'],
                "question": q['question'],
                "choices": q['choices'],
                "correct_answer": q['answer'],
                "explanation": explanation,
                "weight": weight,
                "model_answer": model_answer_text,
                "is_correct": is_correct
            })

        # 计算最终得分
        if total_weight > 0:
            detailed_result["final_score"] = weighted_score / total_weight
        else:
            detailed_result["final_score"] = 0.0

        return detailed_result

    # read json, then find rootA and rootB
    def batch_evaluate(self, json_folder, root_path_a, root_path_b, output_folder):
        os.makedirs(output_folder, exist_ok=True)
        json_files = [
            os.path.join(json_folder, f) 
            for f in os.listdir(json_folder) 
            if os.path.isfile(os.path.join(json_folder, f)) and f.lower().endswith('.json')
        ]

        for i, json_file in enumerate(json_files, 1):
            json_filename = os.path.basename(json_file)
            output_file = os.path.join(output_folder, json_filename)
            if os.path.exists(output_file):
                continue

            print(f"\n处理 {i}/{len(json_files)}: {json_filename}")
            result = self.evaluate_pair(root_path_a, root_path_b, json_file, output_file)
            print(f"得分: {result['final_score']:.4f}")

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存至: {output_file}")


if __name__ == "__main__":
    API_KEY = "sk-bC44gVfudbKseHjOCcFc01696d8d4312BaE85043F2E3C33f"
    BASE_URL = "https://az.gptplus5.com/v1"
    PROMPT_PATH = "prompt_templete/answer.txt"  # 统一的prompt文件路径
    TYPE = ["IF", "VC", "VQ"]

    output_root = "/home/ma-user/work/CIE/answer_gpt"
    os.makedirs(output_root, exist_ok=True)
    ROOT_PATH_A = "/home/ma-user/work/CIE/bench/image"  # 原始图片A根目录
    model_names = ["OmniGen2"]

    for modelname in model_names:
        for tp in TYPE:
            JSON_FOLDER = f"/home/ma-user/work/CIE/bench/questions_all/{tp}"  # 存放问题JSON文件的文件夹
            ROOT_PATH_B = f"/home/ma-user/work/CIE/outputs_images/{modelname}"  # 编辑后图片B根目录
            OUTPUT_FOLDER = f"{output_root}/{tp}/{modelname}"  # 详细结果输出文件
            evaluator = ImageEvaluator(API_KEY, BASE_URL, PROMPT_PATH)
            evaluator.batch_evaluate(JSON_FOLDER, ROOT_PATH_A, ROOT_PATH_B, OUTPUT_FOLDER)

