from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import json
from html import unescape
import pandas as pd
from tempfile import NamedTemporaryFile
import base64
from xml.etree import ElementTree
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

# Load .env file
load_dotenv()

# Global constants (to be set by user)
IMAGE_GEN_MODEL = "openai"  # "openai" or "stability"
TEXT_GEN_MODEL = "gpt-3.5-turbo"  # OpenAI model to use for text generation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
WP_USERNAME = os.getenv("WP_USERNAME")  # Set your WordPress username in .env file
WP_PASSWORD = os.getenv("WP_PASSWORD")  # Set your WordPress password in .env file
WORDPRESS_URL = os.getenv("WORDPRESS_URL")  # Set your WordPress site URL in .env file
POST_TO_SOCIALS = False  # Set to True if you want to post to socials
SITEMAP_URLS = [
    f'{WORDPRESS_URL}/post-sitemap.xml',
    f'{WORDPRESS_URL}/page-sitemap.xml'
]  # List of sitemap URLs

# Prompts
PROMPT_SYSTEM = "You are an expert SEO copywriter who always writes original, search engine optimized human-like content."
PROMPT_CATEGORY_NAME = "Blog title: {title}. Here are the available categories: {category_names}. Respond with the category that matches best. Do not respond with anything else or any other words."
PROMPT_META_DESCRIPTION = "Write a short SEO description for a blog titled {title}. It should be no more than 120 chars max."
PROMPT_IMAGE = "Return a prompt for Dall-e image generation that can be used as cover/hero image for a blog background hero image / title image. The blog title is the following for context: {query}. Example prompt for a post about SEO: 'Business meeting, office, photorealism, looking at chart on screen'."
PROMPT_SECTION_INTRO = "You are an expert seo content writer targeting the keyword '{keyword}'. Generate an introduction for the section titled '{section_title}' with the following subsections in mind: {subsections}. Don't include numbers in the subsections if you mention them. Don't mention them all either. Just write about the section in general. It's okay to mention the subsections in the intro, but don't mention them all."
PROMPT_SUBSECTION = "You are an expert seo content writer and blogger targeting the keyword {keyword}. Given the blog title '{blog_title}', section title '{section_title}', and subsection title '{subsection_title}', generate the content for the current subsection. Do not include numbered points in here unless it makes sense for a specific part of what you're writing. Note: please put each paragraph in <p> tags. Also, if it makes sense, include a hyperlink to an applicable link from the following from our website: {urls}. For example <a href=\"*url*\"> *some text*</a>. You should only include a hyperlink 10 percent of the time you see this message. Additionally, include an applicable & relevant HTML table relevant to the subsection title. Use proper HTML table tags."
PROMPT_BLOG_TITLE = "Keyword: {keyword} | USING A MAXIMUM OF 40 CHARACTERS IN YOUR RESPONSE: Generate a h1 / new blog title for my company's website. We are a small digital marketing agency who primarily deals with small businesses. The purpose of our blog is to target small business owners and provide helpful tips and tricks. Keep SEO in mind. Make sure it is not a duplicate of the following posts as they already exist: {post_titles}. But use them as inspiration for the type of posts we like to do. Also, try to make an even balance of topics across these topics: {categories} using my existing blog titles. If you do decide to include a year the current year is 2024, but do not do 'Local SEO in 2024:' for example. NEVER use ':' in your title response. Only return the title and nothing else. No other text. Just the title text. Do not enclose it in double quotes either. This is very important that you only return the title text and create and SEO optimized header between meaning using the keyword in the header. 50-60 total characters max."
PROMPT_BLOG_OUTLINE = "Generate a blog outline for the following blog title / h1: {blog_title}. It's vital that the response is only the json that matches this structure as an example: {example} but include more than just the 2 sections, they're just examples of the json format needed per each object. End with a conclusion for each main section. The conclusion doesn't have subsections. It is VITAL that you provide valid json only in the response. For example, No other words or chars, and \" not 's."

tokens_used = 0
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_category_id(category_name, wordpress_url, username, password):
    categories_url = f"{wordpress_url.rstrip('/')}/wp-json/wp/v2/categories"
    response = requests.get(categories_url, auth=(username, password))

    if response.status_code == 200:
        categories = response.json()
        for category in categories:
            if category['name'].lower() == category_name.lower():
                return category['id']

    logger.info(f"Failed to retrieve categories: {response.status_code} - {response.text}")
    return None

def generate_response(prompt):
    global tokens_used
    response_text = ""

    try:
        completion = openai_client.chat.completions.create(
            model=TEXT_GEN_MODEL,
            messages=[
                {"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user", "content": prompt}
            ]
        )
        tokens_used += completion.usage.total_tokens
        response_text = completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in generating response: {e}")
        raise e

    return response_text

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def save_html_content(path, filename, content):
    with open(os.path.join(path, filename), 'w', encoding='utf-8') as f:
        f.write(content)

def save_image(path, filename, image_data):
    with open(os.path.join(path, filename), 'wb') as f:
        f.write(image_data)


def upload_to_website(title, img_path, content, wordpress_url, username, password):
    try:
        with open(img_path, 'rb') as img_file:
            image_data = img_file.read()
    except Exception as e:
        logger.error(f"Error reading saved image: {e}")
        return

    image_headers = {
        'Content-Type': 'image/jpeg',
        'Content-Disposition': 'attachment; filename=featured_image.jpg',
        'Authorization': f'Basic {base64.b64encode(f"{username}:{password}".encode()).decode()}'
    }
    image_upload_url = f"{wordpress_url.rstrip('/')}/wp-json/wp/v2/media"
    image_upload_response = requests.post(image_upload_url, data=image_data, headers=image_headers)

    if image_upload_response.status_code != 201:
        logger.info(f"Failed to upload image: {image_upload_response.status_code} - {image_upload_response.text}")
        return

    featured_image_id = image_upload_response.json().get('id')

    categories = get_categories(wordpress_url, username, password)
    category_names = [category['name'] for category in categories]

    category_name_prompt = PROMPT_CATEGORY_NAME.format(title=title, category_names=category_names)
    category_name = generate_response(category_name_prompt)

    category_id = None
    for category in categories:
        if category['name'].lower() == category_name.lower():
            category_id = category['id']
            break

    meta_title = title
    meta_description = generate_response(PROMPT_META_DESCRIPTION.format(title=title))

    post_headers = {'Content-Type': 'application/json'}
    post_payload = {
        'title': title.replace("\"", ""),
        'content': content,
        'status': 'publish',
        'featured_media': featured_image_id,
        'categories': [category_id] if category_id else [],
        'meta': {
            'rank_math_title': meta_title,
            'rank_math_description': meta_description
        }
    }
    post_url = f"{wordpress_url.rstrip('/')}/wp-json/wp/v2/posts"
    post_response = requests.post(post_url, json=post_payload, headers=post_headers, auth=(username, password))

    if post_response.status_code == 201:
        logger.info(f"Post published with ID {post_response.json()['id']}. View it at: {post_response.json()['link']}")

        if POST_TO_SOCIALS:
            content = generate_response(f"Generate a captivating, catchy, social media post for my new blog. The title of the blog is: {post_payload['title']} but you don't need to include the title necessarily... Include new lines where necessary, and include 3 to 5 relevant hashtags. Include a link to the blog with some text such as 'Read more here: {post_response.json()['link']}'")
            # post_to_facebook(content)
            content = generate_response(f"Generate a captivating, catchy, social media post for my new blog. The title of the blog is: {post_payload['title']} but you don't need to include the title necessarily... Include new lines where necessary, and include 3 to 5 relevant hashtags. Include a link to the blog with some text such as 'Read more here: {post_response.json()['link']}' No more than 140 characters including the url!! - this is VERY IMPORTANT.")
            # post_to_twitter(content)
        else:
            logger.info(f"Did not post to socials as global var 'POST_TO_SOCIALS' is set to {POST_TO_SOCIALS}")
    else:
        logger.info(f"Failed to publish post: {post_response.status_code} - {post_response.text}")

def get_current_posts(api_url=None):
    if api_url is None:
        api_url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    params = {'per_page': 100, '_fields': 'title'}
    all_titles = []
    page = 1
    total_pages = None

    while True:
        params['page'] = page
        response = requests.get(api_url, params=params)

        logger.info(f"Request URL: {response.url}")
        logger.info(f"Request Parameters: {params}")

        if response.status_code == 200:
            if total_pages is None:
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))

            posts = response.json()
            titles = [unescape(post['title']['rendered']) for post in posts]
            all_titles.extend(titles)

            if page >= total_pages:
                break

            page += 1
        else:
            logger.info(f"Failed to retrieve blog posts on page {page}: {response.status_code}")
            logger.info(f"Response content: {response.content.decode('utf-8')}")
            break

    return all_titles

def get_urls_from_sitemaps(sitemap_urls: list) -> list:
    all_urls = []
    for sitemap_url in sitemap_urls:
        try:
            response = requests.get(sitemap_url)
            xml_content = response.content.decode(response.encoding)
            tree = ElementTree.fromstring(xml_content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = [elem.text for elem in tree.findall(".//ns:loc", namespaces=namespace)]
            all_urls.extend(urls)
        except ElementTree.ParseError as pe:
            logger.error(f"XML Parse Error: {pe}")
        except Exception as e:
            logger.error(f"Error: {e}")
    return all_urls

def generate_image(query):
    if IMAGE_GEN_MODEL == "openai":
        img_prompt = generate_response(PROMPT_IMAGE.format(query=query))
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=img_prompt,
            n=1,
            size="1024x1024",
            response_format="url",
            style="vivid"
        )
        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        with NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
            tmpfile.write(image_data)
            return tmpfile.name, image_data

    elif IMAGE_GEN_MODEL == "stability":
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        body = {
            "steps": 40,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "cfg_scale": 5,
            "samples": 1,
            "text_prompts": [
                {
                    "text": query,
                    "weight": 1
                },
                {
                    "text": "blurry, bad",
                    "weight": -1
                }
            ],
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {STABILITY_API_KEY}",
        }

        response = requests.post(url, headers=headers, json=body)
        if response.status_code != 200:
            raise Exception(f"Non-200 response: {response.text}")

        data = response.json()
        with NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
            tmpfile.write(base64.b64decode(data["artifacts"][0]["base64"]))
            return tmpfile.name, base64.b64decode(data["artifacts"][0]["base64"])

    else:
        raise ValueError("Invalid IMAGE_GEN_MODEL value")

def create_blog_content(keyword, blog_title, sections):
    content = ""
    image_path, image_data = generate_image(blog_title)

    for section in sections:
        logger.info(f"Working on section: {section['title']}")
        section_intro = generate_response(PROMPT_SECTION_INTRO.format(keyword=keyword, section_title=section['title'], subsections=', '.join(section['subsections'])))
        content += f"<h2>{section['title']}</h2>\n<p>{section_intro}</p>\n"

        for subsection_title in section['subsections']:
            logger.info(f"\t - Working on sub-section: {subsection_title}")
            subsection_content = generate_response(PROMPT_SUBSECTION.format(keyword=keyword, blog_title=blog_title, section_title=section['title'], subsection_title=subsection_title, urls=str(get_urls_from_sitemaps(SITEMAP_URLS))))
            content += f"<h3>{subsection_title}</h3>\n{subsection_content}\n"
        content += "\n"

    return blog_title, image_path, content, image_data

def prompt_for_title_approval(blog_title):
    while True:
        user_input = input(f"\n ### INPUT REQUIRED: ### \n\n\tProposed blog title: {blog_title}\n\tProceed? 1 Yes / 2 No: ")
        if user_input == '1':
            return True
        elif user_input == '2':
            return False
        else:
            logger.info("Invalid choice. Please enter 1 for Yes or 2 for No.")

def get_categories(wordpress_url, username, password):
    categories_url = f"{wordpress_url.rstrip('/')}/wp-json/wp/v2/categories"
    response = requests.get(categories_url, auth=(username, password))

    if response.status_code == 200:
        categories = response.json()
        # Remove "Uncategorized" category if it exists
        categories = [category for category in categories if category['name'].lower() != 'uncategorized']
        return categories

    logger.info(f"Failed to retrieve categories: {response.status_code} - {response.text}")
    return []

if __name__ == "__main__":
    user_keyword = input("Enter your keyword: ")
    if not user_keyword:
        logger.error("No keyword provided. Exiting...")
        exit()

    post_titles = get_current_posts()
    categories = ["Search engine optimization", "tips & tricks", "Website Design", "Business Specific"]
    while True:
        blog_title = generate_response(PROMPT_BLOG_TITLE.format(keyword=user_keyword, post_titles=str(post_titles), categories=str(categories)))
        if prompt_for_title_approval(blog_title):
            break

    logger.info(f"New blog incoming!! {blog_title}")
    blog_outline_example = {
        "Title": blog_title,
        "sections": [
            {
                "title": "1. *replace with title for section 1*",
                "subsections": ["1.1 *subsection title*", "1.2 *subsection title*", "1.3 *subsection title*"]
            },
            {
                "title": "2. *replace with title for section 2*",
                "subsections": ["2.1 *subsection title*", "2.2 *subsection title*"]
            }
        ]
    }

    logger.info("Generating the outline for a killer blog...")
    blog_outline = generate_response(PROMPT_BLOG_OUTLINE.format(blog_title=blog_title, example=json.dumps(blog_outline_example)))

    try:
        blog_outline_json = json.loads(blog_outline)
        logger.info(f"Blog outline generated: {blog_outline_json}")
        title, img_path, content, img_data = create_blog_content(user_keyword, blog_title, blog_outline_json["sections"])

        # Create directory structure and save files
        today = datetime.now().strftime("%Y-%m-%d")
        sanitized_title = ''.join(e for e in blog_title if e.isalnum() or e.isspace()).replace(' ', '_')
        base_dir = f"runs/{today}-{sanitized_title}"
        create_directory(base_dir)
        save_html_content(base_dir, 'content.html', content)
        save_image(base_dir, f"{sanitized_title}.png", img_data)

        # Attempt to upload to WordPress
        upload_to_website(title, f"{base_dir}/{sanitized_title}.png", content, WORDPRESS_URL, WP_USERNAME, WP_PASSWORD)

        estimated_cost = (tokens_used / 1000) * 0.002
        logger.info(f"Created blog with {tokens_used} tokens. Estimated cost in USD is ${estimated_cost:.4f}")

    except json.JSONDecodeError:
        logger.error("Error decoding blog_outline response to JSON")
        logger.error(f"Received: {blog_outline}")
