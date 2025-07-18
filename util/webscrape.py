import re
import json
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

url = "https://www.remotepython.com/jobs/"
response = requests.get(url)
soup = BeautifulSoup(response.text, "lxml")
results = []
# first find all job listing boxes:
job_listing_boxes = soup.find_all(class_="item")
# then extract listing from each box:
for item in job_listing_boxes:
    parsed = {}
    if title := item.find("h3"):
        parsed["title"] = title.get_text(strip=True)
    if item_url := item.find("h3").a["href"]:
        parsed["url"] = urljoin(url, item_url)
    if company := item.find("h5").find("span", class_="color-black"):
        parsed["company"] = company.text
    if location := item.select_one("h5 .color-white-mute"):
        parsed["location"] = location.text
    if posted_on := item.find("span", class_="color-white-mute", string=re.compile("posted:", re.I)):
        parsed["posted_on"] = posted_on.text.split("Posted:")[-1].strip()
    results.append(parsed)

print(results[0]['url'])
#for i in range(len(results)):
url2 = results[0]['url']
response2 = requests.get(url2)
#print(url2)
soup2 = BeautifulSoup(response2.text, "lxml")
#print(soup2)
job_div = soup2.find("div", class_="block-section box-item-details")
#print(job_div)
# Extract all paragraphs and join them with newlines
job_description = "\n\n".join(p.get_text(separator=" ", strip=True) for p in job_div.find_all("p"))
print(job_description)
[{
    "title": "Hiring Senior Python / DJANGO Developer",
    "url": "https://www.remotepython.com/jobs/3edf4109d642494d81719fc9fe8dd5d6/",
    "company": "Mathieu Holding sarl",
    "location": "Rennes, France",
    "posted_on": "Sept. 1, 2022"
  },
  ...  # etc.
]