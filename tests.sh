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
rm -r results/; ./katana.py  -ff 'USCGA{.*?}' -a ./tests/orchestra -v


BLUE "exiftool"
rm -r results/; ./katana.py  -ff 'USCGA{.*?}' -a ./tests/woof64.jpg -v --exclude crypto


BLUE "morsecode"
rm -r results/; ./katana.py  -ff 'gigem{.*?}' -a ./tests/tamuctf_morsecode.txt -v --exclude crypto


BLUE "QR code"
rm -r results/; ./katana.py  -ff 'USCGA{.*?}' -a ./tests/qrcode.png -v


BLUE "steghide (no password)"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a ./tests/rubber_ducky.jpg -v 

BLUE "steghide (with password)"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a ./tests/evil_ducky.jpg --dict /opt/rockyou.txt -v 


BLUE "snow"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a ./tests/let_it_snow.txt -v 


BLUE "zsteg"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a ./tests/pierre.png -v 


BLUE "robots.txt"
rm -r results/; ./katana.py -ff "FLAG{.*?}" -a 'https://johnhammond.org' -v 


BLUE "basic SQL injection"
rm -r results/ ; ./katana.py -a "http://2018shell.picoctf.com:53261/" -nd -ff 'picoCTF{.*?}'


BLUE "ROT47"
rm -r results/; ./katana.py -ff "sun{.*?}" -a './tests/welcome_crypto.txt' -v 


BLUE "Brainfuck"
rm -r results/; ./katana.py -ff "USCGA{.*?}" -a './tests/brainfuck.txt' -v 


BLUE "pdftotext"
rm -r results/; ./katana.py -ff "actf{.*?}" -a './tests/blank_paper.pdf' -v 