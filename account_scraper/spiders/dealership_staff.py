import scrapy
import html
import re


class DealershipStaffSpider(scrapy.Spider):
    name = "dealership_staff"
    start_urls = [
        "https://www.garveyhyundai.com/staff.aspx",
        "https://www.richardsonford.net/staff.aspx",
        "https://www.interstatetoyota.net/staff.aspx",
        "https://www.toyotaofstamford.com/dealership/staff.htm",
        "https://www.billknightford.com/staff.aspx"
    ]
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Deduplication set
    seen_staff = set()

    def decode_cloudflare_email(self, protected_email):
        try:
            key = int(protected_email[:2], 16)
            decoded_email = ''.join(
                chr(int(protected_email[i:i+2], 16) ^ key)
                for i in range(2, len(protected_email), 2)
            )
            return html.unescape(decoded_email)
        except Exception as e:
            self.logger.error(f"Error decoding email: {e}")
            return None

    def parse(self, response):
        staff_links = response.xpath(
            '//a[contains(text(), "Staff") or contains(text(), "Team") or contains(@href, "staff") or contains(@href, "about-us")]/@href'
        ).extract()

        for link in staff_links:
            full_link = response.urljoin(link)
            if "staff" in full_link or "about-us" in full_link:
                yield scrapy.Request(full_link, callback=self.parse_staff_page)

    def parse_staff_page(self, response):
        # Handle primary structures
        
        staff_items = response.xpath(
            '//li[contains(@class, "staff-item")] | '
            '//div[contains(@class, "staff-entry")] | '
            '//div[contains(@class, "employee-row")] | '
            '//div[contains(@class, "staff-card")] | '
            '//div[contains(@class, "employee") and @data-profile-row]'  # Match employees with data-profile-row attribute
        )
        
        if staff_items:
            for index, staff in enumerate(staff_items):
                name = staff.xpath(
                    './/h3[contains(@class, "employee__name")]/strong/text() | '
                    './/h3[contains(@class, "employee__name")]/text() | '
                    './/h3/text() | '
                    './/div[contains(@class, "staff-title")]/text() | '
                    './/div[contains(@class, "name")]/text() | '
                    './/@data-dotagging-affiliation'
                ).get()
                
                if not name.strip():
                    name = staff.xpath('.//h3[contains(@class, \"employee__name\")]/strong/text()').get()
                #  Debug potential name extraction paths
                #  # Log raw HTML for the staff item
                # self.logger.debug(f"Raw staff HTML: {staff.get()}")
                # self.logger.debug(f"Attempting name extraction for staff item: {staff.get()}")
                # self.logger.debug(f"Path 1 (h3 > strong): {staff.xpath('.//h3[contains(@class, \"employee__name\")]/strong/text()').get()}")
                # self.logger.debug(f"Path 2 (h3): {staff.xpath('.//h3[contains(@class, \"employee__name\")]/text()').get()}")
                # self.logger.debug(f"Path 3 (general h3): {staff.xpath('.//h3/text()').get()}")
                # self.logger.debug(f"Path 4 (data-dotagging-affiliation): {staff.xpath('.//@data-dotagging-affiliation').get()}")

                # Exit condition after processing the first staff item
                # if index == 2:
                #     break

                title = staff.xpath(
                    './/h4[contains(@class, "employee__title")]/text() | '
                    './/h4/text() | '
                    './/div[contains(@class, "staff-desc")]/em/text() | '
                    './/div[contains(@class, "title")]/text()'
                ).get()

                obfuscated_email_href = staff.xpath('.//a[contains(@href, "cdn-cgi/l/email-protection")]/@href').get()
                email = None
                if obfuscated_email_href:
                    encoded_email = obfuscated_email_href.split('#')[-1]
                    email = self.decode_cloudflare_email(encoded_email)
                else:
                    email = staff.xpath('.//a[contains(@href, "mailto:")]/@href').get(default='').replace("mailto:", "")

                # Phone extraction with fallback
                phone_div = staff.xpath('.//div[contains(@class, "staffphone")]/text()').getall()
                phone = "".join([line.strip() for line in phone_div if line.strip()])
                phone = re.sub(r'\s+', '', phone) if phone else None
                if not phone:
                    phone = staff.xpath('.//a[contains(@href, "tel:")]/@href').get()
                    phone = phone.replace("tel:", "").strip() if phone else None

                # Image extraction
                image_url = staff.xpath(
                    './/img[contains(@class, "employee__pic") or contains(@class, "staffpic") or contains(@class, "staff-photo") or contains(@class, "img-responsive")]/@src'
                ).get()
                # Fallback for image
                if not image_url:
                    image_url = staff.xpath('.//div[contains(@class, "staff-img")]//img/@src').get()
                image_url = response.urljoin(image_url) if image_url else None

                bio = staff.xpath(
                    './/p[contains(@class, "bio")]//text() | '
                    './/div[contains(@class, "bio")]/p//text()'
                ).getall()
                bio = " ".join([line.strip() for line in bio]) if bio else None

                staff_data = {
                    "name": name.strip() if name else None,
                    "title": title.strip() if title else None,
                    "email": email if email else None,
                    "phone_number": phone if phone else None,
                    "bio": bio.strip() if bio else None,
                    "image_url": image_url,
                    "source_url": response.url,
                }

                unique_key = (staff_data["name"], staff_data["email"], staff_data["source_url"])
                if unique_key not in self.seen_staff and any(
                    staff_data[key] for key in ["name", "title", "email", "phone_number", "bio"]
                ):
                    self.seen_staff.add(unique_key)
                    yield staff_data

        else:
            # Handle fallback structures
            staff_sections = response.xpath(
                '//dl[contains(@class, "vcard")] | '
                '//div[contains(@class, "cvcard")] | '
                '//div[contains(@class, "staff")] | '
                '//div[contains(@class, "employee-card")]'
            )

            for staff in staff_sections:
                name = staff.xpath(
                    './/dt[@class="fn"]/a/text() | '
                    './/h3/text() | '
                    './/div[contains(@class, "name")]/text() | '
                    './/div[contains(@class, "cvcard-name")]/text()'
                ).get()

                title = staff.xpath(
                    './/dd[@class="title"]/text() | '
                    './/p[contains(@class, "title") or contains(@class, "position") or contains(@class, "cvcard-title")]/text()'
                ).get()

                email = staff.xpath(
                    './/dd[@class="email"]/text() | '
                    './/a[contains(@href, "mailto:")]/@href'
                ).get(default='').replace("mailto:", "")

                phone = staff.xpath(
                    './/dd[@class="phone"]/text() | '
                    './/a[contains(@href, "tel:")]/@href'
                ).get(default='').replace("tel:", "")

                bio = staff.xpath(
                    './/dd[@class="bio"]/p//text() | '
                    './/p[contains(@class, "description")]//text()'
                ).getall()
                bio = " ".join([line.strip() for line in bio]) if bio else None

                image_url = staff.xpath(
                    './/dd[@class="photo"]//img/@src | '
                    './/img/@src'
                ).get()

                staff_data = {
                    "name": name.strip() if name else None,
                    "title": title.strip() if title else None,
                    "email": email.strip() if email else None,
                    "phone_number": phone.strip() if phone else None,
                    "bio": bio.strip() if bio else None,
                    "image_url": response.urljoin(image_url) if image_url else None,
                    "source_url": response.url,
                }

                unique_key = (staff_data["name"], staff_data["email"], staff_data["title"], staff_data["source_url"])
                if unique_key not in self.seen_staff and any(
                    staff_data[key] for key in ["name", "title", "email", "phone_number", "bio"]
                ):
                    self.seen_staff.add(unique_key)
                    yield staff_data
