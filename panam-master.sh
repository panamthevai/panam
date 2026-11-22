#!/data/data/com.termux/files/usr/bin/bash

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SERVER_URL="https://onrender.com"

while true; do
    clear
    echo -e "${CYAN}=================================================${NC}"
    echo -e "${GREEN}   🚀 PANAM CLOUD MASTER CONTROL (TERMUX)       ${NC}"
    echo -e "${CYAN}=================================================${NC}"
    echo -e "1) 📊 Live Server Status & Visitors பார்க்க"
    echo -e "2) 📦 புதிய .deb பேக்கேஜ் அப்டேட் & Repo Build செய்ய"
    echo -e "3) 🚀 GitHub & Render Cloud-க்கு Sync (Push) செய்ய"
    echo -e "4) 🔄 Render சர்வரை 24/7 விழித்திருக்க Ping செய்ய"
    echo -e "5) ❌ வெளியேறு (Exit)"
    echo -e "${CYAN}=================================================${NC}"
    read -p "தேர்வை உள்ளிடவும் [1-5]: " choice

    case $choice in
        1)
            echo -e "${YELLOW}சர்வர் டேட்டா பெறப்படுகிறது...${NC}"
            curl -s "$SERVER_URL/api/status" | python3 -m json.tool
            read -p "தொடர Enter அழுத்தவும்..."
            ;;
        2)
            echo -e "${YELLOW}APT Packages Index உருவாக்கப்படுகிறது...${NC}"
            if command -v dpkg-scanpackages &> /dev/null; then
                dpkg-scanpackages -m . /dev/null > Packages
                gzip -k -f Packages
                echo -e "${GREEN}✅ Packages மற்றும் Packages.gz வெற்றிகரமாக அப்டேட் செய்யப்பட்டது!${NC}"
            else
                echo -e "${RED}dpkg-dev இல்லை! இன்ஸ்டால் செய்யப்படுகிறது...${NC}"
                pkg install dpkg-scanpackages -y
            fi
            read -p "தொடர Enter அழுத்தவும்..."
            ;;
        3)
            echo -e "${YELLOW}GitHub & Render-க்கு அப்லோட் செய்யப்படுகிறது...${NC}"
            cp -f index.html templates/index.html 2>/dev/null
            git add -A
            git commit -m "Master Sync: $(date +'%Y-%m-%d %H:%M')"
            git push -f origin main
            echo -e "${GREEN}✅ அப்டேட் முடிந்தது! 2 நிமிடங்களில் Render லைவ் ஆகும்.${NC}"
            read -p "தொடர Enter அழுத்தவும்..."
            ;;
        4)
            echo -e "${YELLOW}Render சர்வர் Ping செய்யப்படுகிறது...${NC}"
            STATUS=$(curl -o /dev/null -s -w "%{http_code}" "$SERVER_URL")
            echo -e "${GREEN}✅ சர்வர் நிலை: HTTP $STATUS (Active)${NC}"
            read -p "தொடர Enter அழுத்தவும்..."
            ;;
        5)
            echo -e "${CYAN}நன்றி!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}தவறான தேர்வு!${NC}"
            sleep 1
            ;;
    esac
done
