# 毛孩交友天地 - Pet Social Universe

## 項目簡介 (Project Overview)

本專題「毛孩交友天地」旨在為寵物和飼主建立一個安全的社交地圖與資訊平台。透過地理定位、個性化社交卡片和 AI 智慧助手，協助飼主輕鬆找到附近的寵物友善地點及潛在玩伴，並提供寵物數位護照以確保互動安全。

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
