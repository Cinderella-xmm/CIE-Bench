import json
import os
import re

def txt_to_quality_json(txt_path, output_json_path):
    # 1. 读取txt文件内容
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 2. 按Q1、Q2等分割问题块（兼容全角冒号“：”和半角冒号“:”）
    question_blocks = re.split(r'(?=Q\d+[:：])', content)
    quality_check_questions = []
    
    for block in question_blocks:
        block = block.strip()
        if not block.startswith('Q'):
            continue  # 跳过空内容或非问题块
        
        # 3. 提取各字段（正则兼容空白和格式差异）
        # 提取question_id（如Q1、Q2）
        qid_match = re.search(r'Q(\d+)[:：]', block)
        question_id = f"Q{qid_match.group(1)}" if qid_match else ""
        
        # 提取thinking_process（Thinking process: 后面的内容）
        thinking_match = re.search(r'Thinking process:\s*(.*?)\s*Question:', block, re.DOTALL)
        thinking_process = thinking_match.group(1).strip() if thinking_match else ""
        
        # 提取question（Question: 后面的内容）
        question_match = re.search(r'Question:\s*(.*?)\s*Choices:', block, re.DOTALL)
        question = question_match.group(1).strip() if question_match else ""
        
        # 提取choices（Choices: 后面的内容，拆分为列表）
        choice_match = re.search(r'Choices:\s*(.*?)\s*A:', block, re.DOTALL)
        choices_str = choice_match.group(1).strip() if choice_match else ""
        choices = [c.strip() for c in choices_str.split(',')] if choices_str else []
        
        # 提取answer（A: 后面的内容）
        answer_match = re.search(r'A:\s*(.*?)\s*(?=Weight:|$)', block, re.DOTALL | re.IGNORECASE)
        answer = answer_match.group(1).strip() if answer_match else ""
        
        # 提取weight（默认1，如果有Weight字段则取其值）
        weight_match = re.search(r'Weight:\s*(\d+)', block)
        weight = int(weight_match.group(1)) if weight_match else 1
        
        # 4. 组装单个问题字典
        quality_check_questions.append({
            "question_id": question_id,
            "thinking_process": thinking_process,
            "question": question,
            "choices": choices,
            "answer": answer,
            "weight": weight
        })
    
    # 5. 生成最终JSON结构并保存
    result = {
        "quality_check_questions": quality_check_questions
    }
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)  # indent=2美化格式


chinese_pattern = re.compile(r'[\u4e00-\u9fa5]')
TYPE=["IF","VC","VQ"]
# for tp in TYPE:
    # for i in range(1,10):

json_folder = f"/home/ma-user/work/CIE/answer_gpt/IF/Flux1-Kontext-Pro"
filenames = os.listdir(json_folder)
for filename in filenames:
    if not filename.endswith('.json'):
        continue
    filepath = os.path.join(json_folder, filename)

    # 检查json中是否有中文
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # if chinese_pattern.search(content):
    if "用尽" in content:
        print(f"{filepath}")
        os.remove(filepath)

        
