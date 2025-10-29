import json
import os
import argparse

def find_score(folder_path, filename):
    """获取指定类型（IF/VC/VQ）下各模型的final_score"""
    model_scores = {}  # 键：模型名，值：该类型下的final_score
    model_names = os.listdir(folder_path)
    for modelname in model_names:
        file_path = os.path.join(folder_path, modelname, f"{filename}.json")
        if not os.path.exists(file_path):
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        final_score = info["final_score"]  # 提取该类型下的final_score
        single_info = info["questions"]
        # 打印单题得分和该类型的final_score
        print(f"{modelname}:", end="")
        for item in single_info:
            single_score = 0 if item["is_correct"] is False else 1
            print(f" {single_score}", end="")
        print(f" final_score: {final_score:.2f}")
        model_scores[modelname] = final_score  # 存储当前模型在该类型下的final_score
    return model_scores

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True, help="指定图片的id")
    args = parser.parse_args()

    root_path = "/home/ma-user/work/CIE/answer_gpt"
    
    # 分别获取IF、VC、VQ三类的final_score（键为模型名，值为对应类型的final_score）
    print("IF")
    if_scores = find_score(os.path.join(root_path, "IF"), args.id)
    
    print("\nVC")
    vc_scores = find_score(os.path.join(root_path, "VC"), args.id)
    
    print("\nVQ")
    vq_scores = find_score(os.path.join(root_path, "VQ"), args.id)
    
    # 计算加权得分：0.4*IF_final_score + 0.4*VC_final_score + 0.2*VQ_final_score
    all_models = set(if_scores.keys()).union(vc_scores.keys()).union(vq_scores.keys())
    print("\nAvg:")
    for model in all_models:
        # 若模型在某类型下无数据，默认该类型得分为0
        if_score = if_scores.get(model, 0.0)
        vc_score = vc_scores.get(model, 0.0)
        vq_score = vq_scores.get(model, 0.0)
        weighted_score = 0.4 * if_score + 0.4 * vc_score + 0.2 * vq_score
        print(f"{model}: {weighted_score:.2f}")