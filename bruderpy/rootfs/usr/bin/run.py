#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from datetime import datetime
import threading
import os
from queue import Queue
import pytesseract
from PIL import Image
import re
import cv2
import numpy
import xml.etree.ElementTree as ET
import dateparser
import json

from thumbnailer import cropped_thumbnail

logging.basicConfig(level=logging.INFO)

output_folder = "/data/scans"
tess_language = "deu"
labels = {
    "_AUTO_DATED" : "rgb(252,175,62)",
    "_UN_DATED" : "rgb(252,175,61)"
}


class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_PROPFIND(self):
        if str(self.path).endswith("/"):
            return_string = """<D:multistatus xmlns:D="DAV:" xmlns:Z="urn:schemas-microsoft-com:">
            <D:response>
            <D:href>/</D:href>
            <D:propstat>
            <D:prop>
              <D:name/>
              <D:getcontentlength/>
              <D:iscollection>1</D:iscollection>
              <D:isroot>1</D:isroot>
              <D:resourcetype><D:collection/></D:resourcetype>
            </D:prop>
            <D:status>HTTP/1.1 200 OK</D:status>
            </D:propstat>
            </D:response>
            </D:multistatus>""".encode("utf-8")
            self.send_response(207)
            self.send_header('Content-type', 'text/xml')
            self.send_header('Content-length', len(return_string))
            self.end_headers()
            self.wfile.write(return_string)

            start_new_scan()

        elif "/_TEST_FILE_" in str(self.path):
            # test file from setup
            self.send_response(404)
            self.send_header('Content-type', 'text/xml')
            self.end_headers()

    def do_LOCK(self):
        global  scan_completed_timer
        return_string = """<?xml version="1.0" encoding="utf-8" ?>
        <d:prop xmlns:d="DAV:">
          <d:lockdiscovery>
            <d:activelock>
              <d:locktype><d:write/></d:locktype>
              <d:lockscope><d:exclusive/></d:lockscope>
              <d:depth>Infinity</d:depth>
              <d:owner>
                <d:href>http://localhost/user</d:href>
              </d:owner>
              <d:timeout>Second-345600</d:timeout>
              <d:locktoken>
                <d:href>opaquelocktoken:this-is-not-a-real-lock</d:href>
              </d:locktoken>
            </d:activelock>
          </d:lockdiscovery>
        </d:prop>""".encode("utf-8")
        self.send_response(200)
        self.send_header('Content-type', 'text/xml')
        self.send_header('Content-length', len(return_string))
        self.end_headers()
        self.wfile.write(return_string)

        # this is a new file, so cancel the timer again
        if scan_completed_timer is not None and scan_completed_timer.is_alive():
            scan_completed_timer.cancel()



    def do_UNLOCK(self):
        global scan_completed_timer
        self.send_response(200)
        self.end_headers()
        # unlock is done after file is completed
        # now wait for next page,
        scan_completed_timer = threading.Timer(3.0, finish_scan)
        scan_completed_timer.start()

    def do_DELETE(self):
        # only happens in test for setup
        # or if something went wrong
        self.send_response(200)
        self.end_headers()

    def do_PUT(self):
        global current_scan
        logging.debug("Getting File...")


        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data

        if content_length > 0:

            if current_scan is None:
                logging.warning("Tried to scan without current scan")
                start_new_scan()

            # cant be named num.original.jpg, this messes up gui
            current_file_name = os.path.join(current_scan["folder_name"], "paper.{}.original.jpg_bak".format(current_scan["current_page"]))

            with open(current_file_name,"wb") as imgfile:
                read = 0
                while read < content_length:
                    buffer = self.rfile.read(1024)
                    if not buffer:
                        break
                    imgfile.write(buffer)
                    read += len(buffer)
                if read > content_length:
                    logging.error("Read more data than content length")
                    return

            current_scan["current_page"] += 1


        self._set_response()


def run_server(server_class=HTTPServer, handler_class=S, port=8000):
    global worker_queue
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    handler_class.rbufsize = 0
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        worker_queue.put("QUIT")
    httpd.server_close()
    logging.info('Stopping httpd...\n')


def worker():
    global worker_queue, labels
    logging.info("Starting Worker")

    while True:
        work_item = worker_queue.get()
        if work_item == "QUIT":
            logging.info("Stopping Worker...")
            break

        logging.info("Processing document ...")
        file_labels = []

        for i in range(1, work_item["current_page"]):

            original_input_jpg = os.path.join(work_item["folder_name"], "paper.{}.original.jpg_bak".format(i))
            input_jpg = os.path.join(work_item["folder_name"], "paper.{}.jpg".format(i))

            img = Image.open(original_input_jpg)
            orig_info = img.info  # extract metadata
            img = numpy.array(img)
            text_page = True
            try:
                # find text orientation
                tess_output = re.search(r'Rotate: (\d*)', pytesseract.image_to_osd(img, lang=tess_language))
                # rotate image according to tesseract output
                if tess_output is not None and tess_output.group(1) != "0":
                    angle = int(tess_output.group(1))
                    if angle == 90:
                        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    elif angle == 180:
                        img = cv2.rotate(img, cv2.ROTATE_180)
                    elif angle == 270:
                        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            except:
                text_page = False
                logging.warning("Error finding tesseract orientation;")
            
            try:
              # then deskew
              img = deskew(img)
            except:
              logging.warning("Error deskewing image")

            # restore original image info
            img = Image.fromarray(img)
            img.info = orig_info

            # write page
            img.save(input_jpg)

            if text_page:
                # generate hocr file
                hocr = (pytesseract.image_to_pdf_or_hocr(img, lang=tess_language, extension="hocr"))
                hocr_file_path = os.path.join(work_item["folder_name"], "paper.{}.words".format(i))
                with open(hocr_file_path, "wb") as hocr_file:
                    hocr_file.write(hocr)




            # generate thumbnails
            # must be exact size or they get regenerated by paperworks
            thumbnail = cropped_thumbnail(img.copy(), (150, 212))
            thumbnail.save(os.path.join(work_item["folder_name"], "paper.{}.thumb.jpg".format(i)))
            logging.info("Finished file...")


        # try to guess date
        try:
            logging.info("Guessing date...")
            # get first page with hocr file
            first_page_hocr = next(filter(
                lambda path: os.path.exists(path),
                map(
                    lambda num : os.path.join(work_item["folder_name"], "paper.{}.words".format(num)),
                    range(1, work_item["current_page"])
                )))

            dates = find_promising_dates(first_page_hocr)

            # when we havent found anything on the first page,
            # check the last page, maybe scanned in wrong order
            if len(dates) == 0:
                last_page_hocr = next(filter(
                    lambda path: os.path.exists(path),
                    map(
                        lambda num: os.path.join(work_item["folder_name"], "paper.{}.words".format(num)),
                        range(work_item["current_page"] - 1, 0, -1)
                    )))
                dates = find_promising_dates(last_page_hocr)
            seen_dates = {}
            deduped_dates = [seen_dates.setdefault(x, x) for x in dates if x not in seen_dates]

            if len(deduped_dates) > 1:
                logging.info("Found more than one date candidate")
            elif len(deduped_dates) == 0:
                logging.warning("No date found")

            # if we have at least one date, take the first (roughly topmost)
            if len(deduped_dates) > 0:
                date_str = deduped_dates[0].strftime('%Y%m%d_%H%M_%S')
                logging.info("Using found date %s",date_str)
                # find unused folder that matches dates
                base_folder = os.path.join(output_folder,date_str)
                valid_path = base_folder
                folder_counter = 1
                while os.path.exists(valid_path):
                    valid_path = "{}_{}".format(base_folder, folder_counter)
                    folder_counter += 1

                logging.info("Renaming %s to %s",work_item["folder_name"], valid_path)
                # actually rename folder
                os.rename(work_item["folder_name"], valid_path)
                work_item["folder_name"] = valid_path
        except:
            logging.error("Error in guessing date, continuing")
            pass

        try:
            # store document labels in file
            if len(file_labels) > 0:
                labels_file_path = os.path.join(work_item["folder_name"], "labels")
                with open(labels_file_path, "w") as label_file:
                    for label in file_labels:
                        if label in labels:
                            label_file.write("{},{}".format(label, labels[label]))
                        else:
                            label_file.write("{},{}".format(label, "rgb(0,0,0)"))
        except:
            logging.error("Error setting labels, continuing")
            pass

        logging.info("Finished processing document!")
        worker_queue.task_done()


# start the local worker thread
def run_worker_loop():
    x = threading.Thread(target=worker)
    x.start()


worker_queue = Queue()
current_scan = None
scan_completed_timer = None


def start_new_scan():
    global current_scan
    if current_scan is not None:
        logging.error("Tried to Start Scan when there was already scan active")
        finish_scan() # try to finish the broken scan

    # create new scan state

    # find non existing folder
    base_folder = os.path.join(output_folder,datetime.today().strftime('%Y%m%d_%H%M_%S'))
    valid_path = base_folder
    folder_counter = 1
    while os.path.exists(valid_path):
        valid_path = "{}_{}".format(base_folder, folder_counter)
        folder_counter += 1

    current_scan = {
        "folder_name" : valid_path,
        "current_page" : 1
    }
    # and create matching folder
    os.mkdir(current_scan["folder_name"])


def finish_scan():
    global scan_completed_timer, current_scan,worker_queue
    logging.info("Finishing Scan")
    # cancel running timer, put scan state in working queue and reset scan state
    if scan_completed_timer is not None and scan_completed_timer.is_alive():
        scan_completed_timer.cancel()
    worker_queue.put(current_scan)
    current_scan = None


def deskew(im, max_skew=10):
    height = im.shape[0]
    width = im.shape[1]

    # Create a grayscale image and denoise it
    im_gs = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im_gs = cv2.fastNlMeansDenoising(im_gs, h=3)

    # Create an inverted B&W copy using Otsu (automatic) thresholding
    im_bw = cv2.threshold(im_gs, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # Detect lines in this image. Parameters here mostly arrived at by trial and error.
    lines = cv2.HoughLinesP(
        im_bw, 1, numpy.pi / 180, 200, minLineLength=width / 12, maxLineGap=width / 150
    )

    # Collect the angles of these lines (in radians)
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angles.append(numpy.arctan2(y2 - y1, x2 - x1))

    angles = [angle for angle in angles if abs(angle) < numpy.deg2rad(max_skew)]

    if len(angles) < 5:
        # Insufficient data to deskew
        return im

    # Average the angles to a degree offset
    angle_deg = numpy.rad2deg(numpy.median(angles))

    M = cv2.getRotationMatrix2D((width / 2, height / 2), angle_deg, 1)
    im = cv2.warpAffine(im, M, (width, height), borderMode=cv2.BORDER_REPLICATE)
    return im


def find_promising_dates(file_name):
    def get_bbox(title):
        return list(map(int, re.search(r'bbox (\d* \d* \d* \d*)', title).group(1).split(' ')))

    root = ET.parse(file_name)

    # find the bbox of the first page (dinA4)
    page_title = \
        root.findall('./{http://www.w3.org/1999/xhtml}body/{http://www.w3.org/1999/xhtml}div[@class="ocr_page"]')[0].get(
            "title")
    page_bbox = get_bbox(page_title)

    # now find all ocr_lines
    lines = root.findall('.//*[@class="ocr_line"]')

    def parse(bbox, text):
        # bbox =  x0 y0 x1 y1

        # only consider dates within the first 40% of the page,
        # likely the letterhead
        if bbox[1] < page_bbox[3] * 0.40:
            date = dateparser.parse(text, languages=['de'])
            if date is not None:
                return date

            # try simple regex heuristic to guide date parser
            # its bad at finding dates with much text around it
            # so these regexes do some fuzzy matching first, then
            simple_heuristics = [
                r'\d{4}-\d{2}-\d{2}',  # iso yyyy-mm-dd
                r'\d{1,2}[ \.\-\/]\d{1,2}[ \.\-\/]((20\d{2})|\d{2}(\D|$))',  # mostly dd.mm.20yy
                r'\d{1,2}[ \.]{1,2}\w{3,22}[ \.]{1,2}((20\d{2})|\d{2}(\D|$))',  # mostly dd written_month 20yy
                r'\w{3,10}\.? \d{4}'  # lastly check written_month yyyy
            ]
            for heuristic in simple_heuristics:
                date_match = re.search(heuristic, text)
                if date_match is not None:
                    date = dateparser.parse(date_match.group(), languages=['de'])
                    if date is not None:
                        return date

    date_candidates = []
    for line in lines:
        bbox = get_bbox(line.get("title"))

        # clean up word spacings
        words = [str(s).replace("\n", "") for s in line.itertext()]
        words = [s.strip() for s in words if len(s.strip()) > 0]
        merged_line = " ".join(words)

        date = parse(bbox, merged_line)
        if date is not None:
            date_candidates.append(date)

    return date_candidates

# load config from json
config = {}
with open("/data/options.json", 'r') as f:
       config = json.load(f)
if not os.path.exists(output_folder):
    os.mkdir(output_folder)

run_worker_loop()
run_server(port = 8080)
