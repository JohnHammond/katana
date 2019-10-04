#!/bin/bash

# Define colors...
RED=`tput bold && tput setaf 1`
GREEN=`tput bold && tput setaf 2`
YELLOW=`tput bold && tput setaf 3`
BLUE=`tput bold && tput setaf 4`
NC=`tput sgr0`

function RED(){
	echo -e "\n${RED}${1}${NC}"
}
function GREEN(){
	echo -e "\n${GREEN}${1}${NC}"
}
function YELLOW(){
	echo -e "\n${YELLOW}${1}${NC}"
}
function BLUE(){
	echo -e "\n${BLUE}${1}${NC}"
}

BLUE "strings"
rm -r results/; ./katana.py  -ff 'USCGA{.*?}' -a ./tests/orchestra  


BLUE "exiftool"
rm -r results/; ./katana.py  -ff 'USCGA{.*?}' -a ./tests/woof64.jpg  --exclude crypto


BLUE "morsecode"
rm -r results/; ./katana.py  -ff 'gigem{.*?}' -a ./tests/tamuctf_morsecode.txt  --exclude crypto


BLUE "QR code"
rm -r results/; ./katana.py  -ff 'USCGA{.*?}' -a ./tests/qrcode.png  


BLUE "steghide (no password)"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a ./tests/rubber_ducky.jpg  

BLUE "steghide (with password)"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a ./tests/evil_ducky.jpg --dict ./tests/rockyou.txt  


BLUE "snow"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a ./tests/let_it_snow.txt  


BLUE "zsteg"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a ./tests/pierre.png  


BLUE "robots.txt"
rm -r results/; ./katana.py -ff "FLAG{.*?}" -a 'https://johnhammond.org'  

BLUE "basic SQL injection"
rm -r results/ ; ./katana.py -a "http://2018shell.picoctf.com:53261/" -ff 'picoCTF{.*?}'


BLUE "ROT47"
rm -r results/; ./katana.py -ff "sun{.*?}" -a './tests/welcome_crypto.txt'  


BLUE "Brainfuck"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a './tests/brainfuck.txt'  


BLUE "pdftotext"
rm -r results/; ./katana.py -ff "actf{.*?}" -a './tests/blank_paper.pdf' 

BLUE "Malbolge"
rm -r results; ./katana.py -a -ff "InnoCTF{.*?}" tests/inno.txt

BLUE "Differential RSA"
rm -r results/ ; ./katana.py -ff '.*RSA' --unit crypto.rsa tests/weird_rsa.txt
