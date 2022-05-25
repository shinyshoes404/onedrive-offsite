import json, requests, os, urllib.parse, datetime
from onedrive_offsite.config import Config
from onedrive_offsite.crypt import Crypt

def signin():
    app_json_path = Config.app_json_path
    app_oauth2_creds_path = Config.oauth2_json_path

    if os.path.isfile(app_json_path) == False:
        print("Missing app_info.json. Run 'onedrive-offsite-setup-app' from the terminal to create one.")
        return False
    
    with open(app_json_path, 'r') as app_file:
        app_json = json.load(app_file)

    signin_url = app_json.get("signin_url")
    client_id = app_json.get("client_id")
    client_secret = app_json.get("client_secret")
    redirect_uri = app_json.get("redirect_uri")
    grant_type = "authorization_code"



    print("-------- Microsoft OAuth Sign in URL -----------")
    print(signin_url)
    print("------------------------------------------------\n")
    print("Copy and paste the URL above into your browser. Sign in to your Microsoft account and accept the requested access permissions.")
    print("Afterward, you will be redirected to http://localhost:8080?code=<a big long code from microsoft>. Copy everything after ?code= and paste it into the prompt below.")
    print("If there is a pound sign '#' at the end of the code, do not include it.\n")

    code = input("Paste the code here: ")

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"client_id": client_id, "redirect_uri": redirect_uri, "client_secret": client_secret, "code": code, "grant_type": grant_type}

    token_url = Config.token_url + "/consumers/oauth2/v2.0/token"

    token_response = requests.post(url=token_url, data=data, headers=headers, timeout=Config.api_timeout)

    if token_response.status_code == 200:
        token_json = token_response.json()
        token_data = {}
        token_data["access_token"] = token_json.get("access_token")
        token_data["refresh_token"] = token_json.get("refresh_token")
        expires = (datetime.datetime.now() + datetime.timedelta(seconds=token_json.get("expires_in"))).strftime('%Y-%m-%d %H:%M:%S')
        token_data["expires"] = expires
        with open(app_oauth2_creds_path, "w") as json_file:
            json.dump(token_data, json_file)
        
        print("Sign in successful. Token retreived.")
        app_root_url = "https://graph.microsoft.com/v1.0/me/drive/special/approot/children"
        app_root_header = {'Content-type': 'application/json'}
        app_root_header['Authorization'] = "Bearer " + token_json.get("access_token")
        app_root_resp = requests.get(url=app_root_url, headers=app_root_header, timeout=Config.api_timeout)
        if app_root_resp.status_code == 200:
            print("App root directory created successfully")
            return True
        else:
            print("Problem creating app root. You may not be able to upload files.")
            return False

    else:
        print("There was a problem retrieving the tokens.")

        return False

def app_info_setup():
    app_json_path = Config.app_json_path
    print("\n--- onedrive-offsite app info setup ---")
    print("This script will build your app_info.json file as you provide the needed information. Before you start, you will need to register an application at https://portal.azure.com to create the items required for the app_info.json file.\n\nPress enter to continue. Type 'exit' at any time to exit this script.")
    exit_flag = input()
    if exit_flag == "exit":
        return False
    
    client_id = input("\nPlease provide your client ID: ")
    if client_id == "exit":
        print("exiting")
        return False

    client_secret = input("Please provide your client secret: ")
    if client_secret == "exit":
        print("exiting")
        return False

    redirect_uri = input("Please provide an Oauth2 redirect URI. Press enter for default 'http://localhost:8080': ") or "http://localhost:8080"
    if redirect_uri == "exit":
        print("exiting")
        return False

    scopes = input("Please provide your desired scopes. Press enter for defaults of 'files.readwrite.appfolder offline_access user.read user.readbasic.all': ") or "files.readwrite.appfolder offline_access user.read user.readbasic.all"
    if scopes == "exit":
        print("exiting")
        return False

    signin_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?client_id=" + client_id + "&scope=" + scopes + "&response_type=code&redirect_uri=" + urllib.parse.quote(redirect_uri, safe='')


    app_info_json = {}
    app_info_json["client_id"] = client_id
    app_info_json["client_secret"] = client_secret
    app_info_json["redirect_uri"] = redirect_uri
    app_info_json["signin_url"] = signin_url

    try:
        with open(app_json_path, "w") as json_file:
            json.dump(app_info_json, json_file)
        print("\nThe app_info.json file has been created.")
        print("\nNow, run 'onedrive-offsite-signin' from the terminal to grant this application access to Onedrive via Oauth2.")
        return True
    except:
        print("\nThere was a problem creating the app_info.json file.")
        return False

def create_key():
    print("--- onedrive-offsite create key ---")
    print("This will create a new key for encrypting and decrypting backup files.")
    if os.path.isfile(Config.key_path) == True:
        print("A key file already exists. Continuing will create a new one. Do you want to proceed?  Y/N")
        proceed = input() or "N"
        if proceed == "N" or proceed == "n" or (proceed != "Y" and proceed != "y"):
            print("Exiting. No key created")
            return False
        else:
            datetime_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            with open(Config.key_path, "rb") as key_file_orig:
                key_contents = key_file_orig.read()
            
            with open(os.path.join(Config.etc_basedir, Config.key_name + "_" + datetime_str + Config.key_extension), "wb") as key_file_archive:
                key_file_archive.write(key_contents)
            
            print("A copy of the old key has been saved as: " + Config.key_name + "_" + datetime_str + Config.key_extension)
    
    crypt = Crypt(Config.key_path)
    if crypt.gen_key_file() == True:
        print("New key created.")
        return True
    else:
        print("key creation failed")
        return False
