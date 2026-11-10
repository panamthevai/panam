#!/data/data/com.termux/files/usr/bin/bash
clear
echo -e "\e[1;32m==\e[0m"

echo -e "\e[1;36m    💥 PANAM 💥       \e[0m"
echo -e "\e[1;32m==\e[0m"
echo -e "\e[1;33m[+] Adding Panam Custom Repository...\e[0m"

echo "deb [trusted=yes] https://panamthevai.github.io/panam ./" > $PREFIX/etc/apt/sources.list.d/panam.list
apt update -y

echo -e "\e[1;32m[✓] Repository Added Successfully!\e[0m"

echo -e "\e[1;35m[+] Installing mytool...\e[0m"
apt install mytool -y

echo -e "\e[1;32m[✓] All Done! Type 'mytool' to start.\e[0m"
