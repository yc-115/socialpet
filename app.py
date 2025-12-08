import os
import json
from flask import Flask, request, render_template, redirect, url_for, jsonify
from werkzeug.utils import secure_filename 
import requests 
from datetime import datetime # ⭐ 新增：用於記錄時間

# --- 新增 Gemini 相關模組 ---
from google import genai
from google.genai.errors import APIError
# -----------------------------

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key_for_dev') 

# --- 配置區 ---
UPLOAD_FOLDER = 'static/uploads' 
DATA_FILE = 'pets.json' 
MESSAGES_FILE = 'messages.json' # ⭐ 新增：走失寵物啟事及留言資料
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# ⭐ 初始化 messages.json
if not os.path.exists(MESSAGES_FILE):
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        # 結構: { "posts": [], "messages": [] }
        json.dump({"posts": [], "messages": []}, f, ensure_ascii=False, indent=4) 

# 檔案類型調整：允許圖片和醫療文件 (pdf, docx)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

# ----------------------------------------------------
# 輔助函數 (地理編碼、JSON & 檔案處理)
# ----------------------------------------------------

# ⭐ 地理編碼函數：保留，但 handle_upload 將不再使用
def geocode_address(address):
    """使用 Nominatim API 將地址轉換為 (lat, lon)"""
    if not address:
        return None, None
        
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'tw' # 限制在台灣範圍內提高準確度
    }
    # 推薦設置 User-Agent
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
            # 保持原始順序 (最舊到最新)
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_pets(pets):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(pets, f, ensure_ascii=False, indent=4)

def get_pet_by_id(pet_id):
    pets = load_pets()
    
    try:
        target_id = int(pet_id)
    except ValueError:
        return None
        
    for pet in pets:
        if int(pet.get('id', 0)) == target_id:
            return pet
    return None

# ⭐ 載入留言板數據
def load_messages():
    try:
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"posts": [], "messages": []}

# ⭐ 儲存留言板數據
def save_messages(data):
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ⭐ 根據 ID 查找單個走失啟事
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
# Gemini AI 配置區 (保持不變)
# ----------------------------------------------------
GEMINI_API_KEY = "AIzaSyCYxks0PfkeuxgT-znQT8HZILE1Pq1yZK0" 
client = None
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"ERROR: Failed to initialize Gemini Client: {e}")
    
MODEL_NAME = "gemini-2.5-flash"
PET_CONTEXT = """
您是寵物社交地圖『毛孩交友天地』的 AI 智慧助手，請以友善、簡潔且中文繁體回答。
請鼓勵用戶多使用地圖和社交卡片進行探索。
"""

# ----------------------------------------------------
# 路由區
# ----------------------------------------------------

# 1. 主頁面/地圖頁面 (index.html) (保持不變)
@app.route('/')
@app.route('/index.html')
@app.route('/show_main_map')
def show_main_map():
    """主地圖與社交頁面，讀取 pets.json 資料"""
    pets_data = load_pets()
    
    if not pets_data:
        # 為了讓前端卡片堆疊功能運作，資料庫空時提供 Mock Data (帶有經緯度)
        pets_data = [
            {"id": 101, "name": "點點", "species": "貴賓犬", "image_url": url_for('static', filename='mock_dog.png', _external=True), "tags": ["愛跑跳", "對狗友善"], "location": "信義公園", "lat": 25.033964, "lon": 121.564468, "interactionNote": "喜歡追球", "healthNote": "健康良好", "medicalRecords": []},
            {"id": 102, "name": "麻糬", "species": "布偶貓", "image_url": url_for('static', filename='mock_cat.png', _external=True), "tags": ["高冷", "慢熟怕生"], "location": "貓咪咖啡廳", "lat": 25.040183, "lon": 121.547192, "interactionNote": "不喜歡摸肚子", "healthNote": "對特定貓砂過敏", "medicalRecords": []}
        ]
        
    return render_template('index.html', pets=pets_data)

# 2. 上傳頁面 (upload.html) (保持不變)
@app.route('/upload.html')
@app.route('/show_upload_form')
def show_upload_form():
    """顯示上傳表單頁面"""
    return render_template('upload.html')

# 3. 處理表單提交 (核心功能) (保持不變)
@app.route('/upload', methods=['POST'])
def handle_upload():
    """處理毛孩資料和圖片上傳，並儲存到 pets.json"""
    
    # --- 處理主要照片上傳 ---
    if 'petImage' not in request.files or request.files['petImage'].filename == '':
        return "請上傳毛孩照片", 400

    pet_image_file = request.files['petImage']
    if not allowed_file(pet_image_file.filename):
        return "不允許的毛孩照片格式", 400
        
    pet_image_filename = secure_filename(pet_image_file.filename)
    pet_image_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pet_image_filename)
    pet_image_file.save(pet_image_file_path)

    # --- 處理醫療文件上傳 (多檔案) ---
    medical_records_urls = []
    if 'medicalRecord' in request.files:
        medical_files = request.files.getlist('medicalRecord')
        for file in medical_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                # 儲存檔案的 URL
                medical_records_urls.append({
                    "filename": filename,
                    "url": url_for('static', filename=f'uploads/{filename}')
                })
    
    # ⭐ ⭐ 關鍵修改：直接從表單獲取經緯度 (來自地圖點擊) ⭐ ⭐
    pet_location = request.form.get('location') # 這是地圖顯示的文字描述 (非地址)
    lat_str = request.form.get('lat')
    lon_str = request.form.get('lon')
    
    try:
        # 將字串轉換為浮點數
        lat = float(lat_str)
        lon = float(lon_str)
    except (TypeError, ValueError):
        # 如果地圖沒有成功傳回經緯度，則返回錯誤
        return "錯誤：未能獲取準確的地理座標 (請在地圖上點擊標記)。", 400
    # ⭐ ⭐ 關鍵修改結束 ⭐ ⭐
    
    # --- 處理個性標籤 ---
    tags = request.form.getlist('tags')
    other_tags_text = request.form.get('otherTagsText')
    
    # 將「其他」標籤的文字解析並合併
    if 'other' in tags and other_tags_text:
        # 移除原生的 'other' 標籤
        tags.remove('other') 
        # 將逗號分隔的文字轉換為列表並合併
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
        "lat": lat,  # 使用地圖傳入的經緯度
        "lon": lon   # 使用地圖傳入的經緯度
    }

    pets.append(pet_data)
    save_pets(pets)

    return render_template('success_page.html', pet_name=pet_data['name'], pet_id=pet_data['id'], image_url=pet_data['image_url'])

# 4. 處理 Gemini AI 聊天請求 (保持不變)
@app.route('/ai_chat', methods=['POST'])
def ai_chat():
    """處理前端發送的 AI 聊天請求"""
    user_query = request.json.get('query')
    
    if not client:
         return jsonify({"response": "🤖 AI 服務未啟用，請檢查金鑰或初始化失敗。"}, 503)
    if not user_query:
        return jsonify({"response": "請輸入您的問題。"}, 400)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[user_query],
            config=genai.types.GenerateContentConfig(
                system_instruction=PET_CONTEXT
            )
        )
        return jsonify({"response": response.text})

    except APIError:
        return jsonify({"response": "🤖 AI 服務連線失敗，請檢查金鑰或網路。"}, 500)
    except Exception as e:
        print(f"Unknown error in AI chat: {e}")
        return jsonify({"response": "🤖 發生未知錯誤。"}, 500)

# 5. 動態寵物數位護照頁面 (保持不變)
@app.route('/passport/<int:pet_id>')
def show_pet_passport(pet_id):
    """根據 URL 中的 pet_id 顯示特定的寵物護照，並提供前後導航 ID"""
    pets = load_pets()
    
    current_pet = None
    pet_index = -1
    
    # 查找當前寵物及其在列表中的索引
    for i, pet in enumerate(pets):
        if int(pet.get('id', 0)) == pet_id:
            current_pet = pet
            pet_index = i
            break
    
    if current_pet is None:
        return render_template('passport.html', pet=None, error_message=f"錯誤：找不到 ID 為 {pet_id} 的寵物檔案。"), 404
        
    # 確定前後寵物的 ID
    prev_id = pets[pet_index - 1]['id'] if pet_index > 0 else None
    next_id = pets[pet_index + 1]['id'] if pet_index < len(pets) - 1 else None
    
    return render_template('passport.html', pet=current_pet, prev_id=prev_id, next_id=next_id)


# ⭐ 6. 協尋中心頁面 (新增路由，取代舊的靜態路由)
@app.route('/messageboard')
@app.route('/show_message_board')
def show_message_board():
    """顯示留言板頁面，並加載所有走失啟事和留言數據"""
    messages_data = load_messages()
    
    # 傳遞所有啟事和留言到前端
    return render_template('messageboard.html', 
                           posts=messages_data["posts"], 
                           messages=messages_data["messages"])


# ⭐ 7. 處理走失啟事發布 (新增路由)
@app.route('/post_lost_pet', methods=['POST'])
def handle_pet_post():
    """處理前端發布的走失啟事"""
    messages_data = load_messages()
    
    # 確保 ID 唯一性
    new_id = (max([p.get('id', 0) for p in messages_data["posts"]]) + 1) if messages_data["posts"] else 1
    
    # 處理圖片上傳
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

    messages_data["posts"].insert(0, post_data) # 新貼文插在最前面
    save_messages(messages_data)

    return jsonify({"success": True, "message": f"走失啟事【{post_data['petName']}】發布成功！", "post_data": post_data}), 201


# ⭐ 8. 處理留言線索發布 (新增路由)
@app.route('/post_message', methods=['POST'])
def handle_message_post():
    """處理前端發布的留言線索"""
    data = request.json
    post_id = data.get('postId')
    
    if not post_id or not data.get('content'):
        return jsonify({"success": False, "message": "缺少必要參數 (postId, content)"}), 400
        
    messages_data = load_messages()
    
    # 確保 ID 唯一性
    new_msg_id = (max([m.get('id', 0) for m in messages_data["messages"]]) + 1) if messages_data["messages"] else 1
    
    message_data = {
        "id": new_msg_id,
        "postId": int(post_id),
        "username": data.get('username', '熱心網友'), # 假設可以從 session 獲取或預設
        "content": data.get('content'),
        "isOwnerReply": data.get('isOwnerReply', False),
        "postTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    messages_data["messages"].insert(0, message_data) # 新留言插在最前面
    save_messages(messages_data)

    return jsonify({"success": True, "message": "線索發布成功！", "message_data": message_data}), 201


# ⭐ 9. 其他靜態頁面路由 (修改 messageboard 路由)
@app.route('/<template_name>.html')
def serve_template(template_name):
    
    # 處理 /passport.html 連結 (自動導向最舊的寵物)
    if template_name == 'passport':
        pets_data = load_pets()
        if pets_data:
            # 導向索引 [0] 的寵物 ID (最舊的)
            first_pet_id = pets_data[0].get('id')
            return redirect(url_for('show_pet_passport', pet_id=first_pet_id))
        
        return render_template('passport.html', pet=None)

    # 處理 /messageboard.html 連結
    if template_name == 'messageboard':
        return redirect(url_for('show_message_board'))

    # 處理其他靜態頁面
    if template_name in ['vendor', 'safety', 'knowledge']:
        return render_template(f'{template_name}.html')
         
    return "頁面不存在", 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)