import os, json, time, datetime, requests, pygame
from dotenv import load_dotenv
from pathlib import Path
from sys import exit

conversation = [
    {"role": "system", "content": (
        "Provide users health information, but don't diagnose people, tell people to see a doctor instead, and make sure your responses are short."
    )}
]

load_dotenv(Path("/healthapp/.env"))
HF_TOKEN = os.getenv("HF_TOKEN")
HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
CACHE_FILE = "tasks_cache.json"

def hf_chat_query(prompt,model="meta-llama/Llama-3.1-8B-Instruct:sambanova"):
    if not HF_TOKEN: return "Sorry, there was an error."
    try:
        r=requests.post(HF_CHAT_URL,
            headers=HEADERS,
            json={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":500},
            timeout=(10,600))
        if r.status_code!=200: return "Sorry, there was an error."
        if "application/json" not in r.headers.get("Content-Type",""): return "Sorry, there was an error."
        try: data=r.json()
        except: return "Sorry, there was an error."
        msg=data.get("choices",[{}])[0].get("message",{}).get("content")
        if not msg or not isinstance(msg,str): return "Sorry, there was an error."
        return msg.strip()
    except Exception as e: return "Sorry, there was an error."


def city_to_coordinates(city):
    try:
        time.sleep(1.1)
        url="https://nominatim.openstreetmap.org/search"
        params={"q":city,"format":"json","limit":1}
        h={"User-Agent":"HydrAidApp/1.0 (isobelparry03@gmail.com)"}
        r=requests.get(url,params=params,headers=h,timeout=10)
        data=r.json()
        if not data:
            time.sleep(1.1)
            r=requests.get("https://nominatim.openstreetmap.fr/search",params=params,headers=h,timeout=10)
            data=r.json()
        if not data: return None
        return float(data[0]["lat"]),float(data[0]["lon"])
    except: return None


def concise_task(prompt):
    raw = hf_chat_query(prompt)
    if not raw or "error" in raw.lower() or "http" in raw.lower():
        return "Sorry, there was an error."

    bits = [x.strip("-• ").strip() for x in raw.splitlines() if x.strip()]
    for b in bits:
        if any(w in b.lower() for w in ("what a", "great", "you could", "consider", "remember")):
            continue
        if 4 < len(b.split()) <= 12:
            return b.rstrip(".") + "."
    if bits:
        first = bits[0].split()[:10]
        return " ".join(first).rstrip(".") + "."
    return "Sorry, there was an error."



def load_or_generate_daily_tasks():
    if os.path.exists(CACHE_FILE):
        try:
            today=datetime.date.today().isoformat()
            with open(CACHE_FILE,"r",encoding="utf-8") as f: d=json.load(f)
            if d.get("date")==today: return d["tasks"]
        except: pass
    try:
        health=concise_task("Give me a daily action task (max 12 words) to help improve personal health and wellbeing and phrase it in a motivational way.")
        time.sleep(0.3)
    except: health="Sorry, there was an error."
    try:
        water=concise_task("Give me a short, daily action task (max 12 words) to help clean water and sanitation and phrase it in a motivational way.")
    except: water="Sorry, there was an error."
    t={"health":health,"water":water}
    try:
        with open(CACHE_FILE,"w",encoding="utf-8") as f:
            json.dump({"date":datetime.date.today().isoformat(),"tasks":t},f,indent=2)
    except: pass
    return t

daily_tasks = load_or_generate_daily_tasks()
pygame.init();pygame.font.init()
screenwidth,screenheight=375,667
screen=pygame.display.set_mode((screenwidth,screenheight))
pygame.display.set_caption("HydrAid")
clock=pygame.time.Clock()
font=pygame.font.SysFont("Bahnschrift",18)


def load(path, size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size) if size else img
    except Exception:
        surf = pygame.Surface(size if size else (50, 50))
        surf.fill((200, 200, 200))
        return surf

background   = load("media/homebackground.png", (screenwidth, screenheight))
home_img     = load("media/house.png", (50, 50))
checklist_img= load("media/checklist.png", (70, 70))
search_img   = load("media/binoculars.png", (70, 70))
airobot_img  = load("media/robot.png", (70, 70))
checklist_bg = load("media/checklistbg.png", (screenwidth, screenheight))
finder_bg    = load("media/finderbg.png", (screenwidth, screenheight))
chatbot_bg   = load("media/chatbotbg.png", (screenwidth, screenheight))

check_rect  = pygame.Rect(157, 350, 70, 70)
search_rect = pygame.Rect(57, 350, 70, 70)
ai_rect     = pygame.Rect(257, 350, 70, 70)
home_rect   = pygame.Rect(167, 50, 50, 50)
text_box    = pygame.Rect(37, 205, 300, 50)
dropdown_rect = pygame.Rect(37, 265, 240, 50)
search_button_rect = pygame.Rect(277, 265, 60, 50)
chatbox     = pygame.Rect(26, 500, 322, 100)
CHAT_AREA   = pygame.Rect(23, 191, 327, 295)
FINDER_AREA = pygame.Rect(37, 325, 302, 265)
TASK_HEALTH_RECT = pygame.Rect(48, 218, 280, 90)
TASK_WATER_RECT  = pygame.Rect(48, 367, 280, 90)

last_search_time = 0
SEARCH_COOLDOWN = 1.1
screen_state = "home"
user_text = ""
active = False
current_amenity = "hospital"
dropdown_open = False
amenities = ["hospital", "clinic", "social_facility", "water_point"]
finder_lines = ["Type a city name or coordinates into the top box."]
finder_scroll = 0
chat_lines = ["Assistant: Hi! How can I help with your health today?"]
chat_scroll = 0

def wrap_text(text, font, width):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_scrollable_lines(lines, rect, scroll):
    clip = screen.get_clip()
    screen.set_clip(rect)
    y = rect.y - scroll
    for line in lines:
        for w in wrap_text(line, font, rect.width - 10):
            screen.blit(font.render(w, True, (64, 64, 64)), (rect.x + 5, y+3))
            y += font.get_linesize()
    screen.set_clip(clip)

def lookup_amenity(coord_text,amenity_type="hospital"):
    coord_text=coord_text.strip()
    try: lat,lon=map(float,coord_text.split(","))
    except:
        coords=city_to_coordinates(coord_text)
        if not coords: return [f"Couldn't find amenities for '{coord_text}'. Please try another city or enter latitude,longitude."]
        lat,lon=coords
    amap={"hospital":"Hospitals","clinic":"Clinics","social_facility":"Social Facilities","water_point":"Water Points"}
    display=amap.get(amenity_type,"Locations")
    lines=[f"Searching {display} near {lat:.4f},{lon:.4f}..."]
    q=f'''[out:json][timeout:15];
    node["amenity"="{amenity_type}"](around:5000,{lat},{lon});
    out center 20;'''
    try:
        r=requests.get("https://overpass-api.de/api/interpreter",params={"data":q},timeout=25)
        if r.status_code!=200: return [f"Overpass HTTP {r.status_code}"]
        data=r.json(); elems=data.get("elements",[])
        if not elems: return [f"No {display.lower()} found nearby."]
        for e in elems[:15]:
            t=e.get("tags",{})
            name=t.get("name","Unnamed")
            addr=t.get("addr:street",t.get("addr:full",t.get("address","Unknown")))
            phone=t.get("phone",t.get("contact:phone","N/A"))
            lines.append(f"{name} — {addr} — {phone}")
        return lines
    except Exception as e: return [f"Error: {e}"]


def draw_home():
    screen.blit(background, (0, 0))
    screen.blit(checklist_img, check_rect.topleft)
    screen.blit(search_img, search_rect.topleft)
    screen.blit(airobot_img, ai_rect.topleft)

def draw_dropdown():
    label = font.render(current_amenity.replace("_", " ").title(), True, (64, 64, 64))
    pygame.draw.rect(screen, (255,255,255), dropdown_rect)
    pygame.draw.rect(screen, (255,255,255), dropdown_rect, 2)
    screen.blit(label, (dropdown_rect.x + 8, dropdown_rect.y + 15))
    if dropdown_open:
        for i, a in enumerate(amenities):
            item_rect = pygame.Rect(dropdown_rect.x, dropdown_rect.bottom + i * 36, dropdown_rect.width, 36)
            mx, my = pygame.mouse.get_pos()
            pygame.draw.rect(screen, (244,244,255) if item_rect.collidepoint(mx,my) else (255,255,255), item_rect)
            screen.blit(font.render(a.replace("_"," ").title(), True, (64,64,64)), (item_rect.x+8, item_rect.y+8))

def draw_finder():
    screen.blit(finder_bg, (0,0))
    screen.blit(home_img, home_rect.topleft)
    pygame.draw.rect(screen, (255,255,255), FINDER_AREA, 2)
    draw_scrollable_lines(finder_lines, FINDER_AREA, finder_scroll)
    pygame.draw.rect(screen, (0,200,255) if active else (255,255,255), text_box, 2)
    screen.blit(font.render(user_text, True, (64,64,64)), (text_box.x+6, text_box.y+15))
    draw_dropdown()
    pygame.draw.rect(screen, (0,200,0), search_button_rect)
    screen.blit(font.render("Go", True, (255,255,255)), (search_button_rect.x + 18, search_button_rect.y + 15))

def draw_chatbot():
    screen.blit(chatbot_bg,(0,0))
    screen.blit(home_img,home_rect)
    draw_scrollable_lines(chat_lines,CHAT_AREA,chat_scroll)
    c = (0,200,255) if active else (73,105,158)
    pygame.draw.rect(screen,c,chatbox,3)
    screen.blit(font.render(user_text,True,(0,0,0)),(chatbox.x+6,chatbox.y+8))

def draw_checklist():
    screen.blit(checklist_bg,(0,0))
    screen.blit(home_img,home_rect)
    for rect,txt in [(TASK_HEALTH_RECT,daily_tasks["health"]),(TASK_WATER_RECT,daily_tasks["water"])]:
        pygame.draw.rect(screen,(255,255,255),rect)
        pygame.draw.rect(screen,(255,255,255),rect,2)
        draw_scrollable_lines([txt],rect,0)

running = True
while running:
    screen.fill((255,255,255))
    if screen_state=="home": draw_home()
    elif screen_state=="finder": draw_finder()
    elif screen_state=="chatbot": draw_chatbot()
    elif screen_state=="checklist": draw_checklist()

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False
        mx,my = pygame.mouse.get_pos()
        if e.type==pygame.MOUSEBUTTONDOWN:
            if e.button==4:
                if screen_state=="finder": finder_scroll=max(finder_scroll-20,0)
                elif screen_state=="chatbot": chat_scroll=max(chat_scroll-20,0)
            elif e.button==5:
                if screen_state=="finder": finder_scroll+=20
                elif screen_state=="chatbot": chat_scroll+=20

            if screen_state=="home":
                if check_rect.collidepoint(mx,my):
                    screen_state="checklist"
                    user_text=""
                elif search_rect.collidepoint(mx,my):
                    screen_state="finder"
                    user_text=""
                elif ai_rect.collidepoint(mx,my):
                    screen_state="chatbot"
                    user_text=""

            elif screen_state in ("finder","chatbot","checklist") and home_rect.collidepoint(mx,my):
                screen_state="home"
                user_text=""

            if screen_state == "finder":
                if search_button_rect.collidepoint(mx, my):
                    now = time.time()
                    if now - last_search_time >= SEARCH_COOLDOWN:
                        finder_lines = lookup_amenity(user_text.strip(), current_amenity)
                        finder_scroll = 0
                        dropdown_open = False
                        last_search_time = now
                    else:
                        finder_lines = ["Please wait a moment before searching again."]
                elif dropdown_rect.collidepoint(mx, my):
                    dropdown_open = not dropdown_open
                    if dropdown_open:
                        active = False
                elif dropdown_open:
                    item_h = 36
                    clicked_item = False
                    for i, a in enumerate(amenities):
                        item_rect = pygame.Rect(dropdown_rect.x, dropdown_rect.bottom + i*item_h, dropdown_rect.width, item_h)
                        if item_rect.collidepoint(mx, my):
                            current_amenity = a
                            dropdown_open = False
                            clicked_item = True
                            break
                    if not clicked_item:
                        dropdown_open = False
                elif text_box.collidepoint(mx, my):
                    active = True
                    dropdown_open = False
                else:
                    active = False
                    dropdown_open = False

            if screen_state=="chatbot":
                active = chatbox.collidepoint(mx,my)

        if e.type==pygame.KEYDOWN:
            if active:
                if e.key==pygame.K_RETURN:
                    if screen_state=="chatbot":
                        text=user_text.strip()
                        if text:
                            chat_lines.append(f"You: {text}")
                            reply=hf_chat_query(text)
                            chat_lines+=wrap_text(f"Assistant: {reply}",font,CHAT_AREA.width-10)
                        user_text=""
                    elif screen_state=="finder":
                        active=False
                elif e.key==pygame.K_BACKSPACE:
                    user_text=user_text[:-1]
                else:
                    user_text+=e.unicode

    pygame.display.update()
    clock.tick(60)

pygame.quit()
exit()
