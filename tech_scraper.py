from bs4 import BeautifulSoup
import urllib2
import re
import csv

KEYWORDS = ['death', 'died', 'dead', 'suicide', 'dies', 'kills himself', 'kills herself', 'takes life']

def get_soup(url):
    '''
    This is a helper function which just spits out the soup for a URL.
    Saves a couple lines, right?  Why not.
    '''
    try:
        page = urllib2.urlopen(url)
        return BeautifulSoup(page.read())
    except Exception:
        try:
            url_plus = url + '.html'
            page = urllib2.urlopen(url_plus)
            return BeautifulSoup(page.read())
        except Exception:
            print "URL {0} could not be opened.".format(url)
            return None

def get_issue_links():
    '''
    This function iterates through all the Volume pages going back through 1990
    and returns a list of all the Issue links contained on each one.  
    '''

    # First, build a list of every volume url from Volume 109 (1990) to 135 (2015).
    url_base = 'http://tech.mit.edu'
    volume_urls = []
    for i in range(109,136):
        volume_urls.append(url_base+'/V'+str(i)+'/')

    # Then, open each of their soups and add all the issue tags to a list.
    issue_tags = []
    for volume_url in volume_urls:
        volume_soup = get_soup(volume_url)
        issue_tags.extend(list(volume_soup.find_all('a', text=re.compile('Issue'))))

    # Now, to make life easier later on, go through each of these tags and
    # convert it into an actually useful link.
    issue_urls = []
    for tag in issue_tags:

        # Use BeautifulSoup's property reference system to get the 'href', add
        # it onto the tech.mit.edu link base and we're, ready to rock!
        clean_url = url_base + tag['href']
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
    url_base = 'http://tech.mit.edu'

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

                        # Check if the href already includes the '/V###/N##' part.
                        prefixed = len(re.compile('^/V[\d]+/N[\d]+').findall(article_link['href'])) > 0

                        # Filter out the author URLs.
                        if len(re.compile('/author/').findall(article_link['href'])) > 0:
                            continue

                        # If it does, add the href onto the url_base.  If not, add the href to the issue_url.
                        if prefixed:
                            article_url = url_base + article_link['href']
                        else:
                            article_url = issue_url + article_link['href']

                        # Finally, append the article onto our big list.
                        headline_list.append((article_link.text, article_url, pub_date))
                    except KeyError:
                        print "Headline append failed for this tag: " + article_link
        except Exception:
            print "Issue souping failed for this issue URL: " + issue_url

    # Finally, print something pretty for the user and return the list of headlines.
    print "Just finished collecting all of the headlines printed in The Tech from the year 1990 to now."
    print "There were " + str(len(headline_list)) + " headlines found in total."
    return headline_list

def get_filtered_articles(headline_list):
    '''
    Filters through a list of headline tuples, where each tuple is (headline_text, headline_url, publication_date).
    Draws from a global KEYWORDS variable to filter through each headline, returning a list of all headlines
    which contained a keyword from the list.
    '''

    # Make a list to store all the desired headlines.
    filtered_list = []

    # And start iterating through the headlines...
    print "About to start filtering through {0} articles, searching for ones which contain any of these keywords: {1}".format(str(len(headline_list)), KEYWORDS)
    print "..."
    for headline_entry in headline_list:

        # Grab the text out of each one and rip it into lowercase words with a regex & a list comprehension.
        (headline, url, date) = headline_entry
        if (filter_article(url) == True):
            filtered_list.append(headline_entry)

    # And round it all up by returning that list.
    print "Found {0} articles total -- returning now.".format(str(len(filtered_list)))
    return filtered_list

def filter_article(article_url):
    '''
    Performs the filtering on articles to check if the headline or text contains any of our KEYWORDS.
    If they do, this returns True.  If not, it returns False.
    '''
    # First, make sure this link isn't to an image.
    if article_url[-3:] in ['gif', 'jpg']:
        return False

    article_soup = get_soup(article_url)
    if article_soup is None:
        print "The soup for article {0} didn't work, filtered it out.".format(article_url)
        return False
    else:
        try:
            main_div = article_soup.div(id='main')
            words = set([word.lower() for word in re.compile('\w+').findall(str(main_div))])
            return len([word for word in KEYWORDS if word in words]) > 0
        except Exception as e:
            print "Exception: ",e
            print "The URL being filtered was: {0}".format(article_url)

def write_to_csv(heading_list, entry_list, filename):
    '''
    This method encapuslates all the logic behind writing a .csv given a heading row,
    list of entries, and an output filename.
    '''

    # Open up a context with the file.
    with open(filename, 'wb') as out:

        # Make a csv writer and add in the header row.
        csv_out = csv.writer(out)
        csv_out.writerow(heading_list)

        # Finally, write all the rows!  The list comprehension makes sure any screwy
        # characters get converted over into unicode.
        print "Writing {0} rows to {1}.".format(str(len(entry_list)), filename)
        for row in entry_list:
            csv_out.writerow([unicode(s).encode('utf-8') for s in row])

if __name__ == '__main__':
    '''
    This is what actually runs.  It gets all the headline tuples, 
    then writes 'em to a .csv. Fun, fun, fun.
    '''
    all_headlines = build_headline_list()
    filtered_headlines = get_filtered_articles(all_headlines)
    write_to_csv(['Headline', 'URL', 'Date'], filtered_headlines, 'filtered_headlines.csv')
    # print re.compile('^/V[\d]+/N[\d]+').findall("/V119/N46/Our_Lady_Peace.46a.html")