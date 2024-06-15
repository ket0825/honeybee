from image_function_main import char_pix_extract, last_OCR_image, make_ocr_sequence, make_ocr_sequence_json
from extra_image_function import OCR_image
import os
import json

from image_processing.ocr_engine import OCREngine

# ocr_engine = OCREngine.get_instance()

# 폴더 경로 설정.
dir_path = r".\image_processing\train_image"

for img_filename in os.listdir(dir_path):
    # image_path = "https://shopping-phinf.pstatic.net/20231109_13_7/578b9973-8ea2-43e0-bebe-51a0ab52c61a/-859484887.jpg"
    img_path = os.path.join(dir_path,img_filename)

    cut_pix_list = char_pix_extract(img_path)
    
    # 위에서 찾은 경계로 이미지 다시 잘라서 last_image폴더에 저장하는 함수
    # ocr_sequence = make_ocr_sequence(img_path, cut_pix_list)
    make_ocr_sequence_json(img_path, cut_pix_list)
    # last_image_cut(img_path,"last_image",cut_pix_list)
    # last_image 폴더에 저장된 이미지 ocr한 후에, 문자+바운딩박스 튜플로 묶어서 하나의 리스트로 반환하는 함수
    # ocr_sequence = last_OCR_image("last_image", cut_pix_list)


    # with open('./ocr_result.json', 'a', encoding='utf-8-sig') as json_file:
    #     json.dump(ocr_sequence, json_file, ensure_ascii=False)
