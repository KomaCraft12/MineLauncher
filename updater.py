import subprocess
import time

import customtkinter
import threading
import json
import mysql.connector as mysql
import os
import uuid
import requests
import zipfile

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

class MainWindow(customtkinter.CTk):

    def __init__(self):
        super().__init__()
        self.title("MineCraft UPDATER")
        self.geometry("400x200")
        self.resizable(False, False)

        self.latest_version = database.getTable("SELECT * FROM updates ORDER BY id DESC LIMIT 1")
        print(self.latest_version)

        if os.path.exists("client.json"):
            with open("client.json","r") as file:
                self.json = json.loads(file.read())
            if self.json['id'] == "" or self.json['id'] == 0:

                try:
                    uuid.UUID(self.json["client_id"], version=4)
                except ValueError:
                    self.json["client_id"] = str(uuid.uuid4())

                self.lastid = database.insert(
                    "INSERT INTO clients (`client_id`,`version`) VALUES (%(client_id)s, %(version)s)",
                    {"client_id": self.json["client_id"], "version": self.latest_version[0][1]})
                self.json["id"] = self.lastid
                self.json["version"] = self.latest_version[0][1]

        else:

            self.json = {}
            self.json["client_id"] = str(uuid.uuid4())

            self.lastid = database.insert("INSERT INTO clients (`client_id`,`version`) VALUES (%(client_id)s, %(version)s)",{"client_id":self.json["client_id"],"version":self.latest_version[0][1]})
            self.json["id"] = self.lastid
            self.json["version"] = self.latest_version[0][1]

        with open("client.json","w") as file:
            json.dump(self.json,file,indent=2)

        elem = customtkinter.CTkFrame(self,fg_color="#8B4513")
        title = customtkinter.CTkLabel(elem,text="Frissítő",font=("Arial",20))
        title.pack()

        action = customtkinter.CTkLabel(elem,text="Frissítések keresése...")
        action.pack(side="top", fill="x", expand=True)

        elem.pack(side='top', fill="both", expand=True, in_=self)

        if self.json["version"] != self.latest_version[0][1]:

            action.configure(text="Új verzió elérhető: "+str(self.latest_version[0][1]))

            self.progressbar = customtkinter.CTkProgressBar(elem, orientation="horizontal",
                                                            progress_color="gray", fg_color="gray", height=25,
                                                            width=480, determinate_speed=0.01)
            self.progressbar.set(0)
            self.progressbar.pack(padx=5, pady=5)

            self.file = customtkinter.CTkLabel(elem, text="")
            self.file.pack(padx=5, pady=5)

            self.progress = customtkinter.CTkLabel(elem, text="")
            self.progress.pack(padx=5, pady=5)

            thread = threading.Thread(target=self.update)
            thread.start()

        else:
            action.configure(text="A laucher naprakész!")
            time.sleep(3)
            thread = threading.Thread(target=self.open_launcher)
            thread.start()

    def save_update(self):
        id = self.json["id"]
        client_id = self.json["client_id"]
        version = self.latest_version[0][1]
        database.update(
            "UPDATE clients SET version = %(version)s WHERE id = %(id) AND client_id = %(client_id)",
            {'version':version,'id':id,'client_id':client_id}
        )

    def update(self):

        self.progressbar.configure(progress_color="green")

        self.url = str(self.latest_version[0][2])
        self.files = str(self.latest_version[0][3])

        response = requests.get(self.url, stream=True)

        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0

        with open("temp/" + self.files, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if bytes_downloaded % (10240000) == 0:
                        self.download_progress(bytes_downloaded, total_size)

        self.bar_custom_unzip("temp/" + self.files, os.getcwd())
        self.update_client()


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

    def update_client(self):

        with open("client.json", "r") as file:
            self.json = json.loads(file.read())

        self.json['version'] = float(self.latest_version[0][1])

        with open("client.json","w") as file:
            json.dump(self.json,file,indent=2)

        thread = threading.Thread(target=self.open_launcher)
        thread.start()

    def open_launcher(self):
        try:
            subprocess.Popen("mc-client.exe")
        except Exception:
            pass

        self.destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()