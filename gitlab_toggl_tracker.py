#!/usr/bin/python3
import gitlab #Technically not necessary, but I'm too lazy to write my own python gitlab rest api
import requests
import json
import atexit #Functionality on Exit handling

#TODO better handling of definition to be more modular
gitlab_data = {"gitlab_url":"", "gitlab_token":"", "project_id":"", "issue_id":""}
toggl_data = {"toggl_token":"", "workspace_id":"", "project_id":""}

#TODO more flexibility for user to decide whether to use config or selfmade stuff
try:
    config_file = open("./config.json", "r")
    config_json = json.loads(config_file.read())
    config_file.close()
    print("config.json detected!")
except:
    print("There is no config.json file. Please enter following data:")
    for gl_key in gitlab_data:
        gitlab_data[gl_key] = input("Enter " + gl_key + ": ")
    for tgl_key in toggl_data:
        toggl_data[tgl_key] = input("Enter " + tgl_key + ": ")
    f = open("./config.json", "w+") #+ stands for if file doesn't exist, create a new one
    json_text = json.dumps({"gitlab_data":gitlab_data, "toggl_data":toggl_data}, indent=4)
    f.write(json_text)
    config_json = json.loads(json_text)
    f.close()
    print("config.json created!")

#GITLAB DATA, needs to be less specific
project_name = "This is my Project"
project_id = int(config_json["gitlab_data"]["project_id"])
issue_id = int(config_json["gitlab_data"]["issue_id"])
git_token = config_json["gitlab_data"]["gitlab_token"]
git_url = config_json["gitlab_data"]["gitlab_url"]
# private token or personal token authentication
gl = gitlab.Gitlab(git_url, private_token=git_token)
gl.auth() #TODO: Handling of auth errors
gitlab_project = gl.projects.get(project_id)
gitlab_issue = gitlab_project.issues.get(issue_id)

#TOGGL DATA
toggl_token= config_json["toggl_data"]["toggl_token"]
workspace_id= config_json["toggl_data"]["workspace_id"]
t_project_id= int(config_json["toggl_data"]["project_id"])
headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}

#TODO For more ease of use, user shall only input the project name, and the fetching of ID will be done internally
#TODO there is no handing of wrong tokens/ids yet
#TODO there is no handling of missing config types in the json (as in there is no checking whether the config.json is in correct format)


#Tracks time. Format is seconds
def gitlab_track_time( time ):
    gitlab_issue.add_spent_time(str(time) + "s")
    return

def toggl_start_tracking(desc, tags, pid):
    id = check_currently_running()
    if(id == -1):
        data_struct = {"time_entry":{"created_with":"Raka_Script"}}
        data_struct["time_entry"]["description"] = str(desc)
        data_struct["time_entry"]["tags"] = tags
        if(int(pid) >= 0):
            data_struct["time_entry"]["pid"] = str(pid)
        data = json.dumps(data_struct)
        response = requests.post('https://www.toggl.com/api/v8/time_entries/start', headers=headers, data=data, auth=(toggl_token, 'api_token'))
        print("You're starting time-tracking \r\n")
        print(response.text)
    else:
        print("You're currently time-tracking")

def toggl_stop_tracking():
    id = check_currently_running()
    if(id != -1):
        response = requests.put('https://www.toggl.com/api/v8/time_entries/' + str(id) + '/stop', headers=headers, auth=(toggl_token, 'api_token'))
        print("You're terminating the time-tracking \r\n")
        print(json.loads(response.text)['data']['duration']) #TODO better start message
        gitlab_track_time(json.loads(response.text)['data']['duration'])
    else:
        print("You're not currently time-tracking")

#If something is currently running, then return the id, otherwise return -1
def check_currently_running():
    response = requests.get('https://www.toggl.com/api/v8/time_entries/current', headers=headers, auth=(toggl_token, 'api_token'))
    if(json.loads(response.text)['data'] == None):
        return -1
    else:
        return json.loads(response.text)['data']['id']

print("Tracking will start now...")
track_title = input("Enter toggl title for tracked time (leave this empty for Format: '[Gitlab Project] - [Gitlab Issue]'): ")
if(track_title == ""):
    track_title = gitlab_project.attributes["name"] + " - " + gitlab_issue.attributes["title"]
print("Enter the toggl tags (empty input will break the loop): ")
track_tags = []
while(True):
    tag_input = input("> ")
    if(tag_input != ""):
        track_tags.append(tag_input)
    else:
        break

toggl_start_tracking(track_title, track_tags, t_project_id)

atexit.register(toggl_stop_tracking)

while(True):
    pass
