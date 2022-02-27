if [ $(id -u) -gt 0 ];
  then echo "I need root...!!!"
  exit

else
  echo  "\n\nOkay Lazy peeps... im gonna install katana for you...\nInstalling dependencies...\n"

  sudo apt update
  sudo apt-get install -y python-tk tk-dev libffi-dev libssl-dev pandoc \
  libgmp3-dev libzbar-dev tesseract-ocr xsel libpoppler-cpp-dev libmpc-dev \
  libdbus-glib-1-dev ruby libenchant-dev apktool nodejs groff binwalk \
  foremost tcpflow poppler-utils exiftool steghide stegsnow bison ffmpeg \
  libgd-dev less

  echo -e "\n\nRunning Setup...\n\n"
  python3.7 -m venv env
  source env/bin/activate
  python setup.py install

fi
