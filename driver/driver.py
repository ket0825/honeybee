import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import ActionChains

from route_handler.route_handler import RouteHandler

#TODO: proxy ip list need.
"""
프록시 서버 필요함... 아래 링크 참조.
https://jaehyojjang.dev/python/free-proxy-server/
"""

from log import Logger
log = Logger.get_instance()
DEBUG = True

## Option 목록.
# #지정한 user-agent로 설정합니다.
# user_agent = "Mozilla/5.0 (Linux; Android 9; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.83 Mobile Safari/537.36"
# options.add_argument('user-agent=' + user_agent)

# options.add_argument('headless') #headless모드 브라우저가 뜨지 않고 실행됩니다.
# options.add_argument('--window-size= x, y') #실행되는 브라우저 크기를 지정할 수 있습니다.
# options.add_argument('--start-maximized') #브라우저가 최대화된 상태로 실행됩니다.
# options.add_argument('--start-fullscreen') #브라우저가 풀스크린 모드(F11)로 실행됩니다.
# options.add_argument('--blink-settings=imagesEnabled=false') #브라우저에서 이미지 로딩을 하지 않습니다.
# options.add_argument('--mute-audio') #브라우저에 음소거 옵션을 적용합니다.
# options.add_argument('incognito') #시크릿 모드의 브라우저가 실행됩니다.


"""
언제까지 웹드라이버가 기다릴지.
https://selenium-python.readthedocs.io/waits.html
"""

"""
각 종 find 참고.
https://www.geeksforgeeks.org/find_element_by_xpath-driver-method-selenium-python/
"""
# 느긋하게 하려면 options.set_capability("pageLoadStrategy"... 이 부분 주석처리.
class Driver:
    
    def __init__(self, headless=True, active_user_agent=False, use_proxy=False, get_log=True) -> None:
        # TODO: start from log requests.
        # make chrome log requests
        # capabilities["loggingPrefs"] = {"performance": "ALL"}  # newer: goog:loggingPrefs
        self._ip_obj = {}
        self._route_handler = RouteHandler()        
        options = self.set_options(headless, active_user_agent, use_proxy, get_log)
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                       options=options)
        # save options
        self.headless = headless
        self.active_user_agent=  active_user_agent
        self.use_proxy = use_proxy
        self.get_log = get_log

        # save current url
        self.current_url = ""
    
    def set_options(self, headless=False, active_user_agent=False, use_proxy=False, get_log=True) -> Options:
        options = Options()
        if headless:
            options.add_argument("--headless=new")

        if active_user_agent or use_proxy:        
            ip_row = self._route_handler.get_ip(unused=True)        
            
            unused_ip = ip_row[0]
            self._ip_obj = unused_ip        
                          
        if active_user_agent:                           
            log.info(f"user_agent: {self._ip_obj['user_agent']}")
            options.add_argument(f'user-agent={self._ip_obj["user_agent"]}')    

        if use_proxy and not DEBUG:            
            options.add_argument('--proxy-server=%s' % self._ip_obj["address"])           
            log.info(f"Proxy: {self._ip_obj['address']}")
            
                            
        options.add_argument('--mute-audio')
        options.add_argument("--disable-gpu") 
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-cookies')
        options.add_argument("--no-sandbox")
        # options.add_argument("--blink-settings=imagesEnabled=false") # Image Disable
        options.add_argument('--disable-blink-features=AutomationControlled')    # Automation detection disable
        preferences = {
            "profile.default_content_setting_values.notifications": 2, # prevent web cookie notification
            "webrtc.ip_handling_policy" : "disable_non_proxied_udp", # prevent IP leak issues.
            "webrtc.multiple_routes_enabled": False, # prevent IP leak issues.
            "webrtc.nonproxied_udp_enabled" : False, # prevent IP leak issues.
            # "profile.default_content_setting_values.cookies": 2
        }
        options.add_experimental_option("excludeSwitches", ["enable-automation"]) # automation message exclude.
        options.add_experimental_option('useAutomationExtension', False) 
        options.add_experimental_option("detach", True)
        options.add_experimental_option("prefs", preferences)    # Add Preferences
        # capa = DesiredCapabilities.CHROME
        # options.set_capability("pageLoadStrategy", 'none') # does not wait loading.
        if get_log:
            options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
        options.set_capability("acceptInsecureCerts", True)
        # capa["pageLoadStrategy"] = "none" # does not wait loading.
        # capa['acceptInsecureCerts'] = True
        # capa['acceptSslCerts'] = True
        return options

    def get(self, url:str) -> None:
        self.driver.get(url)

    def get_url_by_category(self, category:str) -> None:
        self.page = 1
        if category == 'smartwatch':
            self.driver.get(f"https://search.shopping.naver.com/search/category/100005046?adQuery&catId=50000262&origQuery&pagingIndex=1&pagingSize=40&productSet=model&query&sort=rel&spec=M10016843%7CM10664435&timestamp=&viewType=list")
        elif category == 'extra_battery':
            self.driver.get(f"https://search.shopping.naver.com/search/category/100005088?adQuery&catId=50001380&origQuery&pagingIndex=1&pagingSize=40&productSet=model&query&sort=rel&timestamp=&viewType=list")
        elif category == 'keyboard':
            self.driver.get(f"https://search.shopping.naver.com/search/category/100005369?adQuery&catId=50001204&origQuery&pagingIndex=1&pagingSize=40&productSet=model&query&sort=rel&timestamp=&viewType=list")
        elif category == 'monitor':
            self.driver.get(f"https://search.shopping.naver.com/search/category/100005309?adQuery&catId=50000153&origQuery&pagingIndex=1&pagingSize=40&productSet=model&query&sort=rel&timestamp=&viewType=list")

    def get_current_url(self):
        self.driver.get(self.current_url)
    
    def set_current_url(self):
        self.current_url = self.driver.current_url
    
    def go_next_page(self):
        if self.driver.current_url:
            url = self.driver.current_url.replace(f"pagingIndex={self.page}", f"pagingIndex={self.page+1}")
            self.driver.get(url)
            log.info(f"[MOVED] GO TO NEXT PAGE: {self.page} -> {self.page+1}")
            self.page +=1
        else:
            log.error("[ERROR] no current URL.")

    def flush_log(self):
        if self.get_log:
            self.driver.get_log('performance')
        
        


    def wait(self, time:float) -> None:
        self.driver.implicitly_wait(time_to_wait=time)
    
    def wait_until_by_css_selector(self, time:float, class_name:str) -> None:
        WebDriverWait(self.driver, time).until(EC.element_to_be_clickable((By.CSS_SELECTOR, class_name)))
    
    def move_to_element(self, element:WebElement):
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        
    def wait_until_by_xpath(self, time:float, value:str) -> WebElement:            
        return WebDriverWait(self.driver, time).until(EC.element_to_be_clickable((By.XPATH, value)))
    
    def screenshot_whole(self, path:str): # 미완성.
        """
        제품정보 섹션이 아닌, 전체 캡처 =>  OCR 돌리면 오래걸림.
        """
        # S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll'+X)
        # self.driver.set_window_size(S('Width'), S('Height'))
        # img_b64 =self.driver.find_element(By.TAG_NAME, 'body').screenshot(path)
    
    # def find_element_by_xpath(self, element, element_name):
    #     """
    #     XML 형식에 따라 parsing함. 궁금하다면 XML 확인.
    #     """
    #     self.driver.find_element(By.XPATH, "f{element}")
    
    # 태그 매치
    """https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
    def release(self):
        self.driver.quit()
        log.info("DRIVER CLOSING...")
    
    def proxy_check(self):
        self.driver.get("https://www.whatismyip.com/")
        self.driver.implicitly_wait(5)
        proxy_ip = self.driver.find_element(By.XPATH, '//*[@id="ipv4"]/span')        
        print("Proxy Setting:", proxy_ip.text)

    def set_ip_dirty(self):
        """
        Set ip dirty and restart driver.
        """
        if self._ip_obj['naver'] == 'unused':
            self._ip_obj['naver'] = 'dirty'
            self._route_handler.upsert_ip([self._ip_obj])

            log.info(f"IP: {self._ip_obj['address']} set dirty.")            
            self.driver.quit()
            log.info("DRIVER CLOSING...")
            time.sleep(5)
            # Restart driver.
            options = self.set_options(headless=self.headless, active_user_agent=self.active_user_agent, use_proxy=self.use_proxy, get_log=self.get_log)
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                           options=options)
        else:
            log.error("[ERROR] IP is not unused. Can't set dirty.")
            log.info("DRIVER CLOSING...")
            self.release()


if __name__ == '__main__':
    driver = Driver(headless=False, active_user_agent=True, use_proxy=True, get_log=False)
    # driver.proxy_check()
    # driver.release()
    driver.get_url_by_category('smartwatch')
    driver.set_ip_dirty()
    driver.get_url_by_category('keyboard')
    driver.release()
