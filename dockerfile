FROM python:3.13-slim

WORKDIR /wingetrepo

RUN apt-get update && apt-get install -y \
    git \
    osslsigncode \
    wget \
    && wget -q http://archive.ubuntu.com/ubuntu/pool/main/i/icu/libicu74_74.2-1ubuntu3_amd64.deb \
    && dpkg -i libicu74_74.2-1ubuntu3_amd64.deb \
    && rm libicu74_74.2-1ubuntu3_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN MSIX_BIN=$(python -c "import msix; import os; print(os.path.join(os.path.dirname(msix.__file__), 'bin'))") \
    && chmod +x "$MSIX_BIN/makemsix" \
    && chmod +x "$MSIX_BIN/libmsix.so" \
    && echo "$MSIX_BIN" > /etc/ld.so.conf.d/makemsix.conf \
    && ldconfig \
    && ldd "$MSIX_BIN/makemsix"

COPY . .

CMD ["python", "./main.py", "/docker"]