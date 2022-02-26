# Dockerfile to spin up a working Katana installation
FROM python:3.10.0b3

ENV DEBIAN_FRONTEND=noninteractive

# Install base Dependencies
RUN apt-get update -qq \
	&& apt-get install -y -qq python-tk tk-dev libffi-dev libssl-dev pandoc \
	libgmp3-dev libzbar-dev tesseract-ocr xsel libpoppler-cpp-dev libmpc-dev \
	libdbus-glib-1-dev ruby libenchant-2-dev apktool nodejs groff binwalk \
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
RUN pip install -r requirements.txt

# Create runtime data directory directory
RUN mkdir /data

# Copy the start script
COPY katana.sh /start.sh
RUN chmod +x /start.sh

# Run katana
ENTRYPOINT ["/start.sh"]
CMD ["-c", "/data/katana.ini", "-m", "monitor=/data/targets,outdir=/data/results"]
