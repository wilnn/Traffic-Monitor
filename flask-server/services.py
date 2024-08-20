import bs4
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import time

class Scrape:
    def __init__(self, url):
        self.url = url
    def scrape(self):

        option = webdriver.ChromeOptions()
        option.add_argument("--headless=new")
        service = webdriver.ChromeService(executable_path = 'C:/Users/thang/chromedriver-win64/chromedriver.exe')
        driver = webdriver.Chrome(service=service, options=option)
        try:
            driver.get(self.url)
        except WebDriverException:
            return "Page retrieval failed."
        time.sleep(5)
        data = driver.page_source
        driver.quit()
        
        soup = bs4.BeautifulSoup(data, "html.parser")
        return soup
    
    def getModifiedHTML(self, soup):
        #soup = bs4.BeautifulSoup(soup, "html.parser")
        imgs = soup.find_all('img')
        for img in imgs:
            img['src'] = 'placeholer.png'
        
        aTags = soup.find_all('a')
        for index, aTag in enumerate(aTags):
            del aTag['href']
        
        style = soup.find_all('style')
        styleTag = ''.join(str(tag) for tag in style)
        
        css = soup.find_all('link', rel='stylesheet')
        cssTag = ''.join(str(tag) for tag in css)
        '''for tag in css:
            cont = requests.get(tag['href'])
            cssContent += cont.text'''
        text = []
        indeces = []
        #content = list(html.find_all(string=True))
        content = list(soup.descendants)
        #filter to get only the text in the content list
        for index, value in enumerate(content):
            if type(value) == bs4.element.NavigableString and not value.isspace():
                s = value.strip()
                if len(s) > 0:
                    if s[0].isspace():
                        s = s[1:]
                        
                if len(s) > 0:
                    if s[-1].isspace():
                        s = s[:-1]
                #print("'" + s +"'")
                #indeces.append(index)
                value.wrap(soup.new_tag("span"))
                value.parent['id'] = str(index)
                #this.id return the id of the tag that the function is inside the onclick of
                value.parent['onclick'] = "changeColor(this.id)"
                value.parent['class'] = "change"
                value.parent.string = s
                
        newTag = soup.new_tag('script', src='./viewpage.js')
        soup.head.append(newTag)
        newTag = soup.new_tag('script', src='./viewpage.js')

        newTag = soup.new_tag('link')
        newTag['href'] = './viewpage.css'
        newTag['rel'] = 'stylesheet'
        soup.head.append(newTag)

        button = soup.new_tag('button')
        # Set attributes for the button
        button['onclick'] = 'sendSelected()'
        button['class'] = 'button'
        button.string = 'Finish'
        newtag = soup.new_tag('div')
        newtag['style'] = 'position: fixed; z-index: 9999; text-align:center;'
        newtag.append(button)
        # Insert the button at the beginning of the body tag
        soup.body.insert(0, newtag)

        newTag = soup.new_tag('style')
        newTag.string = '.change:hover { background-color: #ffff80; color: black}'
        soup.head.append(newTag)
        return soup
'''
d = Scrape('https://stackoverflow.com/questions/66546886/pip-install-stuck-on-preparing-wheel-metadata-when-trying-to-install-pyqt5')

a = d.scrape()
print(a)
b = d.getModifiedHTML(a)
print(b)
'''