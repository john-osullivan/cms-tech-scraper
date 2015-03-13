from bs4 import BeautifulSoup
import urllib2

url = 'http://www.tech.mit.edu/V135'
proxy_handler = urllib2.ProxyHandler({})
opener = urllib2.build_opener(proxy_handler)
page = urllib2.urlopen(url)

tech_soup = BeautifulSoup(page.read())
links = tech_soup.find_all('a')

print links