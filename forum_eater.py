import os
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
import selenium.common.exceptions
# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# windows only. due to the keys.control used.




def retrieve_participants(targeturl,driver,main_url): # twitter only so far. Can generalise?
    # print("requested s9e...")
    
    driver.execute_script("window.open('about:blank',);")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(targeturl)
    while True:
        participantsoup = BeautifulSoup(driver.page_source,features="lxml")
        participants = participantsoup.find("div",class_="userList").find_all("li",class_="userList-row")
        participantlist = []
        for item in participants:
            userprofile = main_url + item.find("h3",class_="contentRow-header").find("a")["href"]
            username = item.find("h3",class_="contentRow-header").text
            number_replies_in_thread = item.find("div",class_="contentRow-extra--largest").text.replace("\n","").replace("\t","")
            messages = item.find("div",class_="contentRow-minor").find_all("li")[0].text.replace("Messages","").replace(",","").replace("\n","").replace("\t","")
            reactionscore = item.find("div",class_="contentRow-minor").find_all("li")[1].text.replace("Reaction score","").replace(",","").replace("\n","").replace("\t","")
            points = item.find("div",class_="contentRow-minor").find_all("li")[2].text.replace("Points","").replace(",","").replace("\n","").replace("\t","")
            participantlist.append({"Profile Link": userprofile,"Username":username,"Replycount":number_replies_in_thread,"Lifetime Message Count":messages,"Lifetime Reaction score":reactionscore,"Lifetime Points":points})
        if participantsoup.find("a",class_="pageNav-jump pageNav-jump--next"):
            driver.get(main_url+participantsoup.find("a",class_="pageNav-jump pageNav-jump--next")["href"])
        else:
            break
    # print(srclink)
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return participantlist





main_url = "https://forums.hardwarezone.com.sg/"
service = Service(executable_path="geckodriver.exe")
driver = webdriver.Firefox(service=service)

driver.get("https://forums.hardwarezone.com.sg/forums/eat-drink-man-woman.16/")
all_saved_threads = []
while True:
    currentcoord = driver.execute_script("return window.pageYOffset + window.innerHeight")
    while True:
        lastcount = currentcoord
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0,"+str(currentcoord+150)+")")
        currentcoord = driver.execute_script("return window.pageYOffset + window.innerHeight")
        # print(currentcoord,lastcount)
        if lastcount==currentcoord:
            break
    # print("Scrolled")
    time.sleep(3)


    htmlpage = driver.page_source
    soup = BeautifulSoup(htmlpage, features="lxml")
    page_threads = soup.find("div",class_="js-threadList")
    for thread in page_threads.find_all("div",class_="structItem--thread"):
        # print(thread)
        if thread.get("data-author"):
            author = thread["data-author"]
        else:
            author = None
        threadurl = main_url + thread.find("div",class_="structItem-title").find("a")["href"]
        threadtitle = thread.find("div",class_="structItem-title").find("a").text
        starter_info = thread.find("div",class_="structItem-minor")
        starter_href = main_url + starter_info.find("ul",class_="structItem-parts").find("a")["href"]
        starter_name = starter_info.find("ul",class_="structItem-parts").find("a").text
        thread_start_time = starter_info.find("li",class_="structItem-startDate").find("time")["datetime"]
        
        
        replies_views = thread.find("div",class_="structItem-cell--meta")
        replies = replies_views.find_all("dl")[0].text.replace("Replies:","")
        views = replies_views.find_all("dl")[1].text.replace("Views:","")
        try:
            participantlist = retrieve_participants(main_url+replies_views.find_all("dl")[0].find("a")["href"], driver, main_url)
        except TypeError: # Not currently available.
            participantlist = []
        thread_information = {"URL":threadurl,"Author":author,"Title":threadtitle,"Initiator":{"Profile":starter_href,"Username":starter_name},"Replies":replies,"Views":views,"Participants":participantlist,"Thread Start Time":thread_start_time}
        all_saved_threads.append(thread_information)
        # print(thread_information)
        # input()
        
    with open("thread_directories.json","w",encoding="utf-8") as dumpfile:
        json.dump(thread_information,dumpfile,indent=4)
    if soup.find("a",class_="pageNav-jump pageNav-jump--next"):
        print("flipping pages...")
        driver.get(main_url+soup.find("a",class_="pageNav-jump pageNav-jump--next")["href"])
    else:
        break
        