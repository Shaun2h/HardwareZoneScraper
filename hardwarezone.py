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

# todo, quotes. facebook embeds?


import requests
src_ignore_list = ["https://www.hardwarezone.com.sg/newsletters/subscribefooter","https://sg-config.sensic.net/","googlesyndication.com/safeframe/"]

def retrieves9e_twitter(targeturl,driver): # twitter only so far. Can generalise?
    # print("requested s9e...")
    driver.execute_script("window.open('about:blank',);")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(targeturl)
    s9esoup = BeautifulSoup(driver.page_source,features="lxml")
    srclink = s9esoup.find("a")
    # print(srclink)
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return srclink["href"]


def retrieves9e_facebook(targeturl,driver): # twitter only so far. Can generalise?
    # print("requested s9e...")
    driver.execute_script("window.open('about:blank',);")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(targeturl)
    s9esoup = BeautifulSoup(driver.page_source,features="lxml")
    srclink = s9esoup.find("div",class_="fb_iframe_widget")
    # print(srclink)
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    if srclink["data-href"]:
        return srclink["data-href"]
    else:
        return targeturl #didn't work.. some facebook related mishap?

def iframesearch(targetpost,ignorelist,driver):
    # print(targetpost)
    if targetpost.name!="iframe":
        iframes = targetpost.find_all("iframe")
    else:
        iframes  = [targetpost]
    returnsrclist = []
    for iframe_instance in iframes:
        # print(i)
        
        try:
            if iframe_instance["aria-label"]=="Advertistment":
                # print("Skipping Advertistment.")
                return []
        except KeyError: # not aria.
            try:
                # print("Source:",iframe_instance["src"])
                ignore=False
                for ignoreitem in ignorelist:
                    if ignoreitem in iframe_instance["src"]:
                        ignore=True
                        # print(ignoreitem,i["src"])
                if not ignore:
                    if "https://s9e.github.io/" in iframe_instance["src"]:
                        if "twitter" in iframe_instance["src"]:
                            s9e_src = retrieves9e_twitter(iframe_instance["src"],driver)
                            returnsrclist.append(s9e_src)
                        elif "facebook" in iframe_instance["src"]:
                            s9e_src = retrieves9e_facebook(iframe_instance["src"],driver)
                            returnsrclist.append(s9e_src)
                        else:
                            returnsrclist.append(iframe_instance["src"])

                        
                    else:
                        returnsrclist.append(iframe_instance["src"])
                    
            except KeyError:
                # print("no src.")
                pass
    return returnsrclist

def youtube_noniframe_search(targetpost):
    allyoutubevids = targetpost.find_all("a",class_="ytp-title-link")
    return_items = []
    for item in allyoutubevids:
        try:
            return_items.append(item["href"])
        except KeyError:
            continue
    return return_items
    
    
def sequential_extract_post_contents(targetpost,ignorelist,driver,ignore_blockquotes=True):
    # print("extraction begins")
    if targetpost.find("div",class_="bbWrapper"):
        targetpost = targetpost.find("div",class_="bbWrapper") # the rest is forgettable or unimportant.
    astringthusfar = ""
    consecutivelist = []
    # print("--------------------Target Post:--------------------")
    # print(targetpost)
    for child in targetpost.children:
        # input()
        # print("-"*500)
        # print(child)
        if child.name=="blockquote" and not ignore_blockquotes: # quotation...
            if astringthusfar:
                consecutivelist.append(astringthusfar)
                astringthusfar=""
            # blockquotehandling here
            # print("initiating jump....--------------------------------------")
            # print(child)
            consecutivelist.append(sequential_extract_post_contents(child,ignorelist,driver))
            # print("blockquote garbage here.")
            
        elif child.name=="div" and "bbCodeBlock-title" in child["class"]:
            consecutivelist.append(child.find("a")["href"])
            consecutivelist.append(child.find("a").text)

            
        elif child.name=="div" and "bbCodeBlock-content" in child["class"]:
            consecutivelist.append(sequential_extract_post_contents(child.find("div",class_="bbCodeBlock-expandContent js-expandContent"),ignorelist,driver,False))
            
        elif child.name=="iframe":
            if astringthusfar:
                consecutivelist.append(astringthusfar)
                astringthusfar=""
            returned_sources = iframesearch(child,ignorelist,driver)
            consecutivelist.extend(returned_sources)
            # print("found iframe")
            
        elif child.name=="span" and child.get("data-s9e-mediaembed"):
            # print("detected")
            if astringthusfar:
                consecutivelist.append(astringthusfar)
                astringthusfar=""
            if child.get("data-s9e-mediaembed")== "youtube":
                returned_sources = iframesearch(child,ignorelist,driver)
                print(returned_sources)
                consecutivelist.extend(returned_sources)
                # print("detected a youtube s9e span.")
                
            elif child.get("data-s9e-mediaembed")== "facebook":
                returned_sources = iframesearch(child,ignorelist,driver)
                print(returned_sources)
                consecutivelist.extend(returned_sources)
                # print("detected a youtube s9e span.")
            else:
                # print(child)
                consecutivelist.append(child) #unparsable????
                

        elif child.name=="div":
            if child.get("class") and  "fauxBlockLink" in child["class"]:
                # faux quote block inside. Handle here
                # print("detection...")
                if child.get("data-host")=="www.channelnewsasia.com":
                    # used for like an embedded CNA article.
                    sideitem = child.find("div",class_="contentRow-figure contentRow-figure--fixedSmall js-unfurl-figure")
                    articlemini_image = sideitem.find("img")["src"]
                    maincolumn = child.find("div",class_="contentRow-main")
                    articlelink = maincolumn.find("h3",class_="contentRow-header js-unfurl-title").find("a")["href"]
                    maintitle = maincolumn.find("h3",class_="contentRow-header js-unfurl-title").find("a").text
                    article_description = maincolumn.find("div",class_="contentRow-snippet js-unfurl-desc").text
                    speakerlink = maincolumn.find("div",class_="contentRow-minor contentRow-minor--hideLinks").find("span",class_="skimlinks-unlinked").text
                    consecutivelist.append([articlemini_image,articlelink,maintitle,article_description,speakerlink])
            elif child.get("class") and "bbCodeBlock-expandContent" in child["class"]:
                # normal speech in an expanded. quote.
                consecutivelist.append(sequential_extract_post_contents(child,ignorelist,driver))
            elif child.get("class") and "bbImageWrapper" in child["class"]:
                # print("imagechild detected.")
                # print(child)
                images = child.find_all("img")
                print(images)
                for image in images:
                    # print("appending... : ", image["src"])
                    consecutivelist.append(image["src"])
            else:
                consecutivelist.append(str(child)) # unparsable????
            
        elif child.name=="br":
            astringthusfar = astringthusfar+"\n"
        else:
            astringthusfar = astringthusfar+child.text # probably headers and the such...
    if astringthusfar:
        consecutivelist.append(astringthusfar)
        astringthusfar=""
    # print("it's like super DONEEEEZO", "*"*500)
    return consecutivelist

def extract_header(targetpost):
    header = targetpost.find("header",class_="message-attribution message-attribution--split")
    postlink = header.find("li",class_="u-concealed").find("a")["href"]
    datetime = header.find("time")["datetime"]
    header.decompose()
    return postlink,datetime,targetpost

def extract_user(targetpost):
    userportion = targetpost.find("div",class_ = "message-cell message-cell--user")
    try:
        userimagesource = userportion.find("div",class_="message-avatar-wrapper").find("img")["src"]
    except TypeError:
        userimagesource = None
    userdet = userportion.find("div",class_="message-userDetails").find("h4").find("a")
    userlink = userdet["href"]
    username = userdet.text
    usertitle = userportion.find("div",class_="message-userDetails").find("h5").text
    otherdetails = userportion.find("div",class_="message-userExtras").find_all("dl")
    returndetails = []
    for dets in otherdetails:
        returndetails.append(dets.text)
    userportion.decompose()

    return userimagesource,userlink,username,usertitle,returndetails,targetpost



def reaction_check(post):
    reaction_part = post.find_all("footer",class_="message-footer")[-1] # always take the last one as it's the reaction piece.
    reaction_part = reaction_part.find("div",class_="reactionsBar js-reactionsList is-active")
    return_reactions = {}
    if reaction_part:
        if reaction_part.find("a",class_="reactionsBar-link"):
            print("reactions")
            driver.execute_script("window.open('about:blank',);")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get("https://forums.hardwarezone.com.sg/"+reaction_part.find("a",class_="reactionsBar-link")["href"])
            reactionsoup = BeautifulSoup(driver.page_source,features="lxml")
            reactions = reactionsoup.find("h3",class_="tabs hScroller block-minorTabHeader").find_all("a",class_="tabs-tab")
            for reaction in reactions:
                if reaction.find("img"):
                    reactiontype = reaction.find("bdi").text
                    reactioncount = reaction.find("span",class_="reaction-text js-reactionText").text.replace(reactiontype,"").replace("(","").replace(")","")
                    return_reactions[reactiontype] = reactioncount
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
    return return_reactions
            



service = Service(executable_path="geckodriver.exe")
driver = webdriver.Firefox(service=service)


with open("thread_directories.json","r",encoding="utf-8") as dumpfile:
    thread_information = json.load(dumpfile)
dumpdir = "Threads"
if not os.path.isdir(dumpdir):
    os.mkdir(dumpdir)

for thread in thread_information:
    
    driver.get(thread["URL"])
    thread_posts = []
    while True:        
        expansions = driver.find_elements(by=By.CLASS_NAME,value = "js-expandLink")
        for element in expansions:
            driver.execute_script("arguments[0].click();", element.find_element(by=By.CSS_SELECTOR,value="a"))

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
        post_list = soup.find_all('article', class_="message message--post js-post js-inlineModContainer")
        for post in post_list:
            # print(post)
            userimagesource,userlink,username,usertitle,otherdetails, post = extract_user(post)
            # print("*"*50)
            # print("User Image Source:",userimagesource)
            # print("User Profile link:",userlink)
            # print("Username:",username)
            # print("User Title:",usertitle)
            # print("Other Details:",otherdetails)
            # print("*"*50)
            # print(post) # post minus user details.
            postlink,datetime,post = extract_header(post)
            # print("*"*50)
            # print("Postlink:",datetime)
            # print("Post Date:",postlink)
            # print("*"*50)
            # print(post) # post sans header.
            # input()
            
            
            reactions = reaction_check(post)
            # quote_ending=post.find("div",class_="js-selectToQuoteEnd")
            # print(post)
            itemsinchat = sequential_extract_post_contents(post,src_ignore_list,driver,False) # you want to ignore at the top level.
            userdata = {"username":username,"usertitle":usertitle,"userlink":userlink,"userimage":userimagesource,"other":otherdetails}
            postdata = {"time":datetime,"link":postlink,"reactions":reactions}
            # import pprint
            # pprint.pprint(userdata)
            # pprint.pprint(postdata)
            # pprint.pprint(itemsinchat)
            thread_posts.append({"User":userdata,"Posts":postdata,"Items":itemsinchat})
            # print(iframesearch(post,src_ignore_list,driver))
            # print(youtube_noniframe_search(post))
            # print("*"*500)
            # input()
        if soup.find("a",class_="pageNav-jump pageNav-jump--next"):
                driver.get("https://forums.hardwarezone.com.sg/"+soup.find("a",class_="pageNav-jump pageNav-jump--next")["href"])
        else:
            break
        # the normal selenium search is terrible for this because the pages are more complex. Iframes are constantly missed out.
    with open(os.path.join(dumpdir,thread["Title"]+".json"),"w",encoding="utf-8") as threaddump:
        json.dump([thread,thread_posts],threaddump,indent=4)


