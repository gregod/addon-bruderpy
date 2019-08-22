ARG BUILD_FROM=homeassistant/base-python:3.0.1
# hadolint ignore=DL3006
FROM ${BUILD_FROM}


ENV TESSDATA_EN https://raw.githubusercontent.com/tesseract-ocr/tessdata/master/eng.traineddata
ENV TESSDATA_DE https://raw.githubusercontent.com/tesseract-ocr/tessdata/master/deu.traineddata
ENV OPENCV https://github.com/opencv/opencv/archive/4.1.1.tar.gz
ENV OPENCV_VER 4.1.1

# Copy install other python requirements from file
COPY requirements.txt /tmp/

# somehow squash is not working in build script
# therefore merge all in one layer
RUN apk add -U --no-cache --virtual=build-dependencies \
    linux-headers musl libxml2-dev libxslt-dev libffi-dev \
    musl-dev libgcc openssl-dev jpeg-dev zlib-dev freetype-dev build-base \
    lcms2-dev openjpeg-dev make cmake gcc ninja \
    && apk add --no-cache tesseract-ocr zlib jpeg libjpeg freetype openjpeg \
    && pip install --no-cache-dir numpy \
    && curl $TESSDATA_EN -o /usr/share/tessdata/eng.traineddata \
    && curl $TESSDATA_DE -o /usr/share/tessdata/deu.traineddata \
    && ln -s /usr/include/locale.h /usr/include/xlocale.h \
    && cd /opt && \
    curl -L $OPENCV | tar zx && \
    cd opencv-$OPENCV_VER && \
    mkdir build && cd build && \
    cmake   -G Ninja \
            -D CMAKE_BUILD_TYPE=RELEASE \
            -D BUILD_DOCS=OFF \
            -D BUILD_EXAMPLES=OFF \
            -D BUILD_PERF_TESTS=OFF \
            -D BUILD_TESTS=OFF \
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
            -D CMAKE_INSTALL_PREFIX=/usr/local \
            -D WITH_FFMPEG=NO \
            -D WITH_IPP=NO \
            -D PYTHON_EXECUTABLE=/usr/local/bin/python3 \
            -D WITH_OPENEXR=NO .. && \
    ninja && ninja install \
    &&  pip install --no-cache-dir -r /tmp/requirements.txt \
    && apk del build-dependencies && \
    rm -rf /var/cache/apk/* && \
    rm -rf /opt/opencv-$OPENCV_VER

# Copy root filesystem
COPY rootfs /

# Script to run after startup
CMD ["/usr/bin/run.py"]

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
