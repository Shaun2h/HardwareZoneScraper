# Scraper, Hardwarezone.

forum_eater.py generates a json which lists all the available threads in your target forum.

- Might have issues with getting ALL participants in reaction page. 

(Type isn't a big problem, the issue is I couldn't find a post sample with a lot of reactions so much that it might need multiple pages. So i won't be able to catch that case.)

- Contains Geckodriver for reference. Use exactly that one.

- Firefox version: 100.0.2 (64-bit)

- Versions are sensitive. Marionette is not stable a little before and after the version at times.

- Selenium == 4.1.3  
    - Accept no substitutes.