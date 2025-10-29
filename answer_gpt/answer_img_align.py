# 有些原始图像删去了，把对应的问题的回答也删掉 - 之后应该用不到了
import os

img_path = '/home/ma-user/work/CIE/bench/image'
imagenames = os.listdir(img_path)
imge_list = []
for imgname in imagenames:
    prefix = os.path.splitext(imgname)[0]
    imge_list.append(prefix)

root_dir = '/home/ma-user/work/CIE/answer_gpt'
TYPE = ['IF', 'VC', 'VQ']
for tp in TYPE:
    tp_folder = os.path.join(root_dir, tp)
    modelnames = os.listdir(tp_folder)
    print(tp)
    for modelname in modelnames:
        model_dir = os.path.join(tp_folder, modelname)
        filenames = os.listdir(model_dir)
        print('\n' + modelname)
        delete_list = []
        for filename in filenames:
            entry = os.path.splitext(filename)[0]
            if entry not in imge_list:
                delete_path = os.path.join(model_dir, filename)
                delete_list.append(delete_path)
                # os.remove(delete_path)
        print(len(delete_list), ': ', delete_list)