# Dockerfile to spin up a working Katana installation
FROM python:3.8

ENV DEBIAN_FRONTEND=noninteractive

# Install base Dependencies
RUN apt-get update -qq \
	&& apt-get install -y -qq python-tk tk-dev libffi-dev libssl-dev pandoc \
	libgmp3-dev libzbar-dev tesseract-ocr xsel libpoppler-cpp-dev libmpc-dev \
	libdbus-glib-1-dev ruby ruby-dev libenchant-2-dev apktool nodejs groff binwalk \
	foremost tcpflow poppler-utils exiftool steghide stegsnow bison ffmpeg \
	libgd-dev less \
	# Clean up for smaller images
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

# Gem complained unless you bootstrapped rdoc first. I don't know why.
RUN gem install rdoc --no-document
RUN gem install zsteg

# Compile and install npiet
RUN git clone https://github.com/gleitz/npiet /opt/npiet
# npiet includes `sys/malloc.h` which doesn't exist. Malloc definitions come
# from stdlib.h.
RUN sed -i 's|sys/malloc\.h|stdlib.h|g' /opt/npiet/npiet-foogol.*
WORKDIR /opt/npiet
RUN ./configure && make && make install

# Download jsteg
RUN wget -O /usr/local/bin/jsteg https://github.com/lukechampine/jsteg/releases/download/v0.3.0/jsteg-linux-amd64 && chmod +x /usr/local/bin/jsteg
RUN wget -O /usr/local/bin/slink https://github.com/lukechampine/jsteg/releases/download/v0.3.0/slink-linux-amd64 && chmod +x /usr/local/bin/slink

# Download, compile and install snow
RUN wget -O /usr/snow.tar.gz http://www.darkside.com.au/snow/snow-20130616.tar.gz
WORKDIR /usr
RUN tar -xvf snow.tar.gz
WORKDIR /usr/snow-20130616/
RUN make
RUN cp /usr/snow-20130616/snow /usr/local/bin/snow && chmod +x /usr/local/bin/snow

# Clone Katana Repository
RUN git clone --recursive https://github.com/JohnHammond/katana.git /katana
# Install katana python dependencies
WORKDIR /katana
# Unfortunately, since we clone this I can't make a change directly and had to path with SED. 
# I could have changed the clone to a Copy of this project, but that would require moving the Dockerfile
# up a directory (due to security concerns Docker cannot build anything above its build context)
# Arguably a Copy makes more sense as the Clone makes testing local changes harder.
# So to make it explicit, I'd recommend 
# 1. Moving the Dockerfile up a directory
# 2. Removing the Cloning
# 3. COPYing the local folder
	# COPY . /katana
# 4. Updating the path of the COPY that occurs like 15 lines down
	# COPY ./docker/katana.sh /start.sh

RUN sed -i "s/cmd2=='1.0.1'/cmd2==1.0.1/" requirements.txt

RUN pip install -r requirements.txt

# Create runtime data directory directory
RUN mkdir /data

# Copy the start script
COPY katana.sh /start.sh
RUN chmod +x /start.sh

# Run katana
ENTRYPOINT ["/start.sh"]
CMD ["-c", "/data/katana.ini", "-m", "monitor=/data/targets,outdir=/data/results"]
