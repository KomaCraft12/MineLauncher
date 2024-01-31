import os
import zipfile
from io import BytesIO
import customtkinter
import minecraft_launcher_lib
import requests
from PIL import Image
import subprocess
import threading
import json
from CTkListbox import *
import mysql.connector as mysql
from bs4 import BeautifulSoup
import shutil
import webbrowser

class Database():
    def __init__(self):
        pass

    def alternative_connect(self):
        try:
            self.conn = mysql.connect(host="komacloud.asuscomm.com",user="jano",password="Katica.bogar2002",database="mclauncher")
        except mysql.Error as err:
            print(err)
    def connect(self):
        try:
            self.conn = mysql.connect(host="komacloud.synology.me",user="jano",password="Katica.bogar2002",database="mclauncher")
        except mysql.Error as err:
            print(err)
            self.alternative_connect()

    def disconnect(self):
        self.conn.close()
    def getTable(self,sql):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        self.disconnect()
        return result
    def insert(self,sql,data):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute(sql,data)
        self.conn.commit()
        lastid = cursor.lastrowid
        cursor.close()
        self.disconnect()
        return lastid
    def update(self,sql,data):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute(sql,data)
        self.conn.commit()
        cursor.close()
        self.disconnect()
        return True

database = Database()

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

class MineCraft():
    def __init__(self):
        self.installed_versions = []
        self.available_versions = []
        self.versions_json = {}
        self.director2 = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.director = "/modpacks/vanilla/"
        with open("setting.json","r") as file:
            self.json = json.loads(file.read())
        with open("setting.json","w") as file:
            if self.json["JavaDir"] == "":
                self.json["JavaDir"] = minecraft_launcher_lib.utils.get_java_executable()
            json.dump(self.json,file,indent=2)

    def getInstalledVersion(self):
        with open("versions.json","r") as file:
            self.versions_json = json.loads(file.read())
            lista = list(self.versions_json.keys())
        return lista
    def getAvailableVersion(self,type):
        self.getInstalledVersion()
        versions = minecraft_launcher_lib.utils.get_available_versions(self.director)
        #print(versions)
        for version in versions:
            if version["type"] == type and version['id'] not in self.installed_versions:
                self.available_versions.append(version['id'])
        return self.available_versions

mc = MineCraft()

class ModVersions(customtkinter.CTkToplevel):
    def __init__(self,master,master_old,mod_url,modpack_version):
        super().__init__(master)
        self.title("MineCraft")
        self.geometry('500x700')
        self.resizable(False, False)
        self.configure(fg_color="#8B4513")
        self.master_old = master_old
        self.mod_url = mod_url
        self.mod_versions = manager.get_mod_files(mod_url)
        self.modpack_version = modpack_version
        self.mod_frame = {}
        self.index = ""

        print(self.mod_versions)

        scrollable_frame = customtkinter.CTkScrollableFrame(self, height=550, width=460, fg_color="#CD853F")

        index = 0
        for version in self.mod_versions:

            image = Image.open("java.png")

            image2 = image.copy()
            image2.convert("RGBA")
            alpha = 0.75
            alpha_int = int(alpha * 255)
            image2.putalpha(alpha=alpha_int)
            icon_image = customtkinter.CTkImage(light_image=image2, size=(50, 50))

            self.mod_frame[index] = customtkinter.CTkFrame(scrollable_frame, fg_color="#D3D3D3", width=500, height=25)

            column_left = customtkinter.CTkFrame(self.mod_frame[index], fg_color="#D3D3D3", height=25, width=50)
            column_left.grid(row=0, column=0, padx=10, pady=10)
            column_right = customtkinter.CTkFrame(self.mod_frame[index], fg_color="transparent", height=25)
            column_right.grid(row=0, column=1)

            icon = customtkinter.CTkLabel(column_left, image=icon_image, text="", fg_color="transparent")
            icon.grid()

            label = customtkinter.CTkLabel(column_right, text=version["title"], text_color="#000")
            label.grid(row=0, column=0, padx=5, pady=3)

            self.mod_frame[index].pack(side=customtkinter.TOP, anchor="w", fill='x', expand=True, padx=10, pady=10)

            self.mod_frame[index].bind("<Button-1>", lambda event, mod_version_url=version['download'], index=index: self.frame_clicked(event,
                                                                                                    mod_version_url,index))

            index += 1

        scrollable_frame.grid(row=0, column=0, padx=10, pady=10)

        self.install_btn = customtkinter.CTkButton(self,text="Letöltés",command=self.download)
        self.install_btn.grid()

        self.progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal", progress_color="gray",fg_color="gray",height=25,width=480,determinate_speed=0.01)
        self.progressbar.set(0)
        self.progressbar.grid(padx=5,pady=5)

        self.file = customtkinter.CTkLabel(self, text="")
        self.file.grid(padx=5,pady=5)

        self.progress = customtkinter.CTkLabel(self, text="")
        self.progress.grid(padx=5,pady=5)

    def frame_clicked(self,event,mod_version_url,index):
        self.selected_version_url = mod_version_url
        self.mod_frame[index].configure(fg_color="#808080")
        if self.index != "":
            self.mod_frame[self.index].configure(fg_color="#D3D3D3")
        self.index = index

    def download(self):
        thread = threading.Thread(target=self.downloading)
        thread.start()
    def downloading(self):
        print(self.selected_version_url)

        self.install_btn.configure(state=False)
        self.progressbar.configure(progress_color="green")

        print(self.modpack_version)

        self.files = self.selected_version_url.split("/")[::-1][0]

        url = self.selected_version_url

        response = requests.get(url, stream=True)

        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0

        with open("modpacks/" + self.modpack_version + "/mods/" + self.files, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if bytes_downloaded % (10240000) == 0:
                        self.download_progress(bytes_downloaded, total_size)

    def download_progress(self, bytes_downloaded, total_size):
        progress = (bytes_downloaded / total_size) * 100
        self.file.configure(text="Fájl: "+self.files)
        self.progress.configure(text=f'Letöltés: {progress:.2f}% ({bytes_downloaded}/{total_size} bytes)')
        self.progressbar.set(bytes_downloaded / total_size)

class ModsView(customtkinter.CTkToplevel):
    def __init__(self,master):
        super().__init__(master)
        self.title("MineCraft")
        self.geometry('1300x650')
        self.resizable(False, False)
        self.configure(fg_color="#8B4513")
        self.mod_frame_2 = {}
        self.selected_mod = ""
        self.selected_mod_color = ""

        #8B4513

        self.scrollable_frame = customtkinter.CTkScrollableFrame(self, height=500, width=608, fg_color="#CD853F")
        self.scrollable_frame_2 = customtkinter.CTkScrollableFrame(self, height=500, width=608, fg_color="#CD853F")

        files = list(os.listdir(os.path.join("modpacks/"+master.selected_version.lower()+"/mods")))
        files2 = list(os.listdir(os.path.join("modpacks/"+master.selected_version.lower()+"/mods-disabled")))
        self.list_installed_mod(files,"enabled")
        self.list_installed_mod(files2,"disabled")

         # Use default argument

        #scrollable_frame.pack(side="top",fill="both", expand=True, in_=self)
        #frame.pack(side="top",fill="both", expand=True, in_=self)

        # MODOK LISTÁZÁSA

        label1 = customtkinter.CTkLabel(self,text="Telepített módok",font=("Arial",24))
        label1.grid(row=0,column=0,padx=10,pady=10)

        frame_jobb = customtkinter.CTkFrame(self, width=608, height=50, fg_color="#CD853F")
        frame_jobb.grid(row=1,column=1,padx=10,pady=10,sticky="ew")
        self.text = customtkinter.CTkTextbox(frame_jobb,height=25,width=500)
        self.text.grid(row=0,column=0,padx=10,pady=10)
        button = customtkinter.CTkButton(frame_jobb,text="Keresés",height=25,width=100,command=self.search,fg_color="green")
        button.grid(row=0,column=1)

        label2 = customtkinter.CTkLabel(self,text="Módok telepítése",font=("Arial",24))
        label2.grid(row=0,column=1,padx=10,pady=10)

        self.scrollable_frame.grid(row=3,column=0,padx=10, pady=10)
        self.scrollable_frame_2.grid(row=3,column=1,padx=10, pady=10)

        # Alsó sáv

        frame_bal = customtkinter.CTkFrame(self, width=608, height=50, fg_color="#CD853F")
        frame_bal.grid(row=1,column=0,padx=10, pady=10,sticky="ew")
        button_del = customtkinter.CTkButton(frame_bal,text="Törlés",fg_color="red",command=self.mod_remove)
        button_del.grid(row=0,column=0,padx=10,pady=10)
        button_disble = customtkinter.CTkButton(frame_bal, text="Letiltás",fg_color="orange",command=self.mod_disable)
        button_disble.grid(row=0, column=1,padx=10,pady=10)
        button_enable = customtkinter.CTkButton(frame_bal, text="Engedélyezés",fg_color="green",command=self.mod_enable)
        button_enable.grid(row=0, column=2,padx=10,pady=10)

    def list_installed_mod(self,files,mod):

        for file in files:
            image = Image.open("java.png")
            image2 = image.copy()
            image2.convert("RGBA")
            alpha = 0.4
            alpha_int = int(alpha * 255)
            image2.putalpha(alpha=alpha_int)
            icon_image = customtkinter.CTkImage(light_image=image2, size=(50, 50))

            color = "green" if mod == "enabled" else "red"

            self.mod_frame_2[file] = customtkinter.CTkFrame(self.scrollable_frame, fg_color="white", width=480, height=25)

            column_left = customtkinter.CTkFrame(self.mod_frame_2[file], fg_color=color, height=25, width=50)
            column_left.grid(row=0, column=0, padx=10, pady=10)
            column_right = customtkinter.CTkFrame(self.mod_frame_2[file], fg_color="transparent", height=25)
            column_right.grid(row=0, column=1)

            icon = customtkinter.CTkLabel(column_left, image=icon_image, text="", fg_color="transparent")
            icon.grid()

            label = customtkinter.CTkLabel(column_right, text=file, text_color="#000")
            label.grid(row=0, column=0, padx=5, pady=3)

            self.mod_frame_2[file].pack(side=customtkinter.TOP, anchor="w", fill='x', expand=True, padx=10, pady=10)

            self.mod_frame_2[file].bind("<Button-1>", lambda event, file=file: self.mod_selected(event,
                                                                                                 file))
    def clear_2(self):
        for widget in self.scrollable_frame_2.winfo_children():
            widget.destroy()
    def clear(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
    def mods(self,mods):

        for mod in mods:

            if mod["icon"] != '':
                response = requests.get(mod['icon'])
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                else:
                    image = Image.open("java.png")
            else:
                image = Image.open("java.png")

            image2 = image.copy()
            image2.convert("RGBA")
            alpha = 0.75
            alpha_int = int(alpha * 255)
            image2.putalpha(alpha=alpha_int)
            icon_image = customtkinter.CTkImage(light_image=image2, size=(50, 50))

            self.mod_frame = customtkinter.CTkFrame(self.scrollable_frame_2, fg_color="#D3D3D3", width=480,height=25)

            column_left = customtkinter.CTkFrame(self.mod_frame,fg_color="#D3D3D3",height=25, width=50)
            column_left.grid(row=0, column=0, padx=10, pady=10)
            column_right = customtkinter.CTkFrame(self.mod_frame,fg_color="transparent",height=25)
            column_right.grid(row=0,column=1)

            icon = customtkinter.CTkLabel(column_left, image=icon_image, text="", fg_color="transparent")
            icon.grid()

            label = customtkinter.CTkLabel(column_right,text=mod['name'],text_color="#000")
            label.grid(row=0,column=0,padx=5, pady=3)

            self.mod_frame.pack(side=customtkinter.TOP,anchor="w", fill='x', expand=True, padx=10, pady=10)

            self.mod_frame.bind("<Button-1>", lambda event, mod_url=mod['href']: self.frame_clicked(event,
                                                                                                    mod_url))
    def search(self):
        q = self.text.get("0.0",customtkinter.END).replace("\n","")
        mods = manager.mod_search(q)
        self.clear_2()
        self.mods(mods)

    def mod_selected(self,event,file):

        print(file)

        if self.selected_mod != "":
            self.mod_frame_2[self.selected_mod].configure(fg_color=self.selected_mod_color)
        self.selected_mod_color = self.mod_frame_2[file].cget("fg_color")
        self.mod_frame_2[file].configure(fg_color="#808080")
        self.selected_mod = file

    def mod_enable(self):
        print("enable: "+self.selected_mod)
        shutil.move("modpacks/" + self.master.selected_version.lower() + "/mods-disabled/" + self.selected_mod,
                    "modpacks/" + self.master.selected_version.lower() + "/mods/" + self.selected_mod)
        self.clear()
        files = list(os.listdir(os.path.join("modpacks/" + self.master.selected_version.lower() + "/mods")))
        files2 = list(os.listdir(os.path.join("modpacks/" + self.master.selected_version.lower() + "/mods-disabled")))
        self.list_installed_mod(files,"enabled")
        self.list_installed_mod(files2,"disabled")
    def mod_disable(self):
        if not(os.path.exists("modpacks/"+self.master.selected_version.lower()+"/mods-disabled")):
            os.mkdir("modpacks/"+self.master.selected_version.lower()+"/mods-disabled")
        print("disable: "+self.selected_mod)
        shutil.move("modpacks/"+self.master.selected_version.lower()+"/mods/"+self.selected_mod,
                    "modpacks/"+self.master.selected_version.lower()+"/mods-disabled/"+self.selected_mod)
        self.clear()
        files = list(os.listdir(os.path.join("modpacks/" + self.master.selected_version.lower() + "/mods")))
        files2 = list(os.listdir(os.path.join("modpacks/" + self.master.selected_version.lower() + "/mods-disabled")))
        self.list_installed_mod(files,"enabled")
        self.list_installed_mod(files2,"disabled")
    def mod_remove(self):
        print("remove: "+self.selected_mod)
        self.clear()
        files = list(os.listdir(os.path.join("modpacks/" + self.master.selected_version.lower() + "/mods")))
        files2 = list(os.listdir(os.path.join("modpacks/" + self.master.selected_version.lower() + "/mods-disabled")))
        self.list_installed_mod(files,"enabled")
        self.list_installed_mod(files2,"disabled")

    def frame_clicked(self,event,mod_url):
        new = ModVersions(self,self.master,mod_url,self.master.selected_version.lower())
        new.grab_set()


class ModpackDownload(customtkinter.CTkToplevel):
    def __init__(self,master):
        super().__init__(master)
        self.title("MineCraft")
        self.geometry('500x700')
        self.resizable(False, False)
        #self.modpacks = requests.get("https://minecraft.komaweb.eu/modpacks.json").json()
        self.modpacks = database.getTable("SELECT * FROM modpacks")
        self.key = ""
        self.modpack = ""
        self.modpack_frame = {}

        #print(os.getcwd())

        title_frame = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)

        title = customtkinter.CTkLabel(title_frame, text="Modpack letöltése", font=("Arial", 18), anchor='center', justify="center")
        title.pack(padx=20,pady=20)

        scrollable_frame = customtkinter.CTkScrollableFrame(self,height=400,width=480)

        for keys,elem in enumerate(list(self.modpacks)):

            # ICON

            response = requests.get(elem[2])
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                # Most már dolgozhat a képpel...
            else:
                print("Nem sikerült letölteni a képet.")
                image = "mc.jpg"

            image2 = image.copy()
            image2.convert("RGBA")
            alpha = 0.75
            alpha_int = int(alpha * 255)
            image2.putalpha(alpha=alpha_int)
            icon_image = customtkinter.CTkImage(light_image=image2, size=(100, 100))

            # MAIN FRAME
            self.modpack_frame[keys] = customtkinter.CTkFrame(scrollable_frame,fg_color="#D3D3D3")

            # COLUMNS
            column_left = customtkinter.CTkFrame(self.modpack_frame[keys],fg_color="#D3D3D3")
            column_left.grid(row=0, column=0, padx=10, pady=10)
            column_right = customtkinter.CTkFrame(self.modpack_frame[keys],fg_color="transparent")
            column_right.grid(row=0,column=1)

            icon = customtkinter.CTkLabel(column_left, image=icon_image, text="", fg_color="transparent")
            icon.grid()
            # SZÖVEGEK
            label = customtkinter.CTkLabel(column_right, text=elem[1], fg_color="transparent", font=("Arial",16), text_color="#000")
            label.grid(row=0,column=0,padx=130, pady=3)
            label2 = customtkinter.CTkLabel(column_right, text="Játékverzió: "+elem[3], fg_color="transparent",font=("Arial",10), text_color="#000")
            label2.grid(row=1,column=0,padx=130, pady=3)
            label3 = customtkinter.CTkLabel(column_right, text="Forge: " + elem[4] if elem[4] != '0' else '', fg_color="transparent",font=("Arial",10),text_color="#000")
            label3.grid(row=2,column=0,padx=130, pady=3)
            self.modpack_frame[keys].pack(side=customtkinter.TOP,anchor="w",fill='both', expand=True,padx=10, pady=10)


            icon.bind("<Button-1>", lambda event, keys=keys: self.frame_clicked(event, keys))
            column_right.bind("<Button-1>", lambda event, keys=keys: self.frame_clicked(event, keys))
            label.bind("<Button-1>", lambda event, keys=keys: self.frame_clicked(event, keys))
            label2.bind("<Button-1>", lambda event, keys=keys: self.frame_clicked(event, keys))
            label3.bind("<Button-1>", lambda event, keys=keys: self.frame_clicked(event, keys))
            self.modpack_frame[keys].bind("<Button-1>", lambda event, keys=keys: self.frame_clicked(event, keys))  # Use default argument

        action_frame = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)
        self.install_btn = customtkinter.CTkButton(action_frame,text="Telepítés",command=self.install)
        self.install_btn.pack(padx=20,pady=20)

        self.progressbar = customtkinter.CTkProgressBar(action_frame, orientation="horizontal", progress_color="gray",fg_color="gray",height=25,width=480,determinate_speed=0.01)
        self.progressbar.set(0)
        self.progressbar.pack(padx=5,pady=5)

        self.file = customtkinter.CTkLabel(action_frame, text="")
        self.file.pack(padx=5,pady=5)

        self.progress = customtkinter.CTkLabel(action_frame, text="")
        self.progress.pack(padx=5,pady=5)

        # FRAMES PRINTS
        title_frame.pack(side='top', fill="both", expand=False, in_=self)
        scrollable_frame.pack(side="top",fill="both", expand=True, in_=self)
        action_frame.pack(side="top",fill="both", expand=False, in_=self)

    def frame_clicked(self,event,keys):
        if self.key != "":
            self.modpack_frame[self.key].configure(fg_color="#fff")
        self.modpack_frame[keys].configure(fg_color="#808080")
        self.modpack = self.modpacks[keys]
        self.key = keys
        print(self.modpack)

    def install(self):

        thread = threading.Thread(target=self.installing)
        thread.start()

    def installing(self):
        self.install_btn.configure(state=False)
        self.progressbar.configure(progress_color="green")

        self.files = self.modpacks[self.key][5].split("/")[::-1][0]
        url = self.modpacks[self.key][5]

        response = requests.get(url, stream=True)

        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0

        if not(os.path.exists("temp/")):
            os.mkdir("temp")

        with open("temp/" + self.files, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if bytes_downloaded % (10240000) == 0:
                        self.download_progress(bytes_downloaded, total_size)

        self.bar_custom_unzip("temp/" + self.files, "modpacks/")

        dir_name = self.modpacks[self.key][1].lower()

        if self.modpacks[self.key][4] != "0":
            version = self.modpacks[self.key][3] + "-forge-" + self.modpacks[self.key][4]
        else:
            version = self.modpacks[self.key][3]

        with open("versions.json", "r") as file:
            version_list = json.loads(file.read())
            version_list[self.modpacks[self.key][1]] = {
                "version": version,
                "gameDirector": os.getcwd() + "\\modpacks\\" + dir_name,
                "icon": self.modpacks[self.key][2]
            }
        with open("versions.json", "w") as file:
            file.write(json.dumps(version_list, indent=2))

        self.install_btn.configure(state=True)

    def download_progress(self, bytes_downloaded, total_size):
        progress = (bytes_downloaded / total_size) * 100
        self.file.configure(text="Fájl: "+self.files)
        self.progress.configure(text=f'Letöltés: {progress:.2f}% ({bytes_downloaded}/{total_size} bytes)')
        self.progressbar.set(bytes_downloaded / total_size)
    def bar_custom_unzip(self, zip_file_path, extract_to):
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            file_count = len(zip_ref.infolist())
            extracted_count = 0
            for file_info in zip_ref.infolist():
                extracted_count += 1
                progress = extracted_count / file_count * 100
                # print(f'Extraction progress: {progress:.2f}% ({extracted_count}/{file_count})', end='\r')
                self.file.configure(text="Fájl: "+self.files)
                self.progress.configure(text=f'Telepítés: {progress:.2f}% ({extracted_count}/{file_count})')
                self.progressbar.set(extracted_count / file_count)
                zip_ref.extract(file_info, extract_to)
            self.file.configure(text="")
            self.progress.configure(text=f'Sikeres telepítés!')
            # print('\nExtraction complete.')
class ForgeModpack(customtkinter.CTkToplevel):
    def __init__(self,master):
        super().__init__(master)
        self.title("MineCraft")
        self.geometry('500x600')
        self.resizable(False, False)
        self.selected_version = ""
        self.isprogress = False
        self.version_name = ""
        self.listbox = ""
        self.isforge = customtkinter.StringVar()
        self.isforge.set("off")
        self.selected_forge_version = ""

        title_frame = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)

        title = customtkinter.CTkLabel(title_frame, text="Modpack létrehozása", font=("Arial", 18), anchor='center', justify="center")
        title.pack()

        name_frame = customtkinter.CTkFrame(self, fg_color="#8B4513", corner_radius=0)

        version_name_title = customtkinter.CTkLabel(name_frame, text="Modpack neve", font=("Arial", 16), height=25)
        version_name_title.pack()
        self.version_name = customtkinter.CTkTextbox(name_frame,height=25,width=480)
        self.version_name.pack()

        area_frame = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)

        version_title = customtkinter.CTkLabel(area_frame, text="Modpack verziója", font=("Arial", 16), height=25)
        version_title.pack()

        listbox = CTkListbox(area_frame,command=lambda x: self.update_base(x), fg_color="#CD853F")
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        for index,version in enumerate(mc.getAvailableVersion("release")):
            listbox.insert(index,version)

        checkbox = customtkinter.CTkCheckBox(area_frame, text="Forge", command=self.is_forge,
                                             variable=self.isforge, onvalue="on", offvalue="off", height=40, )
        checkbox.pack(fill="both",padx=10)

        self.version_title_2 = customtkinter.CTkLabel(area_frame, text="Forge Verzió", font=("Arial", 16), height=25)
        #self.version_title_2.pack()

        self.listbox = CTkListbox(area_frame,command=lambda x: self.update(x), fg_color="#CD853F")
        #self.listbox.pack(fill="both", expand=True, padx=10, pady=10)

        btn = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)
        self.button = customtkinter.CTkButton(btn,text="Telepítés",command=self.save,fg_color="#CD853F")
        self.button.pack()

        progress_frame = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)

        self.status = customtkinter.CTkLabel(progress_frame,text="")
        self.status.pack()


        self.progressbar = customtkinter.CTkProgressBar(progress_frame, orientation="horizontal",progress_color="gray",fg_color="gray",height=25,width=480,determinate_speed=0.01)
        self.progressbar.set(0)
        self.progressbar.pack()

        self.status2 = customtkinter.CTkLabel(progress_frame,text="",fg_color="transparent",height=20,corner_radius=0)
        self.status2.pack()

        title_frame.pack(side='top', fill="both", expand=True, in_=self)
        name_frame.pack(side='top', fill="both", expand=True, in_=self)
        area_frame.pack(side='top', fill="both", expand=True, in_=self)
        btn.pack(side="top", fill="both", expand=True, in_=self)
        progress_frame.pack(side='bottom', fill="both", expand=True, in_=self)

    def is_forge(self):
            if self.isforge.get() == "off":
                self.version_title_2.pack_forget()
                self.listbox.pack_forget()
                self.geometry('500x600')
            else:
                self.version_title_2.pack()
                self.listbox.pack(fill="both", expand=True, padx=10, pady=10)
                self.geometry('500x900')
    def update_selectlist_version(self):
        self.forge_versions = minecraft_launcher_lib.forge.list_forge_versions()
        current = self.selected_version
        print(current)
        self.forge_versions = list(filter(lambda x: current in x, self.forge_versions))

        for index,version in enumerate(self.forge_versions):
            self.listbox.insert(index,version)

    def update_base(self,value):
        self.selected_version = value
        self.update_selectlist_version()

    def update(self,value):
        self.selected_forge_version = value
    def printProgressBar(self,iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
        self.progressbar.set(iteration / float(total))
        percent = round(100 * (iteration / float(total)))
        self.status2.configure(text=str(percent)+"%")

        #percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        #filledLength = int(length * iteration // total)
        #bar = fill * filledLength + '-' * (length - filledLength)
        #print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printEnd)
        #self.progressbar.set((iteration / float(total)))
        # Print New Line on Complete
        if iteration == total:
            print()
    def maximum(self,max_value, value):
        max_value[0] = value
    def printText(self,value):
        self.status.configure(text=value)
        print(value)
        if value == "Installation complete":
            self.progressbar.stop()
            self.button.configure(state="normal")
    def install(self):
        self.button.configure(state="disabled")
        self.max_value = [0]
        callback = {
            "setStatus": lambda value: self.printText(value),
            "setProgress": lambda value: self.printProgressBar(value, self.max_value[0]),
            "setMax": lambda value: self.maximum(self.max_value,value)
        }

        version_name = self.version_name.get("1.0",customtkinter.END).replace("\n","")
        dir_name = " ".join(version_name.split()).replace(" ","_").replace("\n","").lower()
        os.mkdir("modpacks/"+dir_name)

        game_director = os.getcwd()+"\\modpacks\\"+dir_name

        version = self.selected_version if self.isforge.get() == "off" else self.selected_forge_version.replace("-","-forge-")

        with open("versions.json","r") as file:
            version_list = json.loads(file.read())
            version_list[version_name] = {
                "version": version,
                "gameDirector": game_director,
                "icon": ""
            }
        with open("versions.json","w") as file:
            file.write(json.dumps(version_list,indent=2))

        forge_version = self.selected_forge_version

        if self.isforge.get() == "on":
            minecraft_launcher_lib.forge.install_forge_version(forge_version, game_director, callback=callback)
        else:
            minecraft_launcher_lib.install.install_minecraft_version(self.selected_version, game_director, callback=callback)

    def save(self):
        self.progressbar.configure(progress_color="green")
        thread = threading.Thread(target=self.install, daemon=True)
        thread.start()

class Setting(customtkinter.CTkToplevel):

    def __init__(self,master):
        super().__init__(master)
        self.title("MineCraft")
        self.geometry('475x175')
        self.resizable(False, False)

        title = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)

        title_row = customtkinter.CTkLabel(title, text="Beállitások", font=("Arial", 18), anchor='center', justify="center")
        title_row.pack()

        frame = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)

        java_label = customtkinter.CTkLabel(frame,text="Java: ")
        java_label.grid(row=1, column=0, padx=10, pady=10)
        self.java = customtkinter.CTkTextbox(frame,400,10,fg_color="#CD853F")
        self.java.insert('0.0',mc.json['JavaDir'])
        self.java.grid(row=1,column=1,padx=10, pady=10)

        memory_label = customtkinter.CTkLabel(frame,text="RAM: ")
        memory_label.grid(row=2,column=0,padx=10, pady=10)
        self.memory = customtkinter.CTkTextbox(frame,400,10,fg_color="#CD853F")
        self.memory.insert('0.0',mc.json['RAM'])
        self.memory.grid(row=2,column=1,padx=10, pady=10)

        btn = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)

        button = customtkinter.CTkButton(btn,text="Mentés",command=self.save,fg_color="#CD853F")
        button.pack()

        title.pack(side='top', fill="both", expand=True, in_=self)
        frame.pack(side="top", fill="x", in_=self)
        btn.pack(side="bottom", fill="both", expand=True, in_=self)

    def save(self):
        mc.json["JavaDir"] = self.java.get("0.0",customtkinter.END).split("\n")[0]
        mc.json["RAM"] = self.memory.get("0.0",customtkinter.END).split("\n")[0]
        with open("setting.json", "w") as file:
            json.dump(mc.json, file, indent=2)

class MainWindow(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("MineCraft")
        self.geometry("1300x750")
        self.resizable(False, False)

        self.menu = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)
        self.news = customtkinter.CTkFrame(self,width=1300,height=650,fg_color="#8B4513",corner_radius=0)
        self.app = customtkinter.CTkFrame(self,fg_color="#8B4513",corner_radius=0)
        self.MC = MineCraft()
        self.selected_version = ""

        # MENU

        setting = customtkinter.CTkButton(self.menu, text="Beállitások",fg_color="#CD853F",command=self.open_setting)
        setting.grid(row=0, column=0, padx=10, pady=10)
        """version = customtkinter.CTkButton(self.menu, text="Modpack",fg_color="#CD853F",command=self.open_version)
        version.grid(row=0, column=1, padx=10, pady=10)
        """
        forge_version = customtkinter.CTkButton(self.menu, text="Modpack letöltése",fg_color="#CD853F",command=self.open_download_modpack)
        forge_version.grid(row=0, column=1, padx=10, pady=10)
        forge_version = customtkinter.CTkButton(self.menu, text="Modpack létrehozása",fg_color="#CD853F",command=self.open_forge_version)
        forge_version.grid(row=0, column=2, padx=10, pady=10)

        # NEWS

        """image = Image.open("mc4.jpg")
        image2 = image.copy()
        image2.convert("RGBA")
        alpha = 0.5
        alpha_int = int(alpha * 255)
        image2.putalpha(alpha=alpha_int)

        bg_image = customtkinter.CTkImage(light_image=image2,size=(1300,650))

        bg = customtkinter.CTkLabel(self.news,image=bg_image)

        bg.configure(text="")

        bg.pack(side="top", fill="both", expand=True)"""

        version_list_frame = customtkinter.CTkScrollableFrame(self.news,height=650,width=275,corner_radius=0)
        self.version_data_frame = customtkinter.CTkScrollableFrame(self.news,height=650,width=1010,corner_radius=0,fg_color="#CD853F")
        version_list_frame.grid(row=0,column=0)
        self.version_data_frame.grid(row=0,column=1)

        with open("versions.json","r") as file:
            versions = json.loads(file.read())
            for version_name in versions:

                version_name = str(version_name)

                if versions[version_name]["icon"] != "":
                    response = requests.get(versions[version_name]["icon"])
                    if response.status_code == 200:
                        image = Image.open(BytesIO(response.content))
                        # Most már dolgozhat a képpel...
                    else:
                        print("Nem sikerült letölteni a képet.")
                        image = Image.open("vanilla.png")
                else:
                    image = Image.open("vanilla.png")


                image2 = image.copy()
                image2.convert("RGBA")
                alpha = 0.75
                alpha_int = int(alpha * 255)
                image2.putalpha(alpha=alpha_int)
                icon_image = customtkinter.CTkImage(light_image=image2, size=(100, 100))

                # MAIN FRAME
                self.modpack_frame = customtkinter.CTkFrame(version_list_frame,fg_color="#D3D3D3")

                # COLUMNS
                column_left = customtkinter.CTkFrame(self.modpack_frame,fg_color="transparent")
                column_left.grid(row=0, column=0, padx=10, pady=10)
                column_right = customtkinter.CTkFrame(self.modpack_frame,fg_color="transparent")
                column_right.grid(row=0, column=1)

                icon = customtkinter.CTkLabel(column_left, image=icon_image, text="", fg_color="transparent")
                icon.grid()
                # SZÖVEGEK
                label = customtkinter.CTkLabel(column_right, text=version_name,text_color="#000",font=("Arial", 16))
                label.pack(side="top", fill="both", expand=True)
                self.modpack_frame.pack(side=customtkinter.TOP, anchor="w", fill='both', expand=True, pady=10, padx=10)

                icon.bind("<Button-1>", lambda event, keys=version_name: self.frame_clicked(event, keys))
                column_right.bind("<Button-1>", lambda event, keys=version_name: self.frame_clicked(event, keys))
                label.bind("<Button-1>", lambda event, keys=version_name: self.frame_clicked(event, keys))
                self.modpack_frame.bind("<Button-1>", lambda event, keys=version_name: self.frame_clicked(event,
                                                                                                        keys))  # Use default argument

        # FŐ
        self.button_frame = customtkinter.CTkFrame(self.version_data_frame,width=1025,height=50,fg_color="#CD853F")
        title_frame = customtkinter.CTkFrame(self.version_data_frame,width=1025,height=650,fg_color="#CD853F")

        self.modpack_title = customtkinter.CTkLabel(title_frame,text="",font=("Arial",32),text_color="#fff",fg_color="transparent")
        self.modpack_title.pack()

        self.news_frame = customtkinter.CTkFrame(self.version_data_frame,height=550,fg_color="transparent")
        self.news_frame2 = customtkinter.CTkScrollableFrame(self.version_data_frame,width=500,fg_color="transparent")
        #news_title = customtkinter.CTkLabel(news_frame,text="Ez egy hir cime lesz",font=("Arial",14))
        #news_title.pack()
        #news_desc = customtkinter.CTkLabel(news_frame,text="Ez meg egy leirása a hirnek ahol jó nagyon részletezzük amit ide le kell majd irni",font=("Arial",12))
        #news_desc.pack()

        self.button_frame.pack(side=customtkinter.TOP, anchor="w", fill='both', expand=True, pady=10, padx=10)
        title_frame.pack(side=customtkinter.TOP, anchor="w", fill='both', expand=True, pady=10, padx=10)
        #self.news_frame.pack(fill='y', expand=False, ipady=10, ipadx=10)
        #self.news_frame2.pack(fill='y', expand=False, ipady=10, ipadx=10)

        self.news_frame.pack(side="left", fill="both", expand=True, padx=10, pady=14)
        self.news_frame2.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # ----- APP -----

        # NÉV
        name_label = customtkinter.CTkLabel(self.app,text="Név:")
        name_label.grid(row=0, column=0, padx=10, pady=10)
        self.name = customtkinter.CTkTextbox(self.app,150,30,fg_color="#CD853F")
        self.name.grid(row=0,column=1,padx=10,pady=10)

        # Verzió
        """version_label = customtkinter.CTkLabel(self.app,text="Verzió:")
        version_label.grid(row=0, column=2, padx=10, pady=10)
        self.version = customtkinter.CTkOptionMenu(self.app,values=mc.getInstalledVersion(),height=30,dynamic_resizing=True,fg_color="#CD853F",dropdown_fg_color="#CD853F",button_color="#B26B26")
        self.version.grid(row=0, column=3, padx=10, pady=10)"""

        # Inditás
        start = customtkinter.CTkButton(self.app,text="Inditás",command=self.run,fg_color="green",height=30,width=200)
        start.grid(row=0, column=3, padx=490, pady=10)

        self.menu.pack(side="top", fill="x", in_=self)
        self.news.pack(side="top", fill="x", in_=self)
        self.app.pack(side="top", fill="x", in_=self)

    def clear_news(self):
        # Töröljük az összes hír frame-t
        for widget in self.news_frame2.winfo_children():
            widget.destroy()
        for widget in self.news_frame.winfo_children():
            widget.destroy()

        self.news_frame2.configure(scrollbar_button_color="#CD853F")
    def frame_clicked(self,event,keys):

        self.selected_version = keys
        print(keys)
        self.modpack_title.configure(text=keys)

        title = ""

        self.clear_news()
        response = requests.get("https://minecraft.komaweb.eu/modpacks/" + keys.lower() + "/news/news.json")
        if response.status_code == 200:
            data = response.json()
            print(data)


            """frame = customtkinter.CTkFrame(self.news_frame, bg_color="#FFFFFF", corner_radius=10)
            frame.pack(fill="x", padx=10, pady=10, ipadx=10, ipady=10)
            label = customtkinter.CTkLabel(frame, text=data["2023"]["name"], font=("Arial", 12), padx=10, pady=5)
            label.pack()
            label = customtkinter.CTkLabel(frame, text=data["2023"]["desc"], font=("Arial", 12), padx=10, pady=5)
            label.pack()"""

            with open("versions.json", "r") as file:
                versions = json.loads(file.read())

            for widget in self.button_frame.winfo_children():
                widget.destroy()

            self.button_open_website = customtkinter.CTkButton(self.button_frame, text="Webhely", fg_color="green",command=self.open_modpack_website)
            self.mods_button = customtkinter.CTkButton(self.button_frame, text="Modok", fg_color="green",command=self.open_mod_viewer)

            if "forge" in versions[self.selected_version]["version"]:
                # -after, -anchor, -before, -expand, -fill, -in, -ipadx, -ipady, -padx, -pady, or -side
                self.button_open_website.grid(row=0, column=0,padx=10,pady=10)
                self.mods_button.grid(row=0,column=1,padx=10,pady=10)
            else:
                self.button_open_website.grid(row=0, column=0,padx=10,pady=10)


            if versions[self.selected_version]["icon"] != "":
                response = requests.get(versions[self.selected_version]["icon"])
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    # Most már dolgozhat a képpel...
                else:
                    print("Nem sikerült letölteni a képet.")
                    image = Image.open("vanilla.png")
            else:
                image = Image.open("vanilla.png")

            image2 = image.copy()
            image2.convert("RGBA")
            alpha = 0.75
            alpha_int = int(alpha * 255)
            image2.putalpha(alpha=alpha_int)
            icon_image = customtkinter.CTkImage(light_image=image2, size=(400, 400))

            label = customtkinter.CTkLabel(self.news_frame,image=icon_image, text="", corner_radius=100)
            label.pack()

            if data.keys != "":
                self.news_frame2.configure(scrollbar_button_color="#000")

            for elem in data:

                frame2 = customtkinter.CTkFrame(self.news_frame2,fg_color="#FFF", corner_radius=10,width=600)
                frame2.pack(fill="x", padx=10, pady=10)
                label = customtkinter.CTkLabel(frame2, text=data[elem]["name"], font=("Arial", 16), text_color="#000", padx=10, pady=5)
                label.pack()
                label = customtkinter.CTkLabel(frame2, text=data[elem]["desc"], font=("Arial", 12), text_color="#000", padx=10, pady=5)
                label.pack()


        else:

            print("Nem létezik")

    def selected_version_menu(self):
        pass

    def start(self):

        #selected_version = self.version.get()

        selected_version = self.selected_version

        print(selected_version)

        with open("versions.json","r") as file:
            version_json = json.loads(file.read())

        gamedirector = version_json[selected_version]["gameDirector"]
        version = version_json[selected_version]["version"]

        print(mc.director2)

        print(gamedirector)

        login = minecraft_launcher_lib.utils.generate_test_options()
        if self.name.get('0.0',customtkinter.END).split("\n")[0] != "":
            login['username'] = self.name.get('0.0',customtkinter.END).split("\n")[0]
        login["executablePath"] = mc.json['JavaDir']
        login["jvmArguments"] = ["-Xmx"+mc.json['RAM'], "-Xms"+mc.json['RAM']]
        print(login)

        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(version, gamedirector, login)

        print(minecraft_command)

        subprocess.run(minecraft_command)

    def run(self):

        thread = threading.Thread(target=self.start,daemon=True)
        thread.start()

    def open_setting(self):
        new = Setting(self)
        new.grab_set()

    def open_download_modpack(self):
        new = ModpackDownload(self)
        new.grab_set()
    def open_forge_version(self):
        new = ForgeModpack(self)
        new.grab_set()

    def open_mod_viewer(self):
        new = ModsView(self)
        new.grab_set()

    def open_modpack_website(self):
        result = database.getTable("SELECT * FROM modpacks WHERE name = '"+self.selected_version+"'")
        url = "https://minecraft.komaweb.eu/modpack.php?id="+str(result[0][0])
        webbrowser.open_new_tab(url)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()