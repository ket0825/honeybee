# 태그 매치
"""https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
# XPATH 예시들.
"""https://selenium-python.readthedocs.io/locating-elements.html"""

# TODO: ip banned case.
# TODO: crawled at the last review...

#stdlib
import json
import time
import random
import datetime
import re
import os
from argparse import ArgumentParser

# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

# custom lib.
from log import Logger 
from image_processing.ocr_engine import OCREngine
from image_processing.image_function_main import char_pix_extract, make_ocr_sequence
from route_handler.route_handler import RouteHandler


log = Logger.get_instance()
route_handler = RouteHandler()
double_space_ptrn = re.compile(r" {2,}")
double_newline_ptrn = re.compile(r"\n{2,}")
access_word_ptrn = re.compile(r"[^가-힣ㄱ-ㅎㅏ-ㅣ0-9a-zA-Z\s'\"@_#$\^&*\(\)\-=+<>\/\|}{~:…℃±·°※￦\[\]÷\\;,\s]")

def get_links(path:str) -> list:
    with open(path, 'r', encoding='utf-8-sig') as json_file:
        product_raw_json = json.load(json_file)
        links = [item['url'] for item in product_raw_json['items']]
        product_names = [item['name'] for item in product_raw_json['items']]
        category = product_raw_json['category']
        match_nv_mids = [item['match_nv_mid'] for item in product_raw_json['items']]
        return links, product_names, category, match_nv_mids


def ocr_function(src):
    cut_pix_list = char_pix_extract(src)    
    return make_ocr_sequence(src, cut_pix_list, width_threshold=150, height_threshold=100)

def fetch_product_detail(driver: Driver):
    top_info = driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'top_info_inner_')]")[0]
    top_cells = top_info.find_elements(By.XPATH, ".//span[contains(@class, 'top_cell_')]")    
    
    brand = ""
    maker = ""
    grade = -1
    name = "",
    lowest_price = -1,

    for cell in top_cells:
        if '브랜드' not in cell.text and '제조사' not in cell.text:
            continue
        if '브랜드' in cell.text and '카탈로그' not in cell.text:
            brand = cell.text.replace("브랜드","").replace(" ","")
        elif '제조사' in cell.text:
            maker = cell.text.replace("제조사","").replace(" ","")
    
    # Get grade 
    try:
        grade = driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'top_grade_')]").text
        grade = float(grade.replace("평점", ""))
    except:
        pass
    
    # Get name
    try:
        name = driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'top_summary_title_')]/h2").text
    except:
        pass

    try:
        lowest_price = driver.driver.find_element(By.XPATH, ".//em[contains(@class, 'lowestPrice_num_')]").text
        lowest_price = lowest_price.replace(",", "").replace("원", "")
    except:
        pass

    return brand, maker, grade, name, lowest_price

def is_banned(naver_shopping_driver:Driver):
    # IP Blocked 시, floating tab이 안나옴. 이걸로 체크.
    try:
        floating_tabs = naver_shopping_driver.wait_until_by_xpath(10, ".//div[contains(@class, 'floatingTab_detail_tab')]")
        return False
    except:
        if naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'content_error')]"):
            log.warning("[WARNING] IP Blocked.")
            # 이후 proxy ip 바꿔서 naver_shopping_driver 다시 얻어야 함.
            naver_shopping_driver.set_ip_dirty()
            naver_shopping_driver.get_current_url()
            return True


def fetch_spec(driver:Driver):    
    driver.driver.find_element(By.XPATH, ".//a[contains(@class, 'top_more_')]").click() # 더 보기 클릭.
    spec_dict = {}
    time.sleep(2)
    tables = driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'attribute_product_attribute_')]/table")
    for table in tables:
        table_rows = table.find_elements(By.XPATH, ".//tr")
        for row in table_rows:
            keys = row.find_elements(By.XPATH, ".//th")
            vals = row.find_elements(By.XPATH, ".//td")
            for key, val in zip(keys, vals):
                spec_dict[key.text] = val.text

    return spec_dict

def get_image_specs(driver:Driver, xpath):
    """
    Get image specs with xpath.
    ------------
    return
    image_urls: list[dict] / image url, loc, size
    seller_spec: list[list] / ocr results

    """
    web_elements = driver.driver.find_elements(By.XPATH, xpath)
    image_urls = [] # image, location, size
    seller_spec = []
    for web_element in web_elements:
        src = web_element.get_attribute('src')
        # .gif, 동영상 등의 확장자를 막기 위함.
        if '.jpg' not in src and '.png' not in src:
            continue            

        driver.move_to_element(web_element)
        time.sleep(3)
        
        img_url_dict = {
            'img_url': "",
            'img_loc': [],
            'img_rendered_size':[],
        }

        img_url_dict['img_url'] = src
        img_url_dict['img_loc'] = [web_element.location['x'], web_element.location['y']]
        img_url_dict['img_rendered_size'] = [web_element.size['width'], web_element.size['height']]
        image_urls.append(img_url_dict)
        seller_spec.append(ocr_function(src))
    
    log.info(f"[INFO] seller_spec: {seller_spec}")
    return seller_spec, image_urls

# TODO: later, it should be an multiprocessing.
def fetch_product_spec(driver:Driver):
    spec_info_section = driver.driver.find_element(By.XPATH, ".//h3[contains(@class, 'specInfo_section_title__')]")
    driver.move_to_element(element=spec_info_section)

    # html tag에 height가 있는데...?
    naver_spec =  {} 
    seller_spec =  []
    img_urls = []
    
    # 본 컨텐츠는 ... 부분 위치.
    try:
        driver.wait_until_by_xpath(3, ".//p[contains(@class, 'imageSpecInfo_provide_')]")
    except:
        try:
            driver.wait_until_by_xpath(3, ".//p[contains(@class, 'specInfo_provide_')]") # 이미지 스펙 없는 경우.
        except TimeoutException:
            log.info(f"[WARNING] There is no product details.")    

    # 일반적인 테이블 스펙 추출 가능한지 확인.
    try:
        driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'imageSpecInfo_export_')]")
    except:
        # 안되면 naver spec.
        log.info(f"[INFO] No export spec at here.")
        try:
            tables = driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'attribute_product_attribute_')]/table")
            for table in tables:
                table_rows = table.find_elements(By.XPATH, ".//tr")
                for row in table_rows:
                    keys = row.find_elements(By.XPATH, ".//th")
                    vals = row.find_elements(By.XPATH, ".//td")
                    for key, val in zip(keys, vals):
                        naver_spec[key.text] = {
                                            'text': val.text, 
                                            'location': [val.location['y'], val.location['x']]
                                            }
        except:
            log.info(f"[WARNING] There is no product details.")
                
    # brand content banner 존재 시.
    # TODO: # 사진 가져오고, 이후 병렬처리 (multiprocessing)    
    # try:
    #     seller_spec_payload, img_urls_payload = get_image_specs(driver, ".//div[contains(@class, 'brandContent_export_')]/img")
    #     seller_spec.extend(seller_spec_payload)
    #     img_urls.extend(img_urls_payload)        
    # except NoSuchElementException:
    #     pass
    try:
        seller_spec_payload, img_urls_payload = get_image_specs(driver, ".//p[contains(@id, 'detailFromBrand')]/img")
        seller_spec.extend(seller_spec_payload)
        img_urls.extend(img_urls_payload)        
    except NoSuchElementException:        
        pass

    return naver_spec, seller_spec, img_urls

def review_formatter(reviews:list[dict]) -> None:
    # remain_key = ['id', 'content', 'aidaModifyTime', 'mallId', 'mallSeq', 'matchNvMid', 'qualityScore', 'starScore', 'topicCount', "topicYn", 'topics', 'userId', 'mallName']    
    keys_to_remove = ["aidaCreateTime", "esModifyTime", "modifyDate", "pageUrl", "registerDate", "imageCount", "imageYn", "images", "mallProductId", "mallReviewId", "rankScore", "title", "videoCount", "videoYn", "videos", "mallLogoUrl"]
    for review in reviews:
        for key in keys_to_remove:
            review.pop(key)
        
        review['content'] = review['content'].replace('<br>', '\n')\
                                            .replace('<br/>', '\n')\
                                            .replace("\r\n", "\n")\
                                            .replace("\r", "\n")
        
        review['content'] = BeautifulSoup(review['content'], 'lxml').text
        review['content'] = access_word_ptrn.sub("", review['content'])
        review['content'] = double_space_ptrn.sub(" ", review['content'])
        review['content'] = double_newline_ptrn.sub("\n", review['content'])
        review['content'] = review['content'].strip()

def log_filter(log_):
    return (
        # is an actual response
        log_["method"] == "Network.responseReceived"
        # and json
        and "json" in log_["params"]["response"]["mimeType"]
    )

def upsert_review(naver_shopping_driver: Driver, prid:str, match_nv_mid:str, s_category:str, type:str="R0"):
    """
    Flush log buffer and upsert reviews.
    """
    # Get review log
    chrome_logs_raw = naver_shopping_driver.driver.get_log("performance")
    chrome_logs = [json.loads(lr["message"])["message"] for lr in chrome_logs_raw]
    total_reviews = []    
    for log_ in filter(log_filter, chrome_logs):
        request_id = log_["params"]["requestId"]
        resp_url = log_["params"]["response"]["url"]
        if '/api/review' in resp_url:    
            # review url 구조:"https://search.shopping.naver.com/api/review?isNeedAggregation=N&nvMid=42620727618&page=4&pageSize=20&sortType=RECENT"
            log.info(f"Caught {resp_url}")        
            reviews = json.loads(naver_shopping_driver.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})['body'])['reviews']
            review_formatter(reviews)
            total_reviews.extend(reviews)

    # Complete review formatting.
    # post request to db.
    payload = {
        'type': type,
        'category': s_category,
        'prid': prid,
        'match_nv_mid': match_nv_mid,
        'reviews': total_reviews
    }                                                                             
    res_text, res_code = route_handler.upsert_review_batch(payload)
    log.info(f"[INFO] {res_text}, {res_code}")
    

def review_crawler(category:str, type:str,
                    headless=False, 
                    active_user_agent=False, 
                    use_proxy=False) -> None:
    
    naver_shopping_driver = Driver(headless=headless, active_user_agent=active_user_agent, use_proxy=use_proxy, get_log=True)        
    
    s_category_row = route_handler.get_category(s_category=category)
    caid = s_category_row[0]['caid']    

    products = route_handler.get_product(caid=caid)
    
    for product in products:
        # 원래는 크롤링한 사이트 링크들.
        # if flag or name == "데이비드테크 엔보우 N패드 네오":
        #     flag = True
        # else:
        #     continue
        prod_dict = {
                "grade": "",
                "name": "",
                "lowest_price": "",
                "review_count": "",
                "url": "",
                "brand": "",
                "maker": "",
                "naver_spec": "",
                "seller_spec": "",
                "detail_image_urls": "",
            }
        for key in product.keys():
            prod_dict[key] = product[key]

        url = product['url']
        name = product['name']
        
        naver_shopping_driver.get(url)
        naver_shopping_driver.set_current_url()
        log.info(f"[INFO] Start crawling at {name}.")

        # TODO: test cases:
        # 디알고 헤드셋. 적은 평점.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/36974003618?adId=nad-a001-02-000000223025435&channel=nshop.npla&cat_id=%EB%94%94%EC%A7%80%ED%84%B8/%EA%B0%80%EC%A0%84&NaPm=ct%3Dlu2l3ulc%7Cci%3D0zW0003ypdPztN%5FoFfjw%7Ctr%3Dpla%7Chk%3Dc6b52bbfde6b3967102cd5b772f10fb97a2d3356&cid=0zW0003ypdPztN_oFfjw")
        # 어프어프. 리뷰 없음.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/45960130619?&NaPm=ct%3Dludqbeyg%7Cci%3Dc6cf7cf700e756c885e4e7e9829c11d935a7e990%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3Dbc572d7cb475be323262c78ba2bdd1074c1f6d81")
        # 로지텍 K830: 리뷰 27000개
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/8974763652?&NaPm=ct%3Dlucr5xuw%7Cci%3D5549087459ddae34d93daf8f0d9e0686cf56ea87%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3D784343aaa845130bbe75468952f58e847fc0499c")
                
        while is_banned(naver_shopping_driver):
            pass

        # get product detail         
        brand, maker, grade, name, lowest_price = fetch_product_detail(naver_shopping_driver)
                
        log.info(f"[INFO] Brand: {brand}, Maker: {maker}")
        prod_dict["brand"] = brand
        prod_dict["maker"] = maker
        if grade != -1:
            prod_dict["grade"] = grade
        if name != "":
            prod_dict["name"] = name
        if lowest_price != -1:
            prod_dict["lowest_price"] = lowest_price        
        
        
        # 제품 상세 보러가기
        floating_tabs = naver_shopping_driver.wait_until_by_xpath(10, ".//div[contains(@class, 'floatingTab_detail_tab')]")                
        tabs = floating_tabs.find_elements(By.XPATH, ".//li")
        product_details = None
        review_tab = None
        # for initialization.
        if len(tabs) > 2:
            product_details = tabs[1]
            review_tab = tabs[2]
        for tab in tabs:
            if '제품정보' in tab.text:
                product_details = tab
            elif '쇼핑몰리뷰' in tab.text:
                review_tab = tab

        # 리뷰 개수 가져오기.
        if review_tab:        
            review_count_text = review_tab.find_element(By.XPATH, ".//em").text
            review_count = int(review_count_text.replace(",", "").replace("개", ""))
            prod_dict["review_count"] = review_count

        if product_details:
            naver_shopping_driver.move_to_element(element=product_details)
            product_details.click()

        # 제품 상세 더보기 있는 경우와 없는 경우 둘 다 있음.
        try:
            btn_detail_more = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'imageSpecInfo_btn_detail_more')]")
            naver_shopping_driver.move_to_element(element=btn_detail_more)
            btn_detail_more.click()
        except:
            log.warning("[WARNING] No see more button.")
        
        # 제품 상세에서 ocr 및 location 따기
        naver_spec, seller_spec, img_urls = fetch_product_spec(naver_shopping_driver)

        if not naver_spec:
            naver_spec = fetch_spec(naver_shopping_driver)            
        
        log.info(f"[INFO] Spec: {naver_spec}")
        prod_dict["naver_spec"] = naver_spec  
        prod_dict["seller_spec"] = seller_spec
        prod_dict["detail_image_urls"] = img_urls

        # fetch product detail
        res_text, res_code = route_handler.update_product_detail_one(data=prod_dict)      
        log.info(f"[INFO] {name} product detail updated. Response: {res_text}, Code: {res_code}")

        # 리뷰 크롤링하기.
        review_filters = naver_shopping_driver.driver.find_elements(By.XPATH, ".//ul[contains(@class, 'filter_top_list_')]/li")
        review_filters.pop(0) # 필터 중 전체 별점 제거.
        
        # 필요 없는 log 제거.
        naver_shopping_driver.flush_log()
        
        # 리뷰가 없는 제품인 경우. 스킵함.
        try:
            sort_by_recent = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'filter_sort') and contains(@data-nclick, 'rec')]") # recent라는 뜻임.
        except Exception as e:
            log.warning(f"[WARNING] No Reviews in {name}. Go to next product.")
            continue
            
        # Marking
        current_review_filter_score = review_filters[0].text.split(" ")[0] # 초기값은 첫번째 필터의 "n점"
        current_page_num = 1
        retry_count = 0

        review_crawling_done = False
        while not review_crawling_done:
            if retry_count > 3:
                log.warning(f"[WARNING] Review crawling count over 3. Go to next product.")
                break
            retry_count += 1

            flag_until_banned_review_filter = False
            flag_until_banned_page_num = False
            for review_filter in review_filters:
                # IP Blocked 시 다시 driver를 띄울 때, 리뷰 grade를 특정 수치로 설정해서 넘어가게끔 함.                                
                if is_banned(naver_shopping_driver):
                    break
                if flag_until_banned_review_filter or current_review_filter_score == review_filter.text.split(" ")[0]:
                    flag_until_banned_review_filter = True                    
                if not flag_until_banned_review_filter:
                    continue                

                naver_shopping_driver.move_to_element(element=sort_by_recent) # just move to sort_by_recent. Not crawling with sort_by_recent.

                # click하고 밴 체크 -> 동일한 패턴임.
                review_filter.click()
                time.sleep(random.randint(4,8)*0.5)
                if is_banned(naver_shopping_driver):
                    break

                current_review_filter_score = review_filter.text.split(" ")[0]
                is_last_page = False
                # 100개 이상이면 리뷰가 없음.
                while (not is_last_page 
                    and current_page_num < 102 # prevent while infinite loop.
                    ): 
                    review_section = naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'review_section_review')]")
                    review_pages = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'pagination_pagination')]/a")        
                    
                    if not review_pages: # 리뷰 자체가 한 페이지면 리뷰 로그 얻고 종료.
                        is_last_page = True
                        upsert_review(naver_shopping_driver, prid=prod_dict['prid'], match_nv_mid=prod_dict.get('match_nv_mid'), s_category=category, type=type)                    
                        continue

                    if 'next' not in review_pages[-1].get_attribute('class'): # next라는게 없을 때까지 -> 리뷰의 끝까지.
                        is_last_page = True

                    for review_page in review_pages:
                        # move_to_marker = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'reviewItems_btn_area')]")[-1]
                        time.sleep(random.randint(4,8)*0.5)
                        if is_banned(naver_shopping_driver):
                            is_last_page = True
                            break

                        is_current_page = 'now' in review_page.get_attribute('class')
                        is_prev_pages_button = 'prev' in review_page.get_attribute('class')
                        
                        if is_prev_pages_button:
                            continue
                        elif is_current_page:
                            current_page_num+=1
                            upsert_review(naver_shopping_driver, prid=prod_dict['prid'], match_nv_mid=prod_dict.get('match_nv_mid'), s_category=category, type=type)                    
                            continue
                        
                        if not flag_until_banned_page_num and '다음' in review_page.text:
                            review_page.click()
                            continue

                        if flag_until_banned_page_num or current_page_num == int(review_page.text):
                            flag_until_banned_page_num = True                    
                        
                        if not flag_until_banned_page_num:
                            continue        

                        log.info(f"[INFO] Current page_num: {current_page_num}")

                        naver_shopping_driver.move_to_element(element=review_page)
                        review_page.click()

                        try:
                            # 100 페이지를 넘어가려고 하면 경고가 나옴.
                            naver_shopping_driver.driver.switch_to.alert.accept()
                            log.warning(f"[WARNING] Over 2000+ review.")
                            is_last_page = True
                            break
                        except:
                            pass
                        time.sleep(random.randint(4,8)*0.5)                                    
                        upsert_review(naver_shopping_driver, prid=prod_dict['prid'], match_nv_mid=prod_dict.get('match_nv_mid'), s_category=category, type=type)                                       
                        current_page_num+=1

            
            review_crawling_done = True
        
        log.info(f"[SUCCESS] {name} crawled complete.")


    naver_shopping_driver.release()


if __name__ == '__main__':    
    parser = ArgumentParser(description='Review crawler for naver shopping. Enter the category.')
    parser.add_argument('--category', type=str, help='Enter the category you want to crawl.', default="keyboard")
    parser.add_argument('--headless', type=bool, help='Set headless mode.', default=False)
    parser.add_argument('--use_proxy', type=bool, help='Set use proxy ip.', default=False)
    parser.add_argument('--active_user_agent', type=bool, help='Active user agent.', default=False)
    parser.add_argument('--type', type=str, help='Enter the type.', default="R0")

    args = parser.parse_args()

    log.info(f"[INFO] Start crawling at {args.category}")
    log.info(f"[INFO] Headless: {args.headless}, Use proxy: {args.use_proxy}, Active user agent: {args.active_user_agent}")
    review_crawler(category=args.category, headless=args.headless, 
                         active_user_agent=args.active_user_agent, 
                         use_proxy=args.use_proxy,
                         type=args.type)    
    log.info(f"[SUCCESS] Success at {args.category}")
    
    




