from huggingface_hub import InferenceClient
from flask import Flask, request, render_template, url_for, session
import google.generativeai as genai
import random
import string

app= Flask(__name__)
app.secret_key = 'as5efA2y' 

def generate_random_string():
    characters = string.ascii_letters + string.digits  
    random_string = ''.join(random.choices(characters, k=5)) 
    return random_string


def generate_list(path):
    GOOGLE_API_KEY = "AIzaSyDPAMOiVR0A_hAchpAGG5hcctKrvyO2Ymk"
    genai.configure(api_key=GOOGLE_API_KEY)
    image_api=genai.upload_file(path) 
    image_generation_llm_prompt=""
    llm_prompt=f"Identity the objects in the image and just give the list of items. Be specific with the material of the objects.No sentences"
    model = genai.GenerativeModel("gemini-1.5-pro")
    result = model.generate_content([llm_prompt,image_api])
    print("items detected",result.text)
    list_of_items=result.text 
    return list_of_items

def generate_steps(path,items):
    GOOGLE_API_KEY = "AIzaSyBBuIZMq3pec8KZ1oNTtXtPNfh9r-I4vME"
    genai.configure(api_key=GOOGLE_API_KEY)
    image_api=genai.upload_file(path) 

    llm_prompt=f"give steps to Generate the product given in image using these items: {items} "

    
    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content([llm_prompt,image_api])
    return result.text    

@app.route("/",methods=['GET'])
def home_page():
    session['count']=0  
    return render_template('index.html')


@app.route("/generate_image",methods=['POST'])
def image_generation():
    print("checkpoint 1")       
    
    #Generating items in the uploaded image
    input_image_file=request.files['uploaded_image']
    input_image_path="./input_images/"+input_image_file.filename
    input_image_file.save(input_image_path)
    items=generate_list(input_image_path)

    #Generating image based on the usage and the list of items
    client = InferenceClient("black-forest-labs/FLUX.1-dev", token="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")
    usage=request.form['usage']
    image_generation_prompt=f"Generate image using {items} for {usage}"
    generated_image = client.text_to_image(image_generation_prompt)
    img_id=generate_random_string()
    generated_image_path="C:\\Users\\Ganesh\\Desktop\\Thales Hackathon\\flask app\\static\\generated_image\\"+img_id+".jpg"
    generated_image.save(generated_image_path)

    #Generate steps for the image generated
    steps=generate_steps(generated_image_path,items)   

    final_path=url_for('static', filename=f"generated_image/{img_id}.jpg")
    

    return render_template('result.html',img_path=final_path,final_steps=steps)


if __name__== "__main__":       
    app.run(app.run(host="0.0.0.0", port=5000),debug=True)
