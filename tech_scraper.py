from bs4 import BeautifulSoup
import urllib2
import re
import csv

def get_soup(url):
    '''
    This is a helper function which just spits out the soup for a URL.
    Saves a couple lines, right?  Why not.
    '''
    page = urllib2.urlopen(url)
    return BeautifulSoup(page.read())

def get_issue_links():
    '''
    This function iterates through all the Volume pages going back through 1990
    and returns a list of all the Issue links contained on each one.  
    '''

    # First, build a list of every volume url from Volume 109 (1990) to 135 (2015).
    url_base = 'http://tech.mit.edu/V'
    volume_urls = []
    for i in range(109,136):
        volume_urls.append(url_base+str(i)+'/')

    # Then, open each of their soups and add all the issue tags to a list.
    issue_tags = []
    for volume_url in volume_urls:
        volume_soup = get_soup(volume_url)
        issue_tags.extend(list(volume_soup.find_all('a', text=re.compile('Issue'))))

    # Now, to make life easier later on, go through each of these tags and
    # convert it into an actually useful link.
    issue_urls = []
    for tag in issue_tags:
        tag = str(tag)
        
        # Grab characters [11:19] from the <a> tag to get the part of the link we
        # want.  General solution?  No.  Functional solution?  YES.
        clean_url = url_base+tag[11:19]

        # Downside of a sketchy solution is that you need sketchy cleanup.
        # This if statement handles the special case of issue numbers less than 10.
        if clean_url[-1] == '"':
            clean_url = clean_url[:-1]

        # Anyways, actually append this now-clean url to the list.
        issue_urls.append(clean_url) 
    
    # Finally, return our big ol' list of urls.
    return issue_urls

def build_headline_list():
    '''
    This function builds a list of tuples, where each tuple has the format:
    
    (headline_text, headline_link, headline_date)

    and returns the list to the user.  Gotta love web scraping.
    '''

    # First, get ALL OF THE LINKS to ALL OF THE ISSUES.
    issue_urls = get_issue_links()
    headline_list = []

    #Now, for each url in the list...
    for issue_url in issue_urls:

        # Start doing everything in a try block -- for some reason BeautifulSoup
        # fails on Vol 117 Issue N43 and Vol 124 Issue 38.  It seemed easier to
        # just let the script skip them.
        try:

            # Grab the main div, so we can ignore navigation links... 
            issue_soup = get_soup(issue_url)
            main_div = issue_soup.div(id='main')

            # ... and start going through all of its tags.
            for tags in main_div:

                # Let's grab all the <a>s!
                main_links = tags.find_all('a')
                
                # Then get the publication date and clean it up a little.
                pub_date = main_links[1].text
                pub_date = pub_date[pub_date.index(':')+2:]

                # Now, for all of the actual article links...
                for article_link in main_links[3:]:
                    try:

                        # Add in the (headline, url, date) tuple to our headline list.
                        headline_list.append((article_link.text, issue_url+article_link['href'][0:], pub_date))
                    except KeyError:
                        print "Headline append failed for this tag: " + article_link
        except Exception:
            print "Issue souping failed for this issue URL: " + issue_url

    # Finally, print something pretty for the user and return the list of headlines.
    print "Just finished collecting all of the headlines printed in The Tech from the year 1990 to now."
    print "There were " + str(len(headline_list)) + " headlines found in total."
    return headline_list

if __name__ == '__main__':
    '''
    This is what actually runs.  It gets all the headline tuples, 
    then writes 'em to a .csv. Fun, fun, fun.
    '''
    headlines = build_headline_list()

    with open('headlines.csv', 'wb') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['Headline Text', 'Headline Link', 'Headline Date'])
        for row in headlines:
            csv_out.writerow([unicode(s).encode('utf-8') for s in row])