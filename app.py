import os
import json
from flask import Flask, request, render_template, redirect, url_for, jsonify
from werkzeug.utils import secure_filename 
import requests 
from datetime import datetime

# --- 新增 Gemini 相關模組 ---
from google import genai
from google.genai.errors import APIError
# -----------------------------

app = Flask(__name__)
# 建議在 Render 部署時設定 FLASK_SECRET_KEY 環境變數
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key_for_dev') 

# --- 配置區 ---
UPLOAD_FOLDER = 'static/uploads' 
DATA_FILE = 'pets.json' 
MESSAGES_FILE = 'messages.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

if not os.path.exists(MESSAGES_FILE):
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        # 結構: { "posts": [], "messages": [] }
        json.dump({"posts": [], "messages": []}, f, ensure_ascii=False, indent=4) 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

# ----------------------------------------------------
# 輔助函數 (JSON & 檔案處理)
# ----------------------------------------------------

def geocode_address(address):
    # 保持地理編碼函數不變
    if not address:
        return None, None
        
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'tw'
    }
    headers = {'User-Agent': 'PetSocialMapDemo'} 
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
        return None, None
    except Exception as e:
        print(f"Geocoding error for {address}: {e}")
        return None, None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_pets():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_pets(pets):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(pets, f, ensure_ascii=False, indent=4)

def load_messages():
    try:
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"posts": [], "messages": []}

def save_messages(data):
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_pet_post_by_id(post_id):
    messages_data = load_messages()
    try:
        target_id = int(post_id)
    except ValueError:
        return None
    for post in messages_data["posts"]:
        if int(post.get('id', 0)) == target_id:
            return post
    return None

# ----------------------------------------------------
# Gemini AI 配置區 (已移除全域 Client)
# ----------------------------------------------------
# ⭐ 移除硬編碼金鑰和全域 client 初始化！
MODEL_NAME = "gemini-2.5-flash"
PET_CONTEXT = """
您是寵物社交地圖『毛孩交友天地』的 AI 智慧助手，請以友善、簡潔且中文繁體回答。
請鼓勵用戶多使用地圖和社交卡片進行探索。
"""
# ----------------------------------------------------


# ----------------------------------------------------
# 路由區
# ----------------------------------------------------

# 1. 主頁面/地圖頁面
@app.route('/')
@app.route('/index.html')
@app.route('/show_main_map')
def show_main_map():
    """主地圖與社交頁面，讀取 pets.json 資料"""
    pets_data = load_pets()
        
    return render_template('index.html', pets=pets_data)

# 2. 上傳頁面
@app.route('/upload.html')
@app.route('/show_upload_form')
def show_upload_form():
    """顯示上傳表單頁面"""
    return render_template('upload.html')

# 3. 處理表單提交
@app.route('/upload', methods=['POST'])
def handle_upload():
    """處理毛孩資料和圖片上傳，並儲存到 pets.json"""
    
    # ... (上傳邏輯保持不變)
    if 'petImage' not in request.files or request.files['petImage'].filename == '':
        return "請上傳毛孩照片", 400

    pet_image_file = request.files['petImage']
    if not allowed_file(pet_image_file.filename):
        return "不允許的毛孩照片格式", 400
        
    pet_image_filename = secure_filename(pet_image_file.filename)
    pet_image_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pet_image_filename)
    pet_image_file.save(pet_image_file_path)

    medical_records_urls = []
    if 'medicalRecord' in request.files:
        medical_files = request.files.getlist('medicalRecord')
        for file in medical_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                medical_records_urls.append({
                    "filename": filename,
                    "url": url_for('static', filename=f'uploads/{filename}')
                })
    
    pet_location = request.form.get('location')
    lat_str = request.form.get('lat')
    lon_str = request.form.get('lon')
    
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except (TypeError, ValueError):
        return "錯誤：未能獲取準確的地理座標 (請在地圖上點擊標記)。", 400
    
    tags = request.form.getlist('tags')
    other_tags_text = request.form.get('otherTagsText')
    
    if 'other' in tags and other_tags_text:
        tags.remove('other') 
        manual_tags = [t.strip() for t in other_tags_text.split(',') if t.strip()]
        tags.extend(manual_tags)
    
    pets = load_pets()
    new_id = (max([p.get('id', 0) for p in pets]) + 1) if pets else 1
    
    pet_data = {
        "id": new_id, 
        "name": request.form.get('petName'),
        "species": request.form.get('petSpecies'),
        "age": request.form.get('petAge'),
        "location": pet_location, 
        "interactionNote": request.form.get('interactionNote'),
        "healthNote": request.form.get('healthNote'), 
        "medicalRecords": medical_records_urls,       
        "image_url": url_for('static', filename=f'uploads/{pet_image_filename}'), 
        "tags": tags, 
        "lat": lat, 
        "lon": lon  
    }

    pets.append(pet_data)
    save_pets(pets)

    return render_template('success_page.html', pet_name=pet_data['name'], pet_id=pet_data['id'], image_url=pet_data['image_url'])


# ⭐ 4. 處理 Gemini AI 聊天請求 (使用使用者提供的金鑰) ⭐
@app.route('/ai_chat', methods=['POST'])
def ai_chat():
    """處理前端發送的 AI 聊天請求，使用使用者提供的 API Key"""
    data = request.json
    user_query = data.get('query')
    user_api_key = data.get('api_key') # 獲取使用者傳入的金鑰
    
    if not user_api_key:
         return jsonify({"response": "🤖 錯誤：請先在輸入框中提供您的 Gemini API Key。"}, 400)
    if not user_query:
        return jsonify({"response": "請輸入您的問題。"}, 400)
        
    try:
        # 每次請求都使用使用者金鑰來初始化 Client
        local_client = genai.Client(api_key=user_api_key)
        
        response = local_client.models.generate_content(
            model=MODEL_NAME, # 使用全域定義的模型名稱
            contents=[user_query],
            config=genai.types.GenerateContentConfig(
                system_instruction=PET_CONTEXT 
            )
        )
        return jsonify({"response": response.text})

    except APIError as e:
        # 針對 API 錯誤 (例如金鑰無效、權限不足) 給出更明確的提示
        error_message = f"🤖 API 錯誤：請檢查您輸入的 API Key 是否有效。錯誤詳情：{e}"
        print(f"API Error with User Key: {error_message}")
        return jsonify({"response": error_message}, 500)
        
    except Exception as e:
        # 處理其他未知錯誤
        print(f"Unknown Error in AI chat: {e}")
        return jsonify({"response": "🤖 發生未知錯誤，請檢查您的網路連線或 API Key。"}, 500)


# 5. 動態寵物數位護照頁面
@app.route('/passport/<int:pet_id>')
def show_pet_passport(pet_id):
    """根據 URL 中的 pet_id 顯示特定的寵物護照，並提供前後導航 ID"""
    pets = load_pets()
    
    current_pet = None
    pet_index = -1
    
    for i, pet in enumerate(pets):
        if int(pet.get('id', 0)) == pet_id:
            current_pet = pet
            pet_index = i
            break
    
    if current_pet is None:
        return render_template('passport.html', pet=None, error_message=f"錯誤：找不到 ID 為 {pet_id} 的寵物檔案。"), 404
        
    prev_id = pets[pet_index - 1]['id'] if pet_index > 0 else None
    next_id = pets[pet_index + 1]['id'] if pet_index < len(pets) - 1 else None
    
    return render_template('passport.html', pet=current_pet, prev_id=prev_id, next_id=next_id)


# 6. 協尋中心頁面
@app.route('/messageboard')
@app.route('/show_message_board')
def show_message_board():
    """顯示留言板頁面，並加載所有走失啟事和留言數據"""
    messages_data = load_messages()
    
    return render_template('messageboard.html', 
                           posts=messages_data["posts"], 
                           messages=messages_data["messages"])


# 7. 處理走失啟事發布
@app.route('/post_lost_pet', methods=['POST'])
def handle_pet_post():
    """處理前端發布的走失啟事"""
    messages_data = load_messages()
    
    new_id = (max([p.get('id', 0) for p in messages_data["posts"]]) + 1) if messages_data["posts"] else 1
    
    image_filename = ""
    if 'petImage' in request.files:
        file = request.files['petImage']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_filename = url_for('static', filename=f'uploads/{filename}')
        
    post_data = {
        "id": new_id, 
        "petName": request.form.get('petName'),
        "petSpecies": request.form.get('petSpecies'),
        "lostDate": request.form.get('lostDate'),
        "lostLocation": request.form.get('lostLocation'),
        "petFeatures": request.form.get('petFeatures'),
        "imageUrl": image_filename,
        "isResolved": False,
        "postTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    messages_data["posts"].insert(0, post_data)
    save_messages(messages_data)

    return jsonify({"success": True, "message": f"走失啟事【{post_data['petName']}】發布成功！", "post_data": post_data}), 201


# 8. 處理留言線索發布
@app.route('/post_message', methods=['POST'])
def handle_message_post():
    """處理前端發布的留言線索"""
    data = request.json
    post_id = data.get('postId')
    
    if not post_id or not data.get('content'):
        return jsonify({"success": False, "message": "缺少必要參數 (postId, content)"}), 400
        
    messages_data = load_messages()
    
    new_msg_id = (max([m.get('id', 0) for m in messages_data["messages"]]) + 1) if messages_data["messages"] else 1
    
    message_data = {
        "id": new_msg_id,
        "postId": int(post_id),
        "username": data.get('username', '熱心網友'),
        "content": data.get('content'),
        "isOwnerReply": data.get('isOwnerReply', False),
        "postTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    messages_data["messages"].insert(0, message_data)
    save_messages(messages_data)

    return jsonify({"success": True, "message": "線索發布成功！", "message_data": message_data}), 201


# 9. 其他靜態頁面路由
@app.route('/<template_name>.html')
def serve_template(template_name):
    
    if template_name == 'passport':
        pets_data = load_pets()
        if pets_data:
            first_pet_id = pets_data[0].get('id')
            return redirect(url_for('show_pet_passport', pet_id=first_pet_id))
        
        return render_template('passport.html', pet=None)

    if template_name == 'messageboard':
        return redirect(url_for('show_message_board'))

    if template_name in ['vendor', 'safety', 'knowledge']:
        return render_template(f'{template_name}.html')
         
    return "頁面不存在", 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)