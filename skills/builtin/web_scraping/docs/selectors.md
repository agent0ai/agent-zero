# CSS and XPath Selector Guide

Comprehensive guide to selecting HTML elements for web scraping with BeautifulSoup.

## CSS Selectors (Recommended)

CSS selectors are the preferred method for BeautifulSoup as they are readable and widely supported.

### Basic Selectors

#### By Tag
```python
# Find first occurrence
soup.find('h1')
soup.select_one('h1')

# Find all occurrences
soup.find_all('p')
soup.select('p')
```

#### By Class
```python
# Single class
soup.find('div', class_='content')
soup.select('.content')

# Multiple classes (must have both)
soup.find('div', class_='content featured')
soup.select('.content.featured')

# Any of multiple classes
soup.select('.content, .featured')
```

#### By ID
```python
# Find by ID
soup.find(id='header')
soup.find('div', id='header')
soup.select('#header')
```

### Attribute Selectors

```python
# Element with specific attribute
soup.select('a[href]')           # All links with href
soup.select('img[src]')          # All images with src
soup.select('input[type]')       # All inputs with type

# Attribute equals value
soup.select('a[href="https://example.com"]')
soup.select('input[type="text"]')

# Attribute starts with
soup.select('a[href^="https://"]')     # Links starting with https://
soup.select('img[src^="/images/"]')    # Images in /images/ directory

# Attribute ends with
soup.select('a[href$=".pdf"]')         # PDF links
soup.select('img[src$=".jpg"]')        # JPG images

# Attribute contains
soup.select('a[href*="example"]')      # Links containing "example"
soup.select('div[class*="card"]')      # Divs with "card" in class

# Multiple attributes
soup.select('input[type="text"][name="email"]')
```

### Descendant Selectors

```python
# Direct descendant (child)
soup.select('div > p')           # p directly inside div
soup.select('ul > li')           # li directly inside ul

# Any descendant
soup.select('div p')             # All p inside div (at any level)
soup.select('article a')         # All links inside article

# Multiple levels
soup.select('div.content > article > p')
```

### Pseudo-classes

```python
# First/Last child
soup.select('li:first-child')
soup.select('li:last-child')
soup.select('p:nth-child(2)')    # Second p element

# First/Last of type
soup.select('p:first-of-type')
soup.select('div:last-of-type')

# Nth child
soup.select('tr:nth-child(odd)')   # Odd rows
soup.select('tr:nth-child(even)')  # Even rows
soup.select('li:nth-child(3)')     # Third li

# Not selector
soup.select('a:not(.external)')    # Links without .external class
soup.select('div:not(#header)')    # Divs except #header
```

### Combining Selectors

```python
# Multiple selectors (OR)
soup.select('h1, h2, h3')              # All headings
soup.select('.featured, .popular')     # Elements with either class

# Complex combinations
soup.select('article.post > h2.title')
soup.select('div.content p:first-child')
soup.select('nav ul > li:not(:last-child)')
```

## BeautifulSoup Methods

### find() and find_all()

```python
# Basic usage
soup.find('div')                    # First div
soup.find_all('div')                # All divs

# With attributes
soup.find('div', class_='content')
soup.find('a', href=True)           # Any a with href
soup.find('meta', attrs={'name': 'description'})

# With multiple attributes
soup.find('input', {'type': 'text', 'name': 'email'})
soup.find_all('div', class_='card', id=True)

# Limit results
soup.find_all('p', limit=5)         # First 5 paragraphs

# Recursive search (default True)
soup.find_all('p', recursive=False)  # Only direct children
```

### find_parent() and find_parents()

```python
# Find parent element
element = soup.find('span', class_='price')
parent = element.find_parent('div')

# Find all parents matching criteria
parents = element.find_parents('div', class_='product')
```

### find_next_sibling() and find_previous_sibling()

```python
# Next/previous sibling
element = soup.find('h2', string='Products')
next_elem = element.find_next_sibling('div')
prev_elem = element.find_previous_sibling('nav')

# All next/previous siblings
next_siblings = element.find_next_siblings('p')
prev_siblings = element.find_previous_siblings('p')
```

### select() and select_one()

```python
# CSS selectors (recommended)
soup.select('div.content p')        # All p in div.content
soup.select_one('h1#title')         # First h1 with id="title"

# Returns list (select) or single element (select_one)
all_links = soup.select('a[href]')
first_heading = soup.select_one('h1')
```

## XPath Support (via lxml)

BeautifulSoup doesn't natively support XPath, but you can use lxml:

```python
from lxml import html

# Parse with lxml
tree = html.fromstring(response.content)

# XPath examples
tree.xpath('//div[@class="content"]')          # Divs with class="content"
tree.xpath('//a[@href]')                       # All links with href
tree.xpath('//h1/text()')                      # Text content of h1
tree.xpath('//div[@class="post"]//a/@href')    # Href of links in posts

# Complex XPath
tree.xpath('//article[contains(@class, "post")]//h2/text()')
tree.xpath('//div[@id="main"]//p[position() < 3]')  # First 2 p in #main
```

## Common Patterns

### Extract Text Content

```python
# Get text from element
element = soup.find('h1')
text = element.text              # All text including children
text = element.get_text()        # Same as .text
text = element.string            # Direct text only (no children)

# Clean whitespace
text = element.text.strip()
text = ' '.join(element.text.split())  # Normalize whitespace

# Get text from multiple elements
texts = [p.text.strip() for p in soup.find_all('p')]
```

### Extract Attributes

```python
# Get attribute value
link = soup.find('a')
href = link['href']              # Raises KeyError if missing
href = link.get('href')          # Returns None if missing
href = link.get('href', 'default')  # Default value

# Get all attributes
attrs = link.attrs               # Dict of all attributes

# Check if attribute exists
if link.has_attr('target'):
    print(link['target'])
```

### Navigate Tree

```python
element = soup.find('div', class_='content')

# Children
for child in element.children:
    print(child.name)

# All descendants
for descendant in element.descendants:
    if descendant.name == 'a':
        print(descendant['href'])

# Parent
parent = element.parent

# Siblings
next_sib = element.next_sibling
prev_sib = element.previous_sibling

# Following/preceding elements
next_elem = element.find_next('p')
prev_elem = element.find_previous('h2')
```

## Practical Examples

### Extract Article Data

```python
articles = soup.select('article.post')

for article in articles:
    title = article.select_one('h2.title')
    author = article.select_one('span.author')
    date = article.select_one('time')
    content = article.select_one('div.content')

    data = {
        'title': title.text.strip() if title else None,
        'author': author.text.strip() if author else None,
        'date': date.get('datetime') if date else None,
        'content': content.text.strip() if content else None
    }
```

### Extract Product Information

```python
products = soup.select('div.product-card')

for product in products:
    name = product.select_one('h3.product-name')
    price = product.select_one('span.price')
    image = product.select_one('img.product-image')
    link = product.select_one('a.product-link')

    product_data = {
        'name': name.text.strip() if name else None,
        'price': price.text.strip() if price else None,
        'image_url': image.get('src') if image else None,
        'product_url': link.get('href') if link else None
    }
```

### Extract Table Data

```python
table = soup.find('table', class_='data-table')
rows = table.find_all('tr')

# Extract headers
headers = [th.text.strip() for th in rows[0].find_all('th')]

# Extract data rows
data = []
for row in rows[1:]:
    cells = row.find_all('td')
    row_data = {headers[i]: cell.text.strip() for i, cell in enumerate(cells)}
    data.append(row_data)
```

### Extract Nested Lists

```python
nav = soup.find('nav', class_='menu')
top_items = nav.find_all('li', recursive=False)  # Only direct children

menu_structure = []
for item in top_items:
    item_data = {
        'text': item.find('a', recursive=False).text.strip(),
        'link': item.find('a', recursive=False)['href'],
        'subitems': []
    }

    # Check for submenu
    submenu = item.find('ul')
    if submenu:
        for subitem in submenu.find_all('li'):
            item_data['subitems'].append({
                'text': subitem.find('a').text.strip(),
                'link': subitem.find('a')['href']
            })

    menu_structure.append(item_data)
```

## Performance Tips

1. **Use specific selectors**: `soup.select('div.content > p')` is faster than `soup.find_all('p')`

2. **Limit scope**: Search within a smaller element when possible
   ```python
   content_div = soup.find('div', class_='content')
   paragraphs = content_div.find_all('p')  # Faster than soup.find_all('p')
   ```

3. **Use select_one() when possible**: Stops after first match
   ```python
   title = soup.select_one('h1')  # Faster than soup.select('h1')[0]
   ```

4. **Choose the right parser**:
   - `lxml`: Fastest, most features
   - `html.parser`: Built-in, no dependencies
   - `html5lib`: Most lenient, slowest

5. **Compile regular expressions**: If using regex in searches
   ```python
   import re
   pattern = re.compile(r'product-\d+')
   elements = soup.find_all('div', class_=pattern)
   ```

## Debugging Selectors

### Print Element Structure

```python
# Pretty print HTML
print(element.prettify())

# Print element name and attributes
print(f"Tag: {element.name}")
print(f"Classes: {element.get('class', [])}")
print(f"ID: {element.get('id')}")
```

### Test Selectors in Browser

Use browser DevTools Console to test CSS selectors:
```javascript
// Test CSS selector
document.querySelectorAll('div.content > p')

// Count elements
document.querySelectorAll('a[href]').length
```

### Common Issues

**Selector returns empty list:**
- Check selector syntax
- Verify element exists in HTML (use browser DevTools)
- Check if content loads via JavaScript (use Selenium)
- Ensure correct parser is used

**Gets wrong element:**
- Make selector more specific
- Use multiple classes or attributes
- Navigate from parent element

**AttributeError when accessing properties:**
- Check if element exists before accessing
- Use `.get()` method for safe attribute access
- Verify element is not None

## Reference

### CSS Selector Syntax

| Selector | Description |
|----------|-------------|
| `tag` | Select by tag name |
| `.class` | Select by class |
| `#id` | Select by ID |
| `[attr]` | Has attribute |
| `[attr="val"]` | Attribute equals |
| `[attr^="val"]` | Attribute starts with |
| `[attr$="val"]` | Attribute ends with |
| `[attr*="val"]` | Attribute contains |
| `parent > child` | Direct child |
| `ancestor descendant` | Any descendant |
| `prev + next` | Next sibling |
| `prev ~ siblings` | Following siblings |
| `:first-child` | First child |
| `:last-child` | Last child |
| `:nth-child(n)` | Nth child |
| `:not(selector)` | Negation |

### BeautifulSoup Methods

| Method | Description |
|--------|-------------|
| `find(name, attrs)` | First matching element |
| `find_all(name, attrs)` | All matching elements |
| `select(selector)` | CSS selector (all) |
| `select_one(selector)` | CSS selector (first) |
| `find_parent(name)` | Parent element |
| `find_next_sibling()` | Next sibling |
| `find_previous_sibling()` | Previous sibling |
| `get(attr, default)` | Get attribute safely |
| `has_attr(attr)` | Check attribute exists |
| `text` or `get_text()` | Extract text content |

## Additional Resources

- BeautifulSoup Documentation: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- CSS Selectors Reference: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors
- CSS Diner (Interactive Tutorial): https://flukeout.github.io/
- Selector Specificity Calculator: https://specificity.keegan.st/
