from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem, SoftwareEngine, HardwareType, Popularity, SoftwareType
import random
import requests
from route_handler.route_handler import RouteHandler

route_handler = RouteHandler()  

def set_user_agent(ip_list_len):
    user_agent_rotator = UserAgent(
                    hardware_types=HardwareType.COMPUTER.value,
                    software_types=SoftwareType.WEB_BROWSER.value,
                    software_names=SoftwareName.CHROME.value, 
                    operating_systems=OperatingSystem.WINDOWS.value,
                    popularity=Popularity.POPULAR.value,
                    limit=1000
                    )
                # # Get list of user agents.
    user_agents = user_agent_rotator.get_user_agents()
    random.shuffle(user_agents)
    user_agent_list = []

    for ua in user_agents:
        if "Windows NT 10.0; Win64; x64" in ua['user_agent']:
            user_agent_list.append(ua['user_agent'])
            if len(user_agent_list) == ip_list_len:
                break
    
    return user_agent_list

def insert_ip(ip_list, user_agent_list):    
    data = [{
            "address":ip,
            "user_agent":ua,
            "country":"KR",
            "naver": "unused",
                } for ip, ua in zip(ip_list, user_agent_list)]                
    res_text, res_code = route_handler.upsert_ip(data)
    if not res_text or not res_code:
        print(f'Error on request.')     
    else:
        print(f'[INFO] {res_text}, {res_code}')

def delete_ip(address):
    res_text, res_code = route_handler.delete_ip(address)
    if not res_text or not res_code:
        print(f'Error on request.')     
    else:
        print(f'[INFO] {res_text}, {res_code}')


if __name__ == "__main__":    
    # proxy_list
    proxy_list = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]    
    user_agent_list = set_user_agent(len(proxy_list))    
    insert_ip(proxy_list, user_agent_list)

    # delete_ip
    # for i in proxy_list:
    #     delete_ip(i)




    



    

