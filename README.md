# 📝 Bloggy Blogger

This project is designed to generate blog content and images using OpenAI's GPT and Dall-E models. The generated content is then uploaded to a WordPress site. The script dynamically generates blog titles, outlines, featured images, and sections based on provided keywords and existing blog posts/sitemap.

## ⚙️ Setup

### Prerequisites

- 🐍 Python 3.12.1 or higher
- 🌐 A WordPress site with REST API enabled
- 🔑 API keys for OpenAI and Stability AI
- 📝 WordPress Application Password

### 🧑‍💻 Clone the repository

### 🌟 Create and activate a virtual environment

```
python -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate
```

### 📦 Install the required dependencies

```
pip install -r requirements.txt
```

### 🗂️ Create a .env file

Create a .env file in the project root directory with the following content:

```
OPENAI_API_KEY=your_openai_api_key
STABILITY_API_KEY=your_stability_api_key
WP_USERNAME=your_wordpress_username
WP_PASSWORD=your_wordpress_application_password
WORDPRESS_URL=your_wordpress_url
```

### 🔑 Obtain API Keys

#### OpenAI API Key:

1. Sign up at [OpenAI](https://beta.openai.com/signup/).
2. Go to the API section and generate a new API key.

#### Stability AI API Key (Optional):

1. Sign up at [Stability AI](https://stability.ai/).
2. Go to the API section and generate a new API key.

### 🌐 Enable WordPress REST API and Obtain Application Password

1. **Enable REST API:**
   - The WordPress REST API is enabled by default for all WordPress sites. You can test this by accessing the following URL in your browser:
     ```
     https://your-wordpress-url/wp-json/wp/v2/
     ```
     If you see a JSON response, the REST API is enabled.

2. **Obtain WordPress Application Password:**
   - Log in to your WordPress site.
   - Go to Users > Profile.
   - Scroll down to Application Passwords.
   - Enter a new application password name and click Add New Application Password.
   - Copy the generated password. This will be your WP_PASSWORD.

## 🚀 Usage

### ▶️ Run the script

```
python bloggy.py
```

### 🔍 Input your keyword

When prompted, input the keyword for which you want to generate the blog content.

### 📝 Approve the generated blog title

The script will generate a blog title based on the provided keyword and existing blog posts. You will be prompted to approve or reject the title.

### 📝 Generated Content

The script will:

- Generate a blog outline
- Generate section content
- Generate a hero image for the blog post

### 💾 Local Saving

The generated content and image will be saved locally in the `runs/YYYY-MM-DD-title/` directory.

### 🌐 Upload to WordPress

The script will attempt to upload the generated content and image to your WordPress site.

## 🛠️ Prompts

The prompts used for generating the blog content and images are defined at the top of the script for easy modification:

```
PROMPT_BLOG_TITLE = (
    "Keyword: {keyword} | USING A MAXIMUM OF 40 CHARACTERS IN YOUR RESPONSE: Generate a h1 / new blog title for our website. "
    "The purpose of our blog is to provide valuable insights, tips, and tricks relevant to our audience. "
    "Keep SEO in mind. Make sure it is not a duplicate of the following posts as they already exist: {post_titles}. Use them as inspiration for the type of posts we create. "
    "Also, try to make an even balance of topics across these categories: {categories}. If you decide to include a year, the current year is 2024, but do not use 'Local SEO in 2024:' for example. "
    "NEVER use ':' in your title response. Only return the title and nothing else. No other text. Just the title text. Do not enclose it in double quotes either. "
    "This is very important that you only return the title text and create an SEO optimized header using the keyword in the header. 50-60 total characters max."
)

PROMPT_BLOG_OUTLINE = (
    "Generate a blog outline for the following blog title / h1: {blog_title}. It's vital that the response is only the JSON that matches this structure as an example: {example} "
    "but include more than just the 2 sections, they're just examples of the JSON format needed per each object. End with a conclusion for each main section. The conclusion doesn't have subsections. "
    "It is VITAL that you provide valid JSON only in the response. For example, No other words or chars, and ' not \"s."
)

PROMPT_SECTION_INTRO = (
    "You are an expert SEO content writer targeting the keyword '{keyword}'. Generate an introduction for the section titled '{section_title}' with the following subsections in mind: {subsections}. "
    "Don't include numbers in the subsections if you mention them. Don't mention them all either. Just write about the section in general. It's okay to mention the subsections in the intro, but don't mention them all."
)

PROMPT_SUBSECTION = (
    "You are an expert SEO content writer and blogger targeting the keyword {keyword}. Given the blog title '{blog_title}', section title '{section_title}', and subsection title '{subsection_title}', generate the content for the current subsection. "
    "Do not include numbered points in here unless it makes sense for a specific part of what you're writing. Note: please put each paragraph in <p> tags. "
    "Also, if it makes sense, include a hyperlink to an applicable link from the following from our website: {urls}. For example <a href=\"url\"> some text</a>. "
    "You should only include a hyperlink 10 percent of the time you see this message. Additionally, include an applicable & relevant HTML table relevant to the subsection title. Use proper HTML table tags."
)

PROMPT_IMAGE = (
    "Return a prompt for Dall-e image generation that can be used as a cover/hero image for a blog background hero image / title image. The blog title is the following for context: {query}. "
    "Example prompt for a post about SEO: 'Business meeting, office, photorealism, looking at chart on screen'."
)
```

## 📋 Notes

- The script will save the generated content and image locally in a `runs/YYYY-MM-DD-title/` directory before attempting to upload to WordPress.
- Make sure to replace placeholder values in the `.env` file with your actual credentials and URLs.
- Ensure that your WordPress site is configured to accept API requests for media and post creation.

## 📄 License

This project is licensed under the MIT License.
