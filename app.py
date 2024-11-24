from huggingface_hub import InferenceClient
from flask import Flask, request, render_template, url_for, session, jsonify
import google.generativeai as genai
import random
import string
import json
import time
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet

app= Flask(__name__)
app.secret_key = 'as5efA2y' 

def generate_random_string():
    characters = string.ascii_letters + string.digits  
    random_string = ''.join(random.choices(characters, k=5)) 
    return random_string

def clean_html_content(html_content):
    import re

    # Remove backticks
    html_content = re.sub(r"`{3,}", "", html_content)  # Remove triple backticks (```)

    # Remove unnecessary tags if they exist
    html_content = re.sub(r"<!DOCTYPE html>|<html.*?>|</html>|<head.*?>.*?</head>|<body>|</body>", "", html_content, flags=re.DOTALL)

    # Strip leading and trailing whitespaces or newlines
    cleaned_content = html_content.strip()

    return cleaned_content

def generate_pdf(image_path, contents):

    filtered_data = dict(list(contents.items())[:-4])    

    img_id=contents['Image id']
    generate_pdf_path="C:\\Users\\Ganesh\\Desktop\\Thales Hackathon\\flask app\\static\\pdfs\\"+img_id+".pdf"

    doc = SimpleDocTemplate(generate_pdf_path, pagesize=letter)

    story = []

    story.append(Image(image_path, width=300, height=300))
    styles = getSampleStyleSheet()

    for key, value in filtered_data.items():
        text = f"<b>{key}:</b> {value}"
        story.append(Paragraph(text, styles["Normal"]))

    pdf_path=url_for('static', filename=f"pdfs/{img_id}.pdf")
    doc.build(story)
    print("PDF Generated")
    return pdf_path


def generate_list(path,usage):
    # GOOGLE_API_KEY = "AIzaSyDPAMOiVR0A_hAchpAGG5hcctKrvyO2Ymk" exhausted 
    GOOGLE_API_KEY = "AIzaSyCPLt6MNgpmvVRAnNSPl-dIeWt_99Tcsus"
    genai.configure(api_key=GOOGLE_API_KEY)
    image_api=genai.upload_file(path) 
    # image_generation_llm_prompt=""
    # llm_prompt=f"Two tasks for you: 
    # Task1 : Identity the objects in the image and give the list of items.Be specific with the material of the objects.No sentences
    # Task2 : Give creative idea on how to use the items in the image for use in {usage}(give image generation prompt which i can give
    # it to a image generation model) give json like thing so that i can split those 2 tasks PS: keep in mind these domains: Defence and Security, Aeronatics and SPace, Cybersecurity and DIgital Identity"

    llm_prompt = f"""
Task 1: Identify all objects in the image and provide a list of items with their materials. Use a simple list format like: "plastic bag, newspaper, wooden chair". No sentences.
Task 2: Suggest a creative idea for using the identified items for {usage}. Provide this as an image-generation prompt(very concise prompt no greater than 15 words).
Output format:
{{
    "items_list": ["plastic bag", "newspaper", "wooden chair", ...],
    "image_prompt": "image generation prompt"
}}
"""
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    result = model.generate_content([llm_prompt,image_api])
    print(result.text)
    llm_text=result.text
    stripped=llm_text[7:-3].strip()
    print(stripped)
    parsed_output=json.loads(stripped)
    list_of_items=parsed_output["items_list"]
    image_generation_llm_prompt=parsed_output["image_prompt"]
    print(list_of_items,image_generation_llm_prompt)

    return list_of_items,image_generation_llm_prompt

def generate_steps(path,items):
    # GOOGLE_API_KEY = "AIzaSyBBuIZMq3pec8KZ1oNTtXtPNfh9r-I4vME" exhausted
    GOOGLE_API_KEY = "AIzaSyCy4v_Yc_3xprx-QqJ9YumPiCYEFA_i9p0"
    genai.configure(api_key=GOOGLE_API_KEY)
    image_api=genai.upload_file(path) 

    llm_prompt=f"give steps to Generate the product given in image using these items: {items}. keep in mind, theme is upcycling waste items. just give html fragments not single text, use bold list and other relevant tags wherever necessary no extra text just html fragments, no body, head, doctype tags"

    
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
    start_time=time.time() 

    usage=request.form['usage']     
    
    #Generating items in the uploaded image
    list_generation_time=time.time()
    input_image_file=request.files['uploaded_image']
    input_image_path="./input_images/"+input_image_file.filename
    input_image_file.save(input_image_path)
    items,image_generation_prompt=generate_list(input_image_path,usage)
    list_generation_time=time.time()-list_generation_time
    
    #Generating image based on the usage and the list of items
    image_generation_time=time.time()
    client = InferenceClient("black-forest-labs/FLUX.1-dev", token="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")  

    # image_generation_prompt=f"Generate image using {items} for {usage}"
    generated_image = client.text_to_image(image_generation_prompt)
    image_generation_time=time.time()-image_generation_time
    img_id=generate_random_string()
    generated_image_path="C:\\Users\\Ganesh\\Desktop\\Thales Hackathon\\flask app\\static\\generated_image\\"+img_id+".jpg"
    generated_image.save(generated_image_path)

    #Generate steps for the image generated
    steps_generation_time=time.time()
    steps=generate_steps(generated_image_path,items) 
    steps_generation_time=time.time()-steps_generation_time  

    final_path=url_for('static', filename=f"generated_image/{img_id}.jpg")
    
    total_time=time.time()-start_time
    print("List and image prompt generation time",list_generation_time)
    print("image generation time taken",image_generation_time)
    print("Steps generation time taken",steps_generation_time)
    print("total time taken:",total_time)

    file_path = f"prompts&content/{img_id}.json"
    data = {
    'Image id': img_id,
    'Objects identified': items,
    'Image Generation Prompt': image_generation_prompt,
    'Steps': steps,
    'List and image prompt generation time': list_generation_time,
    'Image generation time taken': image_generation_time,
    'Steps generation time taken': steps_generation_time,
    'Total time taken': total_time
    }
    with open(file_path,'w') as file:
        json.dump(data, file, indent=4)

    pdf_path= generate_pdf(generated_image_path,data)

    # html_frags=clean_html_content(steps)
    html_frags=steps

    return render_template('result.html',img_path=final_path,final_steps=html_frags,download_pdf=pdf_path)


if __name__== "__main__":       
    app.run(host="0.0.0.0", port=5000,debug=True)
