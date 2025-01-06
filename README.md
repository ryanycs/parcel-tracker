# Parcel Tracker

## Concept Development
<!-- Why does your team want to build this idea/project?  -->

台灣有非常多的物流平台，而蝦皮等電商平台在商品送到後並不會立即通知我們去取貨，有時甚至會延遲半天之久。所以我們設計了一個 Discord Bot，透過Discord 指令來查詢不同物流的包裹進度，而且還不用輸入那些麻煩的驗證碼。同時我們還設計一個訂單查詢平台，結合到包裹追蹤的 discord 機器人，讓兩邊都能同步使用服務。

(圖片)

- 查詢不同物流公司的包裹進度，例如 7-11、全家、蝦皮、FamilyMart
- 架設一個包裹追蹤的 discord 機器人和訂單查詢平台

## Implementation Resources

<!-- e.g., How many Raspberry Pi? How much you spent on these resources? -->

## Existing Library/Software

<!-- Which libraries do you use while you implement the project -->

<!-- ### Frontend 主外觀: 
- meta charset="UTF-8"
    -  設置字符編碼為 UTF-8，這有助於網頁正確顯示不同語言的字符，包括中文。
- meta name="viewport" content="width=device-width, initial-scale=1.0"
    - 設定視口的寬度為設備的寬度，幫助頁面在移動設備上響應式顯示。
- title 
    - 定義網頁的標題，顯示在瀏覽器標簽頁上。
- style 
    - 其中包含了頁面的內聯 CSS 樣式，控製頁面的布局和設計。 -->
### Backend:
- fastapi
    - 負責後端 API 開發，處理邏輯和資料
- uvicorn
    - ASGI 伺服器，用於執行 FastAPI 
- requests
	- 對目標網頁發送 http requests
- beautifulsoup4
	- 解析爬到的 HTML
- pillow
	- 處理 captcha 圖片
- pytesseract
	- OCR 光學影像辨識

    
### Database:
- mysql.connector:
    - 建立與 MySQL 資料庫的連線

### Discord 機器人:
- discord.py
	- discord bot framework
- threading
	- 為了讓 Discord bot 有 Webhook 功能(用來接收 Backend API 所傳送包裹更新的通知)，所以使用 threading 來執行一個 FastAPI 後端監聽在 3000 port。


### Nginx reverse proxy
- Nginx
- certbot

## Implementation Process

<!-- What kind of problems you encounter, and how did you resolve the issue? -->

### 重點程式
- `.bot.env`:
    - 機器人環境相關變數
- `.backend.env`:
    - 資料庫環境及Webhook相關變數
- `/frontend`:
- `/backend` 後端服務
    - 功能: 提供 API 來追蹤各物流平台的包裹資訊
    - `api.py` : API 程式
    - `/parcel_tw` : 支援多個物流平台的包裹追蹤 module
- `/bot` 機器人服務
    - 功能: 提供與機器人互動的功能，如:通知包裹狀態
    - `/app` : 機器人相關 module
        - `bot.py`: 負責機器人的主邏輯。
    - `webhook.py`: 用來接收 Backend API 所傳送包裹更新的通知
    - `main.py` : 主程式
- `/db` 資料庫設定
    - 功能: 初始化資料庫，並匯入物流平台的基本資訊
檔案說明:
    - `init.sql`: 用於建立資料庫及其表格
    - `platform_info.sql`: 匯入物流平台的基本資料
 
 ### 遇到困難

- 大部分的網站都有防止爬蟲機制，每個網站繞過驗證碼的方式也不盡相同，爬蟲花費了不少的時間。
- 因為爬蟲與檢查包裹是否更新的邏輯是在後端中，因此 Discord 機器人沒辦法主動得知包裹狀態是否更新，後來解決方法是使用 Webhook 來讓機器人監聽一個連接埠，藉由接收後端傳送過來的通知來得知包裹更新狀態。

## Knowledge from Lecture

<!-- What kind of knowledge did you use on this project? -->
- Linux系統基本指令
- WebServer
- Nginx reverse proxy
- MailServer


## Installation

<!-- How do the user install with your project? -->

- 建立屬於自己的包裹追蹤的 discord 機器人
    - 詳細 discord bot 設置可參閱 [How to Make a Discord Bot in the Developer Portal](https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-the-developer-portal)
    - 簡易教學:
        - 到 https://discord.com/developers/applications
        - `New Application` -> 取名字
        -  到 Menu -> `OAuth2` -> OAuth2 URL Generator -> `bot` -> Bot Permissions -> `Adminstrator` -> 複製 url -> 貼到 browser 貼上 -> 選伺服器... -> 確認
        - 到 Menu ->`bot` -> Privileged Gateway Intents -> 三個選項都勾 -> save changes
    - 複製 `DISCORD_TOKEN` : Menu -> `bot` -> Token -> `Reset token` -> `COPY`
    
### Linux
- clone :
```
git clone git@github.com:ryanycs/parcel-tracker.git
cd parcel-tracker
```
- 將剛才取得 `DISCORD_TOKEN` 填入 `.bot.env` 中的`DISCORD_BOT_TOKEN=`
- 啟動 docker :
```      
# 若尚未安裝 docker 環境，請先
sudo snap install docker
sudo apt install docker-compose

# 建立 docker container
docker-compose up
```
- 所有服務上線，可以看到 discord bot 也有上線
    
## Usage

<!-- How to use your project -->
- container 建立完成後，即可使用 包裹追蹤 discord 機器人、訂單查詢平台
- **物流平台** 查詢僅允許以下輸入值:

| SEVEN_ELEVEN  |  FAMILY_MART   |  OK_MART   | SHOPEE |
| -------- | -------- | -------- |-------- |
| 小七 | 全家 | ok | 蝦皮 |
| 7-11 | family | okmart | shopee 
| seven| family-mart | ok-mart
| seven-eleven| family_mart | ok_mart
| seven_eleven| fami
| 711

- Discord bot
	- `/track [物流平台] [訂單編號]`: 查詢包裹進度
		![image](https://hackmd.io/_uploads/r1tRh9crJg.png)
		![image](https://hackmd.io/_uploads/BkCgpcqr1g.png)

	- `/subscribe [物流平台] [訂單編號]`: 訂閱包裹進度，如果包裹狀態有更新會傳送訊息通知使用者 ![image](https://hackmd.io/_uploads/S1behq9B1e.png)

	- `/unsubscribe [物流平台] [訂單編號]`: 取消訂閱過已經訂閱的包裹進度



- 訂單查詢平台:
    - 查詢包裹： 使用者選擇物流平台並輸入訂單 ID，然後點擊「查詢包裹」按鈕。若查詢成功，包裹狀態和時間將顯示在頁面上。
        - GET :`/api/track/{platform}/{orderId}`
        - (圖片)
            
    - 訂閱包裹更新：在查詢包裹後，使用者可以選擇訂閱包裹更新通知。點擊「訂閱包裹更新」按鈕，填寫電子郵件和 Discord 帳號後，點擊「提交訂閱」以完成訂閱。
        - POST : `/api/subscriptions`
        - (圖片)
    
    - 取消訂閱包裹更新：若使用者希望停止接收包裹更新，可以選擇取消訂閱。點擊「取消訂閱包裹更新」按鈕，填寫電子郵件和 Discord 帳號後，點擊「提交取消訂閱」。
        - DELETE : `/api/subscriptions`
        - (圖片)
            
## Future work
- mail 功能將於 2.0 版上線 

## Job Assignment


|       | 姓名     | 負責內容 | 
| ----- | --------| -------- | 
| 組長   | 蘇翊荃   | Discord 包裹機器人(爬蟲、資料庫、bot)、程式部署(Docker、Nginx Reverse Proxy)、程式整合    |
| 組員  | 陳品妤   |  前端網頁設計整合   |
| 組員  | 陳嘉璐   |  資料庫、做會議記錄、寫 Readme | 
| 組員  | 楊昱淞   |   前端網頁設計  |
| 組員  | 余政葳   |  報告  | 

## References
- [Postman Learning Center](https://learning.postman.com/docs/getting-started/overview/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [CORS (Cross-Origin Resource Sharing) - FastAPI](https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware)
- [Get Docker](https://docs.docker.com/get-started/get-docker/)
- [Docker | 建立 PostgreSQL 的 container 時，同時完成資料庫的初始化](https://eandev.com/post/container/docker-postgresql-initialization-scripts/)
## Demo 實作影片
