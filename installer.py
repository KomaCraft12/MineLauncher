import subprocess

import customtkinter
import threading
import json
import mysql.connector as mysql
import os, winshell
import uuid
import requests
import zipfile
import time
import pythoncom
import win32com.client

from win32com.client import Dispatch

class Database():

    def __init__(self):
        pass

    def connect(self):
        try:
            self.conn = mysql.connect(host="komacloud.synology.me",user="jano",password="Katica.bogar2002",database="mclauncher")
        except mysql.Error as err:
            print(err)
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

    def update(self):
        pass

database = Database()

class MainWindow(customtkinter.CTk):

    def __init__(self):
        super().__init__()
        self.title("MineCraft Telepítő")
        self.geometry("400x320")
        self.resizable(False, False)
        self.desktop_icon = customtkinter.StringVar(value="off")

        self.latest_version = database.getTable("SELECT * FROM updates ORDER BY id DESC LIMIT 1")
        print(self.latest_version)

        elem = customtkinter.CTkFrame(self,fg_color="#8B4513")
        title = customtkinter.CTkLabel(elem,text="Telepítő",font=("Arial",20))
        title.pack()

        path_title = customtkinter.CTkLabel(elem,text="Telepítés helye",font=("Arial",12))
        path_title.pack(side= customtkinter.TOP, anchor="w",padx=5,pady=10)

        self.path = customtkinter.CTkTextbox(elem,height=25,width=390)
        self.path.insert("0.0","C:/Games/mc-launcher/")
        self.path.pack()

        desktop_icon = customtkinter.CTkCheckBox(elem,text="Parancsikon elhelyezése az asztalra",variable=self.desktop_icon, onvalue="on", offvalue="off")
        desktop_icon.pack(side= customtkinter.TOP, anchor="w",padx=5,pady=10)

        install = customtkinter.CTkButton(elem,text="Telepítés", command=self.start)
        install.pack(padx=10,pady=10)

        elem.pack(side='top', fill="both", expand=True, in_=self)

        self.progressbar = customtkinter.CTkProgressBar(elem, orientation="horizontal",
                                                            progress_color="gray", fg_color="gray", height=25,
                                                            width=480, determinate_speed=0.01)
        self.progressbar.set(0)
        self.progressbar.pack(padx=5, pady=5)

        self.file = customtkinter.CTkLabel(elem, text="")
        self.file.pack(padx=5, pady=5)

        self.progress = customtkinter.CTkLabel(elem, text="")
        self.progress.pack(padx=5, pady=5)

    def start(self):

        print(self.path.get("0.0",customtkinter.END))

        thread = threading.Thread(target=self.installing)
        thread.start()

    def installing(self):

        self.progressbar.configure(progress_color="green")

        installing_path = self.path.get("0.0",customtkinter.END).replace("\n","")

        if not(os.path.exists(installing_path)):
            os.mkdir(installing_path)

        self.url = str(self.latest_version[0][2])
        self.files = str(self.latest_version[0][3])

        response = requests.get(self.url, stream=True)

        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0

        with open(installing_path + self.files, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if bytes_downloaded % (10240000) == 0:
                        self.download_progress(bytes_downloaded, total_size)

        self.bar_custom_unzip(installing_path + self.files, installing_path)
        self.register_client(installing_path)
        print(self.desktop_icon.get())
        if self.desktop_icon.get() == "on":
            self.create_shortcut(installing_path,"mc-client.exe", "MCLauncher")

        self.file.configure(text="")
        self.progress.configure(text=f'Sikeres telepítés!')

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
            #self.file.configure(text="")
            #self.progress.configure(text=f'Sikeres telepítés!')
            # print('\nExtraction complete.')

    def register_client(self,path):

        self.file.configure(text="Fájl: client.json")
        self.progress.configure(text=f'Beállítás: Kliens regisztrálása')

        time.sleep(2)

        self.json = {}
        self.json["client_id"] = str(uuid.uuid4())

        self.lastid = database.insert("INSERT INTO clients (`client_id`,`version`) VALUES (%(client_id)s, %(version)s)",{"client_id":self.json["client_id"],"version":1})
        self.json["id"] = self.lastid
        self.json["version"] = self.latest_version[0][1]

        with open(path+"client.json","w") as file:
            json.dump(self.json,file,indent=2)

    def create_shortcut(self,target_path, target_file, shortcut_name, shortcut_dir=None):

        self.file.configure(text="Fájl: "+shortcut_name+".lnk")
        self.progress.configure(text=f'Beállitás: Parancsikon létrehozása az asztalon')

        time.sleep(2)

        if not shortcut_dir:
            # If shortcut directory is not provided, use the desktop directory
            shortcut_dir = os.path.join(os.path.expanduser('~'), 'Desktop')

        # Initialize COM (optional, but recommended)
        pythoncom.CoInitialize()

        # Create a shell object
        shell = win32com.client.Dispatch("WScript.Shell")

        # Get the special folder for the desktop
        desktop = shell.SpecialFolders("Desktop")

        # Create a shortcut object
        shortcut = shell.CreateShortcut(os.path.join(shortcut_dir, f"{shortcut_name}.lnk"))

        # Set the target path
        shortcut.TargetPath = target_path+""+target_file

        # Set the working directory
        if target_path:
            shortcut.WorkingDirectory = target_path

        # Save the shortcut
        shortcut.Save()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()