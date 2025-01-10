import scrapy


class ContactsSpider(scrapy.Spider):
    name = "Contact_Updated"
    start_urls = [
        "https://www.bobrohrmanschaumburgford.com/staff.aspx",
            ]

    def parse(self, response):
        # Loop through each staff card and extract relevant info
        for staff in response.css("div.staff-card"):
            # Extract name
            name = staff.css("div.staff-title::text").get().strip()
            
            # Extract the description (e.g., "Service Manager")
            description = staff.css("div.staff-desc em::text").get()
            if description:
                description = description.strip()


            # Extract phone number from the "tel" href
            phone = staff.css("a[href^='tel']::attr(href)").get()
            if phone:
                phone = phone.replace("tel:", "").strip()

            # Extract email from the "mailto" href
            email = staff.css("a[href^='mailto']::attr(href)").get()
            if email:
                email = email.replace("mailto:", "").strip()

            # Yield the extracted data for each staff member
            yield {
                "name": name,
                "phone": phone,
                "staffDesciption": description,                
                "email": email,
            }
