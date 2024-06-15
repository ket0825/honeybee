#stdlib
import json
import datetime
import os
import re
from argparse import ArgumentParser
# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement

# custom lib.
from log import Logger 
log = Logger.get_instance()
from route_handler.route_handler import RouteHandler


match_nv_mid_ptrn = re.compile(r'nvMid=(\d+)')



def url_naver_formatter(url):
    nvmid = match_nv_mid_ptrn.search(url).group(1)
    if nvmid:
        return nvmid, f'https://search.shopping.naver.com/catalog/{nvmid}'
    else:
        print(f"[ERROR] No nvmid found in the url. {url}")


def price_formatter(price_element: WebElement) -> str:
    return int(price_element.text.replace(",", "").replace("원", ""))

def grade_formatter(grade_element: WebElement) -> str:
    grade_str = ""
    try:
        grade_blind = grade_element.find_element(By.XPATH, ".//span[@class='blind']")
        grade_str = grade_element.text.replace("\n", "").replace(grade_blind.text, "")
    except:
        grade_str =  grade_element.text
    
    return round(float(grade_str),2)

def review_count_formatter(review_count: WebElement) -> str:
    return int(review_count.text.replace(",", "").replace("\n", "").replace('(', '').replace(')', ''))

def product_link_crawler(category:str, type:str, page_num:int, 
                         headless=False, 
                         active_user_agent=False, 
                         use_proxy=False) -> None:
    # category = 'keyboard'
    naver_shopping_driver = Driver(headless=headless, active_user_agent=active_user_agent, use_proxy=use_proxy, get_log=False)
    
    # 태그 매치
    """https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
    # XPATH 예시들.
    """https://selenium-python.readthedocs.io/locating-elements.html"""
    # XPATH substring match.
    # link = naver_shopping_driver.driver.find_elements(By.XPATH, "//div[contains(@class, 'product_title_')/a]") 
    # username = driver.find_element(By.XPATH, "//form[input/@name='username']")
    # CSS_SELECTOR substring match.
    # link = naver_shopping_driver.driver.find_elements(By.CSS_SELECTOR, "div[class*='reviewItems_title']") # substring match.
    
    naver_shopping_driver.get_url_by_category(category)
    naver_shopping_driver.wait(5)
    
    product_dict = {
                    "category": category,
                    'url': naver_shopping_driver.driver.current_url,
                    'start_page': naver_shopping_driver.page,
                    'end_page': "",
                    'items': [],
                    'type': type,
                    }       

    # Crawling start.    
    items = []
    for p in range(page_num): # 1페이지부터 page_num까지임.
        try:
            footer = naver_shopping_driver.wait_until_by_xpath(3, ".//div[contains(@class, 'footer_info')]")
            naver_shopping_driver.move_to_element(element=footer)
            
            # 광고는 자동으로 걸러짐.
            product_items = naver_shopping_driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'product_item_')]") # substring match.        
            for item in product_items:
                item_dict = {
                                "url" : "",
                                "grade": "",
                                'name': "",
                                'lowest_price': "",
                                'review_count': "",
                                'brand': "", # 차후 넣을 예정.
                                'maker': "", # 차후 넣을 예정.
                                "match_nv_mid": "",
                               }
                # 링크와 제품명 추출.
                try:
                    a_tag = item.find_element(By.XPATH, ".//div[contains(@class, 'product_title_')]/a")
                    item_dict['match_nv_mid'], item_dict['url'] = url_naver_formatter(a_tag.get_attribute('href'))
                    item_dict['name'] = a_tag.get_attribute('title') # "/ 들어간 거 replace 하게 될수도"
                    items.append(item_dict)
                except Exception as e:
                    log.error(f'[ERROR] Could not catch product url and name.')

                # 가격 추출.
                try:
                    lowest_price = item.find_element(By.XPATH, ".//span[contains(@class, 'price_num_')]")
                    item_dict['lowest_price'] = price_formatter(lowest_price)
                # 별점 추출.
                except Exception as e:
                    log.error(f'[ERROR] Could not catch price at {item_dict["name"]}')
                try:
                    grade = item.find_element(By.XPATH, ".//span[contains(@class, 'product_grade_')]")
                    item_dict['grade'] = grade_formatter(grade)
                except Exception as e:
                    log.warning(f'[WARNING] Could not catch grade at {item_dict["name"]}')
                # 리뷰 개수 따오기.
                try:
                    grade_num = item.find_element(By.XPATH, ".//div[contains(@class, 'product_etc_')]/a/em[contains(@class, 'product_num')]")
                    # grade_num = product_etc.find_element(By.XPATH, ".//em[contains(@class, 'product_num')]")
                    item_dict['review_count'] = review_count_formatter(grade_num)
                except Exception as e:
                    log.warning(f'[WARNING] Could not catch grade_num at {item_dict["name"]}')
                
            if p < page_num - 1:
                naver_shopping_driver.go_next_page()
                
        except TimeoutException as e:
            # Without page of footers => it might be ip-banned.
            log.info(f"[ERROR] Time out error occured: Couldn't found footer or last page.\n\
                     Error log: {e}")
            if naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'content_error')]"):
                log.warning("[WARNING] IP Blocked.")
                naver_shopping_driver.set_ip_dirty()
            
        except Exception as e:
            log.info(f"[ERROR] Error log: {e}")
            if naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'content_error')]"):
                log.warning("[WARNING] IP Blocked.")
                naver_shopping_driver.set_ip_dirty()            

    current_time = datetime.datetime.now().strftime('%Y%m%d_%Hh%Mm')
    product_dict['items'] = items
    product_dict['end_page'] = naver_shopping_driver.page

    route_handler = RouteHandler()
    route_handler.upsert_product_match(product_dict)
    log.info(f"[SUCCESS] Success at {category}")

    # if not os.path.exists("./api_call"):
    #     os.mkdir("./api_call")

    # with open(f'./api_call/{current_time}_{category}_product_link.json', 'w', encoding='utf-8-sig') as json_file:
    #     json.dump(product_dict, json_file, ensure_ascii=False)
    #     log.info(f"[SUCCESS] Success at {category}")
    
    naver_shopping_driver.release()
    

if __name__ == '__main__':    
    parser = ArgumentParser(description='Product link crawler for naver shopping. Enter the category.')
    parser.add_argument('category', type=str, help='Enter the category you want to crawl.', default="keyboard")
    parser.add_argument('--headless', type=bool, help='Set headless mode.', default=False)
    parser.add_argument('--use_proxy', type=bool, help='Set use proxy ip.', default=False)
    parser.add_argument('--active_user_agent', type=bool, help='Active user agent.', default=False)
    parser.add_argument('--type', type=str, help='Enter the type.', default="P0")
    parser.add_argument('--page_num', type=int, help='Enter page_num.', default=5)
    args = parser.parse_args() 

    log.info(f"[INFO] Start crawling at {args.category}")
    log.info(f"[INFO] Headless: {args.headless}, Use proxy: {args.use_proxy}, Active user agent: {args.active_user_agent}")

    product_link_crawler(category=args.category, headless=args.headless, 
                         active_user_agent=args.active_user_agent, 
                         use_proxy=args.use_proxy,
                         type=args.type, page_num=args.page_num)
    log.info(f"[SUCCESS] Success at {args.category}")
    



