import requests
from copy import deepcopy
import os
import json
import urllib

#llama.cpp-server-api-ip
api_url = "http://127.0.0.1:8081"

_do_sample = True
_temperature = 1

prompt_secondary_core_opinion = [
    {"role": "system", "content": "{name}'s persona: {persona}\n{name} is not a central core.\n{name} is a secondary core to the central core\nCentral core's conversation with USER: {dialog}"},
    {"role": "user", "content": " After the above conversation, USER said \"{input}\".\nAs a secondary core to the central core, what is an appropriate opinion for {name} to make to the central core?\nBe sure to note the persona of {name}. Just show only {name}'s opinion."}
]

prompt_central_core_conclusion = [
    {"role": "system", "content": "{name}'s persona: {persona}\n{name} is a central core.\nCentral core's conversation with USER: {dialog}"},
    {"role": "user", "content": "After the above conversation, USER said \"{input}\".\nHere's what the secondary core's opinion about USER's saying:{secondaryCores}\nAs a central core, What is the appropriate words for {name} to say to the USER with opinion from the secondary cores?\nBe sure to note the persona of {name} and opinion of secondary cores. Keep it to three sentences or less. Just show only {name}'s words to USER."}
]


def process_prompt(inform):
    if (inform["type"] == "secondary_core"):
        prompt_log = deepcopy(prompt_secondary_core_opinion)
        prompt_log[0]["content"] = prompt_log[0]["content"].replace("{name}", inform["name"]).replace("{persona}", inform["persona"]).replace("{dialog}", inform["dialog"])
        prompt_log[1]["content"] = prompt_log[1]["content"].replace("{input}", inform["input"]).replace("{name}", inform["name"])
    
    elif (inform["type"] == "central_core"):
        prompt_log = deepcopy(prompt_central_core_conclusion)
        prompt_log[0]["content"] = prompt_log[0]["content"].replace("{name}", inform["name"]).replace("{persona}", inform["persona"]).replace("{dialog}", inform["dialog"])
        prompt_log[1]["content"] = prompt_log[1]["content"].replace("{input}", inform["input"]).replace("{secondaryCores}", inform["secondaryCores"]).replace("{name}", inform["name"])
    
    prompt = "<|begin_of_text|>"
    for i, line in enumerate(prompt_log):
        prompt += "<|start_header_id|>"
        if (line["role"] == "user"):
            prompt += "user"
        elif (line["role"] == "system"):
            prompt += "system"
        elif (line["role"] == "assistant"):
            prompt += "assistant"
        prompt += "<|end_header_id|>\n\n"
        prompt += line['content'] + "<|eot_id|>"

    prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n\""
    return prompt


def gen_request(inform):
    global _do_sample, _temperature
    prompt = process_prompt(inform)
    # print(prompt)
    if (prompt == None):
        return ""
    postData = {
        "temperature": _temperature,
        "do_sample": _do_sample,
        "n_keep": -1,
        "stop": ["</s>"],
        "prompt": prompt
    }
    
    data = requests.request("POST", urllib.parse.urljoin(api_url, "/completion"), data=json.dumps(postData)).json()
    # data = {"content": ""}
    return data["content"].replace("</s>", "").strip().strip("\"")


class Personality_Core_Conversation:
    def __init__(self):
        self.log = []
        self.cores = []

        print("Core loading...", end='')
        self.cores = self.load_cores()
        print("complete.")
        # print(self.cores)
    
    def load_cores(self):
        dir = "personalityCores"
        files = os.listdir(dir)
        cores = []
        for filename in files:
            if os.path.isdir(filename) == True:
                continue
            name, ext = os.path.splitext(filename)
            if (ext[1:] != "json"):
                continue
            with open(os.path.join(dir, filename), "r") as f:
                core = json.load(f)
            cores.append(core)
        return cores
    
    def get_dialog(self):
        dialog = ""
        for i, line in enumerate(self.log):
            if (line["role"] == "User"):
                dialog += "\n" + f"USER: {line['content']}"
            elif (line["role"] == "Central Core"):
                dialog += "\n" + f"Central Core: {line['content']}"
            else:
                dialog += "\n" + f"{line['role']}'s opinion: {line['content']}"
        return dialog

    
    def chat_progress(self, user_input):
        secondary_cores_opinion = ""
        dialog = self.get_dialog()
        temp = 0
        self.log.append({"role": "User", "content": user_input})
        for i, core in enumerate(self.cores):
            if (core["central_core"]):
                temp = i
                continue
            opinion = gen_request({"type": "secondary_core", "input": user_input, "name": core["name"], "persona": core["persona"], "dialog": dialog})
            secondary_cores_opinion += "\n" + f"{core['name']}'s opinion: {opinion}"
            # print(core["name"], ":", opinion)
            self.log.append({"role": core["name"], "content": opinion})
        
        saying = gen_request({"type": "central_core", "input": user_input, "name": self.cores[temp]["name"], "persona": self.cores[temp]["persona"], "dialog": dialog, "secondaryCores": secondary_cores_opinion})
        self.log.append({"role": "Central core", "content": saying})

        return self.log