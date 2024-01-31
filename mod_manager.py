import requests
from bs4 import BeautifulSoup

class Manager():

    def __init__(self):
        pass

    def mod_search(self,q):
        html = requests.get("https://modrinth.com/mods?q="+q)
        soup = BeautifulSoup(html.content, "html.parser")

        result = []

        for div in soup.find_all("article", class_="project-card"):
            a = div.find_all("a",class_="icon")[0]["href"]
            if div.find_all("img",class_="avatar") != []:
                img = div.find_all("img",class_="avatar")[0]["src"]
            else:
                img = ""
            title = div.find_all("h2",class_="name")[0].text
            result.append({'name': title, "icon":img, "href": a})

        return result

    def get_mod_files(self,mod_url):
        html = requests.get("https://modrinth.com"+mod_url+"/versions#all-versions")
        soup = BeautifulSoup(html.content, "html.parser")

        result = []

        for div in soup.find_all("div", class_="version-button"):
            a = div.find_all("a",class_="download-button")[0]["href"]
            title = div.find_all("a",class_="version__title")[0].text
            result.append({'title': title, "download": a})

        return result

manager = Manager()
#print(manager.mod_search("create"))