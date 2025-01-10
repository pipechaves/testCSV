import scrapy
import re


class contactsSpider(scrapy.Spider):
    name = "contacts"
    start_urls  = [
        "https://www.bobrohrmanschaumburgford.com/staff.aspx",
    ]
        # "https://www.cellaride.com/",
        # "https://enterprise.com/",
        # "https://www.kengarff.com/",
        # "https://www.kengarff.com/contact-us/",
        # "https://www.audilehi.com/contact.htm",

    def parse(self, response):
        # Generic patterns for phone numbers, emails, and addresses
        phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

        phone = None
        email = None
        address = None
        
        text_elements = response.xpath("//text()").getall()

        # Search for phone number in 'tel' href first
        phone_href = response.css("a[href^='tel']::attr(href)").get()
        if phone_href:
            # Extract the actual number from the href, remove 'tel:' and any spaces
            phone = phone_href.replace("tel:", "").strip()

        # If no href, try to match a phone number from visible text
        if phone is None:
            for element in text_elements:
                element = element.strip()
                if phone_pattern.search(element):
                    phone = phone_pattern.search(element).group()
                    break

        # Search for email address using mailto href or visible text
        email_href = response.css("a[href^='mailto']::attr(href)").get()
        if email_href:
            email = email_href.replace("mailto:", "").strip()

        if email is None:
            for element in text_elements:
                element = element.strip()
                if email_pattern.search(element):
                    email = email_pattern.search(element).group()
                    break

        # # Try to locate an address using key terms
        # address_keywords = ["street", "avenue", "suite", "building", "pkwy", "blvd"]
        # for element in text_elements:
        #     if any(keyword.lower() in element.lower() for keyword in address_keywords):
        #         address = element.strip()
        #         break

        # Yield the extracted data
        yield {
            "phone": phone,
            "email": email,
            # "address": address,
        }
