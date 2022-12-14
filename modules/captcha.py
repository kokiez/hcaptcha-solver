import json, time, httpx, cv2, os, json, base64
import tensorflow as tf
from keras.models import load_model
tf.debugging.disable_traceback_filtering()
import numpy as np
from . import hcaptcha

from .console import Console
from .utf_decoder import unicode_Coversion
import requests

from modules.ai_finder.solutions import  resnet, yolo
from pathlib import Path


path_objects_yaml = './modules/ai_finder/objects.yaml'

dir_model = './data/model'
label_alias = {}

# Automatic registration
pom_handler = resnet.PluggableONNXModels(path_objects_yaml)
#Update labelalias list
label_alias.update(pom_handler.label_alias['en'])
on_rainbow = True
pluggable_onnx_models = pom_handler.overload(dir_model, on_rainbow)

class CaptchaSolver:
    def switch_solution(label):
        global pluggable_onnx_models
        global yolo_model
        global label_alias 
        label_alias1 = label_alias.get(label)
        
        # Select ONNX model - ResNet | YOLO
        if pluggable_onnx_models.get(label_alias1):
            return pluggable_onnx_models[label_alias1]
        return "n"

    def challenge(model, alias, label):
            global pluggable_onnx_models
            global yolo_model
            global label_alias 
            count = 0

            # {{< IMAGE CLASSIFICATION >}}
            result = None
            result = model.solution(img_stream=alias, label=label_alias[label])

            return result
            
    @staticmethod
    def get_captcha_by_ai(siteky, host ,proxy: str):
        
        if "http://" not in host:
            host = "http://"+host
        
        Console.debug("[*] SOLVING...")
        ch = hcaptcha.Challenge(
            sitekey=siteky,
            page_url=host,
            http_proxy=proxy
        )

        if ch.token:
            return ch.token
        label = ""
        if ch.question:
            Console.debug("[*] Question: "+ch.question)
            question = ch.question
            if "Please click each image containing an" in question:
                question = question.replace("Please click each image containing an ","")
            elif "Please click each image containing a" in question:
                question = question.replace("Please click each image containing a ","")
            else:
                question = question.replace("Please click each image containing","")
            label = question.replace(".","")

        #Converting unicode letters in label to Latin/Normal Alphabets
        for alphabet in label:
            if "\\" in str(alphabet.encode('utf-8')):
                convertedALphabet = unicode_Coversion(alphabet.encode('utf-8'))
                label = label.replace(alphabet,convertedALphabet)

        Console.debug("[*] Modified Label: "+label)

        answers = []
        count = 0
        for tile in ch.tasks:

            ### Downlowds hcaptcha images, wrote the code for testing the new models.            
            url = tile.url
            alias = requests.get(url).content                  
            count +=1

            solution = CaptchaSolver.switch_solution(label)
            if solution != "n":
                result = CaptchaSolver.challenge(solution,alias, label)
                if result != None:                
                #True means correct, false means wrong image
                    Console.debug(f"[+] Image Number: {count}, Result: {result}")
            else:
                Console.info(f"[+] AI not trained for this captcha type yet !\nRun the Download_Update.bat to check for updates")
                break
            if result == True:
                answers.append(tile)
        try:
            Console.debug(f"[+] Solving Captcha by Choosing Images Now.")
            token = ch.solve(answers)
            return token
        except hcaptcha.ApiError as e:
            #This is where the captcha fails. means its solved but wrong images are chosen
            Console.debug(f"[-] Captcha solved but wrong, Retrying...")
