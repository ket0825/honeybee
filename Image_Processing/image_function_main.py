from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import shutil
import copy
import requests
from io import BytesIO
from log import Logger
import re
import json
from image_processing.ocr_engine import OCREngine



hanja_ptrn = re.compile(r'[一-龥]')
kor_ptrn = re.compile(r'[가-힣]')
kor_vowel_consonant_ptrn = re.compile(r'[ㄱ-ㅎㅏ-ㅣ]]')
eng_ptrn = re.compile(r'[a-zA-Z]')

log = Logger.get_instance()
ocr_engine = OCREngine.get_instance()

def replace_text(text:str):
    return text.replace(':',"").replace("|","").rstrip()

# def slice_image_vertically(image_path, gap):
      
#     # 이미지 로드
#     image = Image.open(image_path)
#     width = image.size[0]   # 이미지 가로
#     height = image.size[1]  # 이미지 세로
    
#     cuted_pix=[]
#     # 이미지 잘라서 저장
#     for i in range(0, height, gap):
#         box = (0, i, width, min(i + gap, height))   # 맨 끝부분
#         cuted_pix.append(min(i + gap, height))
#         image_gap = image.crop(box)
#         image_gap.save(os.path.join(folder_name, f"{i}.jpg"))
    
#     return height # 높이값 반환

def OCR_image(images_array, gap:int): 
    """
    images_array: list[nd.array]
    """
    # 텍스트랑 좌표 1:1로 매칭시켜서 넣을 리스트
    bbox_sequence=[]
    for cnt, image_array in enumerate(images_array):
        # ocr 수행
        try:
            # detection(bounding box)만 진행.
            result=ocr_engine.ocr(image_array, det=True, rec=False, cls=False) 
        except ValueError as val_error:
            log.error("[ERROR] value error in lib. Must modify in paddleocr line 681.")
        
        # 잘린 사진에서 글이 없을 수 있음.
        if not result or not result[0]:
            continue

        # 바운딩박스 좌표들을 갭에 맞춰서 리스트에 추가.    
        for line in result[0]:                    
            bbox_sequence.append([[ax[0], ax[1]+gap*cnt] for ax in line])

    return bbox_sequence     #바운딩 박스 좌표랑 문자가 튜플로 묶인 리스트 반환


# 이분탐색
def find_small_largest(arr, target):
    left = 0
    right = len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return arr[mid-1] # 일부로 하나 전까지만 자름.
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    # 못찾은 경우(while문 끝나고 났을때 right가 더 작은 값이 되어있음)

    if arr[right] < target:
        return arr[right]
    else:
        return arr[right-1]
    

# 이미지 자를 임계값 픽셀 찾기
def char_pix_extract(image_path):
    """
    이미지 자를 임계값 픽셀 찾기

    image_path: img tag src attribute. e.g link of img.

    """

    # 이미지 로드
    if 'http' in image_path:
        res = requests.get(image_path)
        image = Image.open(BytesIO(res.content))
    else:
        image = Image.open(image_path)

    
    width = image.size[0]   # 이미지 가로
    height = image.size[1]  # 이미지 세로

    if height < 2000:
        return [0, height]
    
    cropped_images_2000 = []
    cropped_images_1700 = []
    gaps = (1700, 2000) # 최소공배수 34000.
    for gap in gaps:
        # 이미지 잘라서 저장
        if gap == 2000:
            for i in range(0, height, gap):
                box = (0, i, width, min(i + gap, height))   # 맨 끝부분            
                image_gap = np.asarray(image.crop(box), dtype='uint8')
                cropped_images_2000.append(image_gap)
        elif gap == 1700:
            for i in range(0, height, gap):
                box = (0, i, width, min(i + gap, height))   # 맨 끝부분            
                image_gap = np.asarray(image.crop(box), dtype='uint8')
                cropped_images_1700.append(image_gap)

    boundary=[]
    cut_candidate=set()
    for cut_height in gaps: 
        if cut_height == 1700:       
            result = OCR_image(cropped_images_1700, cut_height)
            cropped_images_1700.clear()
        elif cut_height == 2000:       
            result = OCR_image(cropped_images_2000, cut_height)
            cropped_images_2000.clear()
        for bounding_box in result:
            top= int(min([bounding_box[i][1] for i in range(4)]))
            bottom=int(max([bounding_box[i][1] for i in range(4)]))
            boundary.append((top,bottom))   # 문자 있는 구간 위아래 기준

            # 위에서 10, 아래에서 10 자르기.
            for i in range(0, 11, 5):
                cut_candidate.add(top-i)
                cut_candidate.add(bottom+i)

        # 문자 구간사이에 들어가는 후보 제거
        to_remove = cut_candidate.copy()
        for candidate in to_remove:
            for pair in boundary:
                if candidate > pair[0] and candidate < pair[1]:
                    cut_candidate.remove(candidate)
                    break

    cut_candidate = sorted(cut_candidate)
        
    result_pix_set = set()
    log.info(f"이미지 길이: {height}")
    
    cut_line = 2000
    while cut_line < height:
        new_cut = find_small_largest(cut_candidate, cut_line)
        # 새롭게 찾은게 기준선보다 크거나 같으면, 혹은 이미 있었던 선이면 기준선으로 넣어줘야함.
        if new_cut >= cut_line or new_cut in result_pix_set:
            result_pix_set.add(cut_line)
            cut_line+=2000        
        else:
            # 새롭게 찾은게 기준선보다 작고, 만약 진짜 처음 나온 선이면
            result_pix_set.add(new_cut)
            cut_line = new_cut + 2000
    
    result_pix_set.add(0) # 처음 픽셀 높이 넣어주기.
    result_pix_set.add(height) # 맨 마지막 픽셀 (height) 넣어주기
        
    return sorted(result_pix_set)

# 찾은 임계값 기준으로 이미지 자르고 ocr 돌리기.
def make_ocr_sequence(image_path, cut_pix_list, width_threshold=150, height_threshold=100):
    """
    image_path: img tag src attribute. e.g link of img.

    cut_pix_list: sorted cutline list.
    """
    ocr_sequence = []
    # 이미지 로드
    if 'http' in image_path:
        res = requests.get(image_path)
        image = Image.open(BytesIO(res.content))
    else:
        image = Image.open(image_path)

    width = image.size[0]   # 이미지 가로
    
    prev_bbox = None
    cut_line = 0
    for i in range(len(cut_pix_list)-1):
        # log.info(f"cut_line: {cut_line}")
        box = (0, cut_pix_list[i], width, cut_pix_list[i+1])
        cropped_image_arr = np.asarray(image.crop(box), dtype='uint8')
        result = ocr_engine.ocr(cropped_image_arr, cls=True)

        if not result or not result[0]:
            continue        
        image_data = []
        json_text_list = []
        for line in result[0]:
            # 글자 이상한 것 체크.            
            exist_kor_eng = eng_ptrn.search(line[1][0]) and kor_ptrn.search(line[1][0])
            exist_eng = eng_ptrn.search(line[1][0])
            exist_hanja = hanja_ptrn.search(line[1][0])
            exist_kor_vowel_consonant = kor_vowel_consonant_ptrn.search(line[1][0])
            # bbox = line[0]
            # height = max(bbox[3][1] - bbox[1][1], bbox[2][1] - bbox[0][1]) # 최대 높이 기준. 이게 클수록 OCR이 잘되기에 까다로워지도록 설정.
            # height_threshold = height / 20

            # kor_eng_height_threshold = height_threshold if height_threshold * 0.91 < 0.92 else 0.91
            # eng_height_threshold = height_threshold if height_threshold * 0.93 < 0.94 else 0.93
            
            if exist_hanja or exist_kor_vowel_consonant:
                continue
            elif (exist_kor_eng 
                  and line[1][1] < 0.91 # 정확도 체크. 
                  ): 
                continue
            elif (exist_eng 
                  and line[1][1] < 0.92 # 정확도 체크.
                  ):
                continue
            elif line[1][1] < 0.89:
                continue

            for ax in line[0]:
                ax[1]+=cut_line
                # log.info(f"ax: {ax}")
            
            bbox = line[0]
            # Not the first line
            if prev_bbox is not None and json_text_list:
                over_width_threshold = bbox[0][0] - prev_bbox[2][0]  > width_threshold
                over_height_threshold = bbox[0][1] - prev_bbox[2][1]  > height_threshold                

                if (over_width_threshold or over_height_threshold):  
                    json_text_list[-1]+=("\n")

            json_text_list.append(replace_text(line[1][0]))
            prev_bbox = bbox            

        # 문자와 바운딩박스 좌표를 dict으로 묶어서 리스트에 추가
            image_data.append({'text': replace_text(line[1][0]), "bbox":line[0]})
        
        image_data.insert(0, " ".join(json_text_list))
        ocr_sequence.append(image_data)    

        cut_line += cut_pix_list[i+1] - cut_pix_list[i]

    log.info(f"[SUCCESS] OCR completed.")

    return ocr_sequence


def make_ocr_sequence_json(output_path, image_path, cut_pix_list):
    """
    image_path: img tag src attribute. e.g link of img.

    cut_pix_list: sorted cutline list.
    """
    
    if not os.path.exists('./ocr_jsons'):
        os.mkdir('./ocr_jsons')

    # 이미지 로드
    if 'http' in image_path:
        res = requests.get(image_path)
        image = Image.open(BytesIO(res.content))
    else:
        image = Image.open(image_path)

    width = image.size[0]   # 이미지 가로

    ocr_sequence = []
    height_sequence = []
    tortion_sequence = []
    ocr_sequence_text = ""
    height_sequence_text = ""
    tortion_sequence_text = ""
    # .만 임의로 넣어주고.
    # tagging을 한 이후로 다시 돌려서 중요한 정보들만 추출하자.
    cut_line = 0
    for i in range(len(cut_pix_list)-1):
        box = (0, cut_pix_list[i], width, cut_pix_list[i+1])
        cropped_image_arr = np.asarray(image.crop(box), dtype='uint8')
        result = ocr_engine.ocr(cropped_image_arr, cls=True)

        if not result or not result[0]:
            continue
    
        for line in result[0]:
            # 글자 이상한 것 체크.
            exist_kor_eng = eng_ptrn.search(line[1][0]) and kor_ptrn.search(line[1][0])
            exist_eng = eng_ptrn.search(line[1][0])
            exist_hanja = hanja_ptrn.search(line[1][0])
            exist_kor_vowel_consonant = kor_vowel_consonant_ptrn.search(line[1][0])
            bbox = line[0]
            # height = max(bbox[3][1] - bbox[1][1], bbox[2][1] - bbox[0][1]) # 최대 높이 기준. 이게 클수록 OCR이 잘되기에 까다로워지도록 설정.
            # tortion = max(bbox[3][1] - bbox[2][1], bbox[1][1] - bbox[0][1])
            
            # height_threshold = height / 20

            # kor_eng_height_threshold = height_threshold if height_threshold * 0.91 < 0.92 else 0.91
            # eng_height_threshold = height_threshold if height_threshold * 0.93 < 0.94 else 0.93
            
            if exist_hanja or exist_kor_vowel_consonant:
                continue
            elif (exist_kor_eng 
                  and line[1][1] < 0.91 # 정확도 체크. 
                  ): 
                continue
            elif (exist_eng 
                  and line[1][1] < 0.92 # 정확도 체크.
                  ):
                continue
            elif line[1][1] < 0.89:
                continue

            for ax in line[0]:
                ax[1]+=cut_line
            
            trimmed_text =  replace_text(line[1][0])
        # 문자와 바운딩박스 좌표를 dict으로 묶어서 리스트에 추가
            ocr_sequence.append({'text': trimmed_text, "bbox":line[0]})
            ocr_sequence_text += " "+trimmed_text
            # if height < 30:
            #     height_sequence.append({'text': trimmed_text, "bbox":line[0], "size": height})
            #     height_sequence_text += " "+trimmed_text
            # if tortion/height > 0.15:
            #     tortion_sequence.append({'text': trimmed_text, "bbox":line[0], "tortion": tortion})
            #     tortion_sequence_text += " "+trimmed_text
        
        # cut_line에는 이전 라인의 높이를 더해줌.
        cut_line += cut_pix_list[i+1] - cut_pix_list[i]
            

    image_filename = image_path[image_path.rfind("\\")+1:].replace('.jpg', '').replace('.png', '')
    
    
    # ocr_sequence.insert(0,ocr_sequence_text.lstrip())
    # height_sequence.insert(0,height_sequence_text)
    # tortion_sequence.insert(0,tortion_sequence_text)

    if not os.path.exists(f"./{output_path}"):
        os.mkdir(f"./{output_path}")
    
    count = 1
    final_fp = ""
    while True:
        if os.path.exists(f"./{output_path}/{image_filename}_{count}.json"):
            count+=1
        else:
            final_fp = f"./{output_path}/{image_filename}_{count}.json"
            break

    with open(final_fp,'w', encoding='utf-8-sig') as json_file:
        json.dump(ocr_sequence, json_file, ensure_ascii=False)
    # with open(f'./ocr_jsons_test/{image_filename}_{i}_h_under30.json','w', encoding='utf-8-sig') as json_file:
    #     json.dump(height_sequence, json_file, ensure_ascii=False)
    # with open(f'./ocr_jsons_test/{image_filename}_{i}_tortion02.json','w', encoding='utf-8-sig') as json_file:
    #     json.dump(tortion_sequence, json_file, ensure_ascii=False)    

    log.info(f"[SUCCESS] OCR completed.")

    return ocr_sequence


def last_OCR_image(folder_name, cut_pix_list):
    image_list = os.listdir(folder_name)
    # 이미지 잘린 순서대로 정렬
    image_list = sorted(image_list, key=lambda x: int(''.join(filter(str.isdigit, x))))

    # 텍스트랑 좌표 1:1로 매칭시켜서 넣을 리스트
    ocr_sequence=[]
    for image_index, cut_line in zip(image_list, cut_pix_list[:-1]):
        image_path=os.path.join(folder_name, image_index)
        # ocr 수행
        result=ocr_engine.ocr(image_path, cls=True)
        

        if not result or not result[0]:
            continue
        
        # 픽셀을 나눠놨기 때문에 result의 바운딩 박스 y좌표에 gap을 더해줘야함
        for line in result[0]:
            # 글자 이상한 것 체크.
            exist_kor_eng = eng_ptrn.search(line[1][0]) and kor_ptrn.search(line[1][0])
            exist_eng = eng_ptrn.search(line[1][0])
            exist_hanja = hanja_ptrn.search(line[1][0])
            exist_kor_vowel_consonant = kor_vowel_consonant_ptrn.search(line[1][0])
            bbox = line[0]
            height = max(bbox[3][1] - bbox[1][1], bbox[2][1] - bbox[0][1]) # 최대 높이 기준. 이게 클수록 OCR이 잘되기에 까다로워지도록 설정.
            height_threshold = height / 20

            kor_eng_height_threshold = height_threshold if height_threshold * 0.91 < 0.92 else 0.91
            eng_height_threshold = height_threshold if height_threshold * 0.93 < 0.94 else 0.93
            
            if exist_hanja or exist_kor_vowel_consonant:
                continue
            elif (exist_kor_eng 
                  and line[1][1] < kor_eng_height_threshold # 정확도 체크. 
                  ): 
                continue
            elif (exist_eng 
                  and line[1][1] < eng_height_threshold # 정확도 체크.
                  ):
                continue

            for ax in line[0]:
                ax[1]+=cut_line
        # 문자와 바운딩박스 좌표를 dict으로 묶어서 리스트에 추가
            ocr_sequence.append({'text':line[1][0], "bbox":line[0]})
        
        # 임시로 만들었던 폴더 제거
    if os.path.exists(folder_name):
        for file_name in os.listdir(folder_name):
            file_path = os.path.join(folder_name, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        os.rmdir(folder_name)

    return ocr_sequence     #바운딩 박스 좌표랑 문자가 튜플로 묶인 리스트 반환


