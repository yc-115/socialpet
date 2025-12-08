# 毛孩交友天地 - Pet Social Universe

## 項目簡介 (Project Overview)

我們這個專題「毛孩交友天地」其實就是想幫各位毛爸媽解決社交困境！

簡單來說，我們打造了一個 App 應用程式 來串連寵物跟主人。我們有三大核心功能：
- 寵物版 Tinder + 地圖導航： 想像一下，這個 App 不只是地圖，還能用地理定位技術，讓您馬上看到附近哪裡有寵物友善的店，以及誰家的毛孩正在附近等著交朋友。右邊的 社交卡片 讓您像滑 Tinder 一樣，快速配對、認識潛在玩伴！
- AI 智慧軍師： 我們加入了 AI 助手，您有任何疑難雜症，像是「附近有沒有適合大型犬跑跳的公園？」或是「怎麼判斷貓咪現在是不是生氣了？」，AI 都能即時回答，擔任您的寵物知識顧問。
- 互動安全保障： 為了避免社交摩擦，每個毛孩都有專屬的 數位護照。上面清楚標註了寵物的個性標籤（例如：慢熟怕生、愛玩球），還有重要的健康備註和醫療紀錄。這樣大家在約出來玩之前，就能確保互動是安全又友善的。

***

## 組員資訊 (Team Information)

| 職位 | 姓名 | 學號 |
| :--- | :--- | :--- |
| 組員 | 李雅郁 | 41371204H |
| 組員 | 劉祐羽 | 41371210H |
| 組員 | 周怡辰 | 41371211H |

***

## 專案資源連結 (Project Resources)

| 資源名稱 | 連結/說明 |
| :--- | :--- |
| **線上網站網址 (已部署)** | [https://socialpet-txxm.onrender.com](https://socialpet-txxm.onrender.com) |
| **程式碼 GitHub Repo** | [https://github.com/yc-115/socialpet](https://github.com/yc-115/socialpet.git) |
| **專題展示影片** | [請在此貼上您的專題展示影片連結] |

***

## 技術棧與部署 (Technology & Deployment)

### 主要技術 (Stack)

* **後端框架：** Python / Flask
* **AI 整合：** Google Gemini API
* **地圖服務：** Leaflet.js / OpenStreetMap
* **前端介面：** HTML5 / CSS3 / Bootstrap 5

### 部署細節 (Deployment Details)

本應用程式透過 **Render** 雲端平台部署，並採用 Gunicorn 作為 WSGI 伺服器。

| 設定項目 | 數值 | 說明 |
| :--- | :--- | :--- |
| **Runtime** | Python 3 | Python 運行環境。 |
| **Start Command** | `gunicorn app:app` | 啟動 `app.py` 中名為 `app` 的 Flask 實例。 |
| **Environment Variables** | `FLASK_SECRET_KEY`, `GEMINI_API_KEY` | 確保會話安全與 AI 服務連線。 |

***

## 核心功能 (Key Features)

* **毛孩社交地圖：** 透過 Leaflet 標記附近所有已註冊毛孩的活動地點。
* **AI 智慧助手：** 即時問答，提供寵物知識和地點建議。
* **滑動社交卡片：** 瀏覽附近毛孩的檔案，進行快速配對互動。
* **寵物數位護照：** 詳細記錄毛孩的品種、年齡、個性標籤和重要醫療備註。
* **協尋情報站：** 供使用者即時發布走失啟事及提供線索留言。
