# Preview (Product review) project
- Product review crawler and preprocessing with OCR and etc.

- Combine with honeycomb (Flask server + SQLAlchemy) and MySQL DB.
---------------


## Composition
### Driver
- Can use proxy IP if you have.
- Can changes the user-agent if you want.
- Failover process when crawler stops like IP banned Case.
------------------------------

### Route handler
- Error handling with retry pattern when fetch to the Webserver
- Define fetch url to Web server
------------------------------

### Image processing
- Use PaddleOCR to analyize product explanation by seller.
- Due to large size of the image, there is a image cutting logic without ignoring any characters.
- **TODO: multiprocessing would be added in this process.**
-------------------------------

### GUI
- Use GUI with tkinter to develop tagging tools.
- TWO TYPES
  1. OCR tagging
     - OCR tagging tools.
  2. Review tagging
     - Review tagging tools.
-------------------------------

### Crawler work at
  1. product_link_crawler.py
     - Crawling at naver shopping price comparsion tabs.
     - Crawl data and fetch to the server.

       
  2. review_crawler.py
     - Crawling at the product-unit price comparison page.
     - Get OCR data with PaddleOCR/
     - Get review data by json payloads.
     - Get spec data provided by naver.
     - Fetch to the server
---------------------------------


### Dockerfile (with only testing product_link_crawler.py)
