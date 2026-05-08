from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# just check if something is wrong with the page
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
driver.get("file:///Users/sushanthsiddanna/jarvis_project/ui/index.html")
print(driver.page_source[:500])
driver.quit()
