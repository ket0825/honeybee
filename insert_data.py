import requests
import json
import os

from route_handler.route_handler import RouteHandler

route_handler = RouteHandler()

def request_product_match(local=True):    
    with open('./api_call/20240402_04h11m_keyboard_product_link_3.json', 'r', encoding="utf-8-sig") as f:
        data = json.load(f)
    
    res = route_handler.upsert_product_match(data)
    print(res[0], res[1])  

    with open('./api_call/20240330_15h10m_extra_battery_product_link_3.json', 'r', encoding="utf-8-sig") as f:
        data = json.load(f)
    
    res = route_handler.upsert_product_match(data)
    print(res[0], res[1])  


def request_product_detail(local=True):
    with open('./api_call/20240330_15h10m_extra_battery_product_link_3.json', 'r', encoding="utf-8-sig") as f:
        data = json.load(f)
        # prid를 가진 상태, caid를 가진 상태에서 시작해야 함.


    category = data.get('category')
    res = route_handler.get_category(s_category=category)
    caid = res[0].get('caid')
    type = data.get('type')
        
    prod_dict = {
            "grade": "",
            "name": "",
            "lowest_price": "",
            "review_count": "",
            "url": "",
            "brand": "",
            "maker": "",
            "naver_spec": {},
            "seller_spec": {},
            "detail_image_urls": [],
        }
    seller_spec = {}
    for item in data.get('items'):        
        name = item.get('name')               
            
        match_nv_mid = item.get('match_nv_mid')
        res = route_handler.get_product(match_nv_mid=match_nv_mid)
        
        product = res[0]
        for key in product.keys():
            prod_dict[key] = product.get(key)        

        old_seller_spec = seller_spec
        

        for json_name in os.listdir(f'./ocr_jsons_processed3/'):
            with open(f'./ocr_jsons_processed3/{json_name}', 'r', encoding="utf-8-sig") as f:                
                if json_name == f"{name}.json":
                    seller_spec = json.load(f)
                    break
        if old_seller_spec == seller_spec:
            print(f"OCR JSON NOT FOUND: {name}")
            seller_spec = {}
        else:    
            prod_dict['seller_spec'] = seller_spec            
        
        for key in prod_dict.keys():
            if not prod_dict[key]:
                prod_dict[key] = None
        
        res_text, res_status_code = route_handler.update_product_detail_one(data=prod_dict)
        
        print(res_text, res_status_code)

def request_reviews(local=True):
    review_dir = r"./reviews"
    for review_file in os.listdir(review_dir):
        review_path = os.path.join(review_dir, review_file)

        if not review_path.endswith(".json"):
            continue        
        
        # if (
        #     "디엠케이코리아 스피디 8핀 도킹형 보조배터리 5000mah SPE" in review_file 
        #     or
        #     "데이비드테크 엔보우 P20" in review_file
        #     ):
        #     print(review_file)
        # else:
        #     continue

        with open(review_path, 'r', encoding="utf-8-sig") as f:
            data = json.load(f)        

        match_nv_mid = data[0].get('matchNvMid')
        packets = {
            "match_nv_mid": match_nv_mid,
            "type": "R0",
            "reviews":data,
        }        

        res_text, res_status_code = route_handler.upsert_review_batch(packets)
        print(res_text, res_status_code)
        if res_status_code == 400:
            print(review_path)
    
    # OK.

    # review_dir = r"./reviews_keyboard"
    # for review_file in os.listdir(review_dir):
    #     review_path = os.path.join(review_dir, review_file)

    #     if not review_path.endswith(".json"):
    #         continue        

    #     with open(review_path, 'r', encoding="utf-8-sig") as f:
    #         data = json.load(f)

        

    #     match_nv_mid = data[0].get('matchNvMid')
    #     packets = {
    #         "match_nv_mid": match_nv_mid,
    #         "type": "R0",
    #         "reviews":data,
    #     }        

    #     res_text, res_status_code = route_handler.upsert_review_batch(packets)
    #     print(res_text, res_status_code)
    #     if res_status_code == 400:
    #         print(review_path)

if __name__ == '__main__':
    request_product_match(local=True)
    request_product_detail(local=True)
    request_reviews(local=True)




    


        
    



