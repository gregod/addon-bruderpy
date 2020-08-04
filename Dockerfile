ARG BUILD_FROM=homeassistant/base:3.12 
# ^^^^ just the fallback, see build.json for all
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

ENV OPENCV https://github.com/opencv/opencv/archive/4.4.0.tar.gz
ENV OPENCV_VER 4.4.0

ENV PYTHON_VERSION 3.8.5-r0
ENV NUMPY_VERSION 1.18.4-r0
ENV TESSERACT_VERSION 4.1.1-r3

# first numpy and tesseract runtimes + gnupg
RUN apk add -U --no-cache \
    python3~=$PYTHON_VERSION \
    py3-numpy~=$NUMPY_VERSION \
    tesseract-ocr~=$TESSERACT_VERSION \
    tesseract-ocr-data-deu~=$TESSERACT_VERSION \
    zlib py3-pip jpeg libjpeg freetype openjpeg openjpeg-tools gnupg\
    && ln -s /usr/include/locale.h /usr/include/xlocale.h

# then build opencv
RUN apk add -U --virtual=build-dependencies  \
    linux-headers musl libxml2-dev libxslt-dev libffi-dev \
    musl-dev libgcc openssl-dev jpeg-dev zlib-dev freetype-dev build-base \
    lcms2-dev openjpeg-dev openblas-dev  make cmake gcc ninja \ 
    clang-dev clang \
    && apk add py3-numpy-dev~=$NUMPY_VERSION python3-dev~=$PYTHON_VERSION openblas \
    && cd /opt \
    && curl -L $OPENCV | tar zx \
    && cd opencv-$OPENCV_VER \
    && mkdir build && cd build \
    && cmake -G Ninja \
            -D CMAKE_C_COMPILER=/usr/bin/clang \
            -D CMAKE_CXX_COMPILER=/usr/bin/clang++ \
            -D CMAKE_BUILD_TYPE=RELEASE \
            -D BUILD_DOCS=OFF \
            -D BUILD_EXAMPLES=OFF \
	        -D INSTALL_PYTHON_EXAMPLES=OFF \
            -D BUILD_PERF_TESTS=OFF \
            -D BUILD_TESTS=OFF \
            -D BUILD_PROTOBUF=OFF \
            -D BUILD_opencv_flann=OFF \
            -D BUILD_opencv_ml=OFF \
            -D BUILD_opencv_gapi=OFF \
            -D BUILD_opencv_objdetect=OFF \
            -D BUILD_opencv_video=OFF \
            -D BUILD_opencv_dnn=OFF \
            -D BUILD_opencv_shape=OFF \
            -D BUILD_opencv_videoio=OFF \
            -D BUILD_opencv_highgui=OFF \
            -D BUILD_opencv_superres=OFF \
            -D BUILD_opencv_ts=OFF \
            -D BUILD_opencv_features2d=OFF \
            -D BUILD_opencv_calib3d=OFF \
            -D BUILD_opencv_stitching=OFF \
            -D BUILD_opencv_videostab=OFF \
            -D CMAKE_INSTALL_PREFIX=/usr \
            -D WITH_FFMPEG=NO \
            -D WITH_ADE=OFF \
            -D WITH_OPENCL=OFF \
            -D WITH_V4L=OFF  \
            -D WITH_LIBV4L=OFF \
            -D WITH_FFMPEG=OFF \
            -D WITH_IPP=NO \
            -D PYTHON_EXECUTABLE=/usr/bin/python3 \
            -D WITH_OPENEXR=NO .. \
    && ninja && ninja install && rm -rf /opt/opencv-$OPENCV_VER \
    && apk del build-dependencies py3-numpy-dev  python3-dev \
    && rm -rf /var/cache/apk/*

# then deal with python libraries
COPY requirements.txt /tmp/
RUN apk add -U --virtual=build-dependencies \
    linux-headers musl libxml2-dev libxslt-dev libffi-dev \
    musl-dev libgcc openssl-dev jpeg-dev zlib-dev freetype-dev build-base \
    lcms2-dev openjpeg-dev make cmake gcc ninja \
    && apk add python3-dev~=$PYTHON_VERSION \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt \
    && apk del python3-dev build-dependencies \
    && rm -rf /var/cache/apk/*

# Copy root filesystem
COPY src /opt/bruderpy

# Script to run after startup
CMD ["python3","/opt/bruderpy/run.py"]

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_REF
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="BruderPy" \
    io.hass.description="Receives images from network enabled document scanners via webdav and runs OCR on them" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Gregor Godbersen <homeassistant@k9z.de>" \
    org.label-schema.description="Receives images from network enabled document scanners via webdav and runs OCR on them" \
    org.label-schema.build-date=${BUILD_DATE} \
    org.label-schema.name="BruderPy" \
    org.label-schema.schema-version="1.0" \
    org.label-schema.url="https://github.com/gregod/addon-bruderpy/tree/master/bruderpy" \
    org.label-schema.usage="https://github.com/gregod/addon-bruderpy/blob/master/bruderpy/README.md" \
    org.label-schema.vcs-ref=${BUILD_REF} \
    org.label-schema.vcs-url="https://github.com/gregod/addon-bruderpy/" \
    org.label-schema.vendor="Gregor Godbersen"
