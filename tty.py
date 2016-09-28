import urllib.request, sys, queue, threading, time, os
from html.parser import HTMLParser


def get_source(url):
    try:
        with urllib.request.urlopen(url) as u:
            html = u.read()
            return html
    except urllib.error.HTTPError:
        print("HTTP Error 404: Not Found:", url)
        page_error.append(url)

def saver():
    global pics_downloaded
    global changed_file_name
    global same_file_length
    while q.qsize() > 0:
        data = q.get()
        i = data["url"]
        if "=" in i:
            i = urllib.request.url2pathname(i)
            i = i.split("=")[-1]
        if "http" not in i:
            i = "http://" + i
        try:
            img = urllib.request.urlopen(i)
        except urllib.error.HTTPError:
            print("HTTP Error 404: Not Found:", i)
            img_error.append(i)
        else:
            file_name = img.info()["Content-Disposition"]
            if file_name == None:
                o = urllib.request.url2pathname(i)
                file_name = o.split("/")[-1]
                file_name = file_name + ".jpg"
            else:
                file_name = file_name.split('"')[1]
                file_name = urllib.request.url2pathname(file_name)
            if data["date"] == None:
                data["date"] = "No Title"
            if organize == True:
                img_path = os.path.join(data["date"], file_name)
                if not os.path.exists(data["date"]):
                    os.makedirs(data["date"])
            else:
                img_path = file_name
            while True:
                if not os.path.exists(img_path):
                    print("Downloading: %s" % (i))
                    imglink = open(img_path, "wb")
                    imglink.write(img.read())
                    imglink.close()
                    pics_downloaded += 1
                    break
                else:
                    nonlocal_img = img.info()["Content-Length"]
                    with open(img_path, "rb") as f:
                        local_img = len(f.read())
                        f.close()
                    if int(nonlocal_img) != int(local_img):
                        file_name = file_name.split(".jpg")[0]
                        file_name = file_name + "I" + ".jpg"
                        if not os.path.exists(file_name):
                            changed_file_name += 1
                    else:
                        same_file_length += 1
                        break

def thread_starter():
    t = threading.Thread(target=saver)
    t.start()

link_listg = []
class PicLinks(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.title_check = False
        self.title = ""
        self.title_dict = {}

    def handle_starttag(self, tag, attrs):
        # Tistory
        if tag == "meta":
            for name, value in attrs:
                if value == "og:title":
                    self.title_check = True

                if name == "content" and self.title_check == True:
                    self.title = value
                    self.title_check = False

        if tag == "img":
            for name, value in attrs:
                if name == "src" and "tistory.com" in value:
                    l = value.replace("image", "original")
                    self.title_dict["date"] = self.title
                    self.title_dict["url"] = l
                    if self.title_dict not in link_listg:
                        link_listg.append(self.title_dict.copy())
        # Imgur
        if tag == "a":
            for name, value in attrs:
                if ".jpg" in value:
                    l = value.replace("//", "")
                    link_listg.append(l)


url = sys.argv[1].replace(" ", "")
number_of_threads = 12
number_of_pages = []
multiple_pages = False
organize = False
changed_file_name = 0
same_file_length = 0
pics_downloaded = 0
img_error = []
page_error = []
q = queue.Queue()

for opt in sys.argv[1:]:
    if opt == "-help":
        print(
        "   Download images from a specific tistory page\n"
        "   >tty http://idol-grapher.tistory.com/140\n\n"
        "-p\n"
        "   Download images from multiple pages\n\n"
        "   To download images from page 140 to 150\n"
        "   >tty http://idol-grapher.tistory.com/ -p 140-150\n\n"
        "   To download images from page 1, 2 and 3\n"
        "   >tty http://idol-grapher.tistory.com/ -p 1,2,3\n\n"
        "   To download images from page 1, 2, 3, 5 to 10 and 20 to 25\n"
        "   >tty http://idol-grapher.tistory.com/ -p 1,2,3,5-10,20-25\n\n"
        "-t\n"
        "   Specify number of simultaneous downloads (default is 12)\n"
        "   >tty http://idol-grapher.tistory.com/140 -t 12\n\n"
        "-o\n"
        "   Organize images by title (might not work, it's unpredictable)\n"
        "   >tty http://idol-grapher.tistory.com/140 -o\n\n"
        )
        sys.exit()
    elif opt == "-p":
        multiple_pages = True
        p_num = sys.argv[sys.argv.index("-p") + 1]
        digit_check = p_num.replace(",", " ")
        digit_check = digit_check.replace("-", " ").split(" ")
        for digit in digit_check:
            if not digit.isdigit():
                print(
                "   -p can only accept digits\n"
                "   >tty http://idol-grapher.tistory.com/ -p 1,2,5-10"
                )
                sys.exit()

        p_num = p_num.split(",")
        for num in p_num:
            if "-" in num:
                first_num = num.split("-")[0]
                second_num = num.split("-")[1]
                total_num = int(second_num) - int(first_num)
                for new_num in range(total_num + 1):
                    number_of_pages.append(new_num + int(first_num))
            else:
                number_of_pages.append(num)

    elif opt == "-t":
        t_num = sys.argv[sys.argv.index("-t") + 1]
        if t_num.isdigit() and int(t_num) > 0 and int(t_num) < 61:
            number_of_threads = t_num
        else:
            print(
            "   Threads(-t) needs to be a number in between 1-60\n\n"
            "   >tty http://jjtaeng.tistory.com/244 -t 3\n"
            )
            sys.exit()
    elif opt == "-o" or opt == "-organize":
        organize = True

def work_page():
    while q.qsize() > 0:
        multi_url = q.get()
        print(multi_url)
        html = get_source(multi_url)
        if html != None:
            PicLinks().feed(html.decode("utf-8"))

if multiple_pages == True:
    number_of_pages.sort(key=int)
    print("Fetching source for:")
    if url[-1] != "/":
        url = url + "/"
    for page in number_of_pages:
        multi_url = url + str(page)
        q.put(multi_url)
        
    page_threads = [threading.Thread(target=work_page) for i in range(2)]
    for thread in page_threads:
        thread.start()
    for thread in page_threads:
        thread.join()
else:
    print("Fetching page source...")
    html = get_source(url)
    if html != None:
        PicLinks().feed(html.decode("utf-8"))
    else:
        sys.exit()
link_list = link_listg
for x in link_list:
    q.put(x)
if int(number_of_threads) > q.qsize():
    number_of_threads = q.qsize()
total_found = q.qsize()
print("\nStarting download:")

img_threads = [threading.Thread(target=saver) for i in range(int(number_of_threads))]
for thread in img_threads:
    thread.start()
for thread in img_threads:
    thread.join()

msg_total = (
" Scraper found %s image%s." %
(total_found,
"s" if total_found > 1 else "",
))
msg_dl = (
" %s saved%s" %
(pics_downloaded,
"." if same_file_length <= 0 else ",",
))
msg_length = (
" %s already existed and did not save." %
(same_file_length,
))
print("Done!%s%s%s" % (
msg_total if total_found > 0 else " Scraper could not find any images.",
msg_dl if pics_downloaded > 0 else "",
msg_length if same_file_length > 0 else "",
))
if len(page_error) > 0:
    print(
    "\n%s page%s did not load." % (
    len(page_error),
    "s" if len(page_error) > 1 else "",
    ))
    for x in page_error:
        print(x)
if len(img_error) > 0:
    print(
    "\n%s image%s did not load." % (
    len(img_error),
    "s" if len(img_error) > 1 else "",
    ))
    for x in img_error:
        print(x)
