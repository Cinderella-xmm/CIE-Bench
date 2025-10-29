# 找有原图，但是没生成图的
import os

src_image_dir = '/home/ma-user/work/CIE/bench/image'
target_image_dir = '/home/ma-user/work/CIE/outputs_images/gpt-image-1'
filenams = os.listdir(src_image_dir)
for filename in filenams:
    image_path = os.path.join(target_image_dir, filename)
    if not os.path.exists(image_path):
        src_path = os.path.join(src_image_dir, filename)
        print(src_path)