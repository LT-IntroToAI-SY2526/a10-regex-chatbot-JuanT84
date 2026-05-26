import re, string, calendar, requests, time
from wikipedia import WikipediaPage
import wikipedia
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match


def get_page_html(title: str) -> str:
    for attempt in range(5):
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "redirects": True,
            },
            headers={"User-Agent": "intro-ai-class/1.0"}
        )
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
            print(f"Rate limited — waiting {wait}s before retrying '{title}'...")
            time.sleep(wait)
            continue
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if "error" not in data:
                time.sleep(2)  # polite delay after every successful call
                return data["parse"]["text"]["*"]
    raise ConnectionError(f"Could not retrieve Wikipedia page for '{title}' after 5 attempts")


def get_first_infobox_text(html: str) -> str:
    """Gets first infobox html from a Wikipedia page (summary box)

    Args:
        html - the full html of the page

    Returns:
        html of just the first infobox
    """
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(class_="infobox")

    if not results:
        raise LookupError("Page has no infobox")
    return results[0].text


def clean_text(text: str) -> str:
    """Cleans given text removing non-ASCII characters and duplicate spaces & newlines

    Args:
        text - text to clean

    Returns:
        cleaned text
    """
    only_ascii = "".join([char if char in string.printable else " " for char in text])
    no_dup_spaces = re.sub(" +", " ", only_ascii)
    no_dup_newlines = re.sub("\n+", "\n", no_dup_spaces)
    return no_dup_newlines


def get_match(
    text: str,
    pattern: str,
    error_text: str = "Page doesn't appear to have the property you're expecting",
) -> Match:
    """Finds regex matches for a pattern

    Args:
        text - text to search within
        pattern - pattern to attempt to find within text
        error_text - text to display if pattern fails to match

    Returns:
        text that matches
    """
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match = p.search(text)

    if not match:
        raise AttributeError(error_text)
    return match


def get_polar_radius(planet_name: str) -> str:
    """Gets the radius of the given planet

    Args:
        planet_name - name of the planet to get radius of

    Returns:
        radius of the given planet
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(planet_name)))
    pattern = r"(?:Polar radius|Mean radius)(?:[^\d]*)(?P<radius>[\d,.]+)(?:.*?)km"
    error_text = "Page infobox has no polar radius information"
    match = get_match(infobox_text, pattern, error_text)

    return match.group("radius")


def get_birth_date(name: str) -> str:
    """Gets birth date of the given person

    Args:
        name - name of the person

    Returns:
        birth date of the given person
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})"
    error_text = (
        "Page infobox has no birth information (at least none in xxxx-xx-xx format)"
    )
    match = get_match(infobox_text, pattern, error_text)

    return match.group("birth")


def get_capital(place: str) -> str:
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))
    
    # We add (?P<cap>...) to define a named group
    pattern = r"Capital(?:.*?city)?\s*(?P<cap>[A-Z][a-z]+)"
    error_text = f"I found the page for {search_term}, but couldn't find the capital."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    
    # Now .group("cap") will work perfectly
    return match_obj.group("cap").strip()

def get_population(place: str) -> str:
    """Gets the population of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))
    ##print(infobox_text)
    pattern = r"Population.*?\s(?P<pop>[\d,.]+)(?=\[)"    
    error_text = f"I found the page for {search_term}, but couldn't find a population count."
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("pop").strip()

def get_official_language(place: str) -> str:
    """Gets the official language of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))
    #print(infobox_text)
    
    # Regex looks for "Official language" followed by the first word(s)
    # until it hits a newline or a bracketed reference.
    pattern =r"Official\s+languages?\s*(?P<lang>[A-Z][a-z]+)"
    error_text = f"I found the page for {search_term}, but couldn't identify the official language."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("lang").strip()

def get_birth_date(name: str) -> str:
    # Fix: Capitalize name here so it works for "grace hopper"
    search_term = name.strip().title()
    infobox_text = clean_text(get_first_infobox_text(get_page_html(search_term)))
    pattern = r"(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})"
    error_text = "No birth information found in xxxx-xx-xx format."
    match = get_match(infobox_text, pattern, error_text)
    return match.group("birth")

#Extension Final Project

def get_area(place: str) -> str:
    """Gets the area of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))

    # Example matches: "Area 1,234 km2" or "Area Total 12,345 sq mi"
    pattern = r"Area(?:.*?)(?P<area>[\d,]+(?:\.\d+)?\s*(?:km²|km2|sq\s?mi|sqmi|km))"    
    error_text = f"I found the page for {search_term}, but couldn't find an area value."
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("area").strip()

def get_leader(place: str) -> str:
    """Gets the leader (e.g., President, Prime Minister) of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))
    # Matches things like:
    # "President Joe Biden"
    # "Prime Minister Justin Trudeau"
    pattern = r"(President|Prime Minister|Monarch|Leader)\s+(?P<name>[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)"    
    error_text = f"I found the page for {search_term}, but couldn't identify a leader."
 
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("name").strip()

def get_gdp(place: str) -> str:
    """Gets the GDP (Nominal) of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))

    # Matches "GDP (nominal) 2026 estimate Total $X trillion/billion" or similar variations
    pattern = r"GDP\s*(?:\(nominal\))?.*?Total\s*(?P<gdp>\$[0-9.,]+\s*(?:trillion|billion|million|million)?)"
    error_text = f"I found the page for {search_term}, but couldn't find a GDP value."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("gdp").strip()

def get_currency(place: str) -> str:
    """Gets the currency of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))
    # Matches "Currency United States dollar ($) (USD)" or "Currency Euro"
    pattern = r"Currency\s*(?:\([^)]*\))?\s*(?P<curr>[A-Za-z\s]+(?:\s*\([^)]+\)){0,2})"    
    error_text = f"I found the page for {search_term}, but couldn't identify the currency."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("curr").strip()

def get_anthem(place: str) -> str:
    """Gets the official national anthem of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))

    # Matches Anthem: "Das Lied der Deutschen"
    pattern = r"Anthem:\s*(?P<anthem>\"[^\"]+\"|[A-Z][a-zA-Z\s]+)"
    error_text = f"I found the page for {search_term}, but couldn't identify an anthem."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("anthem").strip()

def get_calling_code(place: str) -> str:
    """Gets the international calling code of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))

    # Matches "Calling code +33" or "Calling code 1" (and can capture the '+' symbol if present)
    pattern = r"Calling\s+code\s*(?P<code>\+?[0-9\s\-]+)"
    error_text = f"I found the page for {search_term}, but couldn't find a calling code."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("code").strip()

def get_timezone(place: str) -> str:
    """Gets the primary time zone of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))

    # Matches "Time zone UTC+1" or "Time zone UTC-05:00"
    pattern = r"Time\s+zone\s*(?P<zone>UTC[+-][0-9:]+|[A-Z]{3,4})"
    error_text = f"I found the page for {search_term}, but couldn't identify the time zone."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("zone").strip()

def get_religion(subject: str) -> str:
    """Gets the predominant religion or the subject's personal religion"""
    search_term = subject.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))
    # Matches "Religion Christianity (85%)" or "Religion Islam" or "Religion Roman Catholic"
    pattern = r"Religion\s*.*?(?P<rel>\d+(?:\.\d+)?%\s+[A-Za-z\s]+)"    
    error_text = f"I found the page for {search_term}, but couldn't find religion information."
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("rel").strip()

def get_independence(place: str) -> str:
    """Gets the independence date or milestone of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))
    pattern = r"Independence\s*.*?(?P<date>\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4})"
    error_text = f"I found the page for {search_term}, but couldn't find an independence date."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("date").strip()

def get_coordinates(place: str) -> str:
    """Gets the geographical coordinates of the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))

    # Matches coordinates like "19.433 N 99.133 W" or standard decimal formats "19.433; -99.133"
    pattern = r"(?P<coords>\d+\.\d+\s*[NS]\s*\d+\.\d+\s*[EW]|\d+\.\d+;\s*-\d+\.\d+)"
    error_text = f"I found the page for {search_term}, but couldn't extract coordinates."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("coords").strip()

def get_first_constitution(place: str) -> str:
    """Gets the date of the first constitution for the given place"""
    search_term = place.strip().title()
    html = get_page_html(search_term)
    infobox_text = clean_text(get_first_infobox_text(html))

    # 1. Matches "First constitution"
    # 2. Captures either a full date (e.g., 4 October 1824) or just the 4-digit year
    pattern = r"First\s+constitution\s*(?P<date>\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{4})"
    error_text = f"I found the page for {search_term}, but couldn't find information on their first constitution."
    
    match_obj = get_match(infobox_text, pattern, error_text)
    return match_obj.group("date").strip()

# below are a set of actions. Each takes a list argument and returns a list of answers
# according to the action and the argument. It is important that each function returns a
# list of the answer(s) and not just the answer itself.


def birth_date(matches: List[str]) -> List[str]:
    """Returns birth date of named person in matches

    Args:
        matches - match from pattern of person's name to find birth date of

    Returns:
        birth date of named person
    """
    return [get_birth_date(" ".join(matches))]


def polar_radius(matches: List[str]) -> List[str]:
    """Returns polar radius of planet in matches

    Args:
        matches - match from pattern of planet to find polar radius of

    Returns:
        polar radius of planet
    """
    return [get_polar_radius(matches[0])]

def capital_city(matches: List[str]) -> List[str]:
    """Action function for the capital query."""
    # join matches in case the user types "united states"
    return [get_capital(" ".join(matches))]

def population_count(matches: List[str]) -> List[str]:
    """Action function for the population query."""
    return [get_population(" ".join(matches))]

def official_language(matches: List[str]) -> List[str]:
    """Action function for the official language query."""
    return [get_official_language(" ".join(matches))]

#Extension Final Project

def area_of_place(matches: List[str]) -> List[str]:
    return [get_area(" ".join(matches))]

def leader_of_place(matches: List[str]) -> List[str]:
    return [get_leader(" ".join(matches))]

def gdp_of_place(matches: List[str]) -> List[str]:
    """Action function for the GDP query."""
    return [get_gdp(" ".join(matches))]

def currency_of_place(matches: List[str]) -> List[str]:
    """Action function for the currency query."""
    return [get_currency(" ".join(matches))]

def anthem_of_place(matches: List[str]) -> List[str]:
    """Action function for the anthem query."""
    return [get_anthem(" ".join(matches))]

def calling_code_of_place(matches: List[str]) -> List[str]:
    """Action function for the calling code query."""
    return [get_calling_code(" ".join(matches))]

def timezone_of_place(matches: List[str]) -> List[str]:
    """Action function for the time zone query."""
    return [get_timezone(" ".join(matches))]

def religion_of_subject(matches: List[str]) -> List[str]:
    """Action function for the religion query."""
    return [get_religion(" ".join(matches))]

def independence_of_place(matches: List[str]) -> List[str]:
    """Action function for the independence query."""
    return [get_independence(" ".join(matches))]

def coordinates_of_place(matches: List[str]) -> List[str]:
    """Action function for the coordinates query."""
    return [get_coordinates(" ".join(matches))]

def first_constitution_of_place(matches: List[str]) -> List[str]:
    """Action function for the first constitution query."""
    return [get_first_constitution(" ".join(matches))]


# dummy argument is ignored and doesn't matter
def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt


# type aliases to make pa_list type more readable, could also have written:
# pa_list: List[Tuple[List[str], Callable[[List[str]], List[Any]]]] = [...]
Pattern = List[str]
Action = Callable[[List[str]], List[Any]]

# The pattern-action list for the natural language query system. It must be declared
# here, after all of the function definitions
pa_list: List[Tuple[Pattern, Action]] = [
    ("what is the capital of %".split(), capital_city),
    ("when was % born".split(), birth_date),
    ("what is the polar radius of %".split(), polar_radius),
    ("what is the population of %".split(), population_count),
    ("how many people live in %".split(), population_count),
    ("what language do they speak in %".split(), official_language),

#Extension Final Project

    ("what is the area of %".split(), area_of_place),
    ("who is the leader of %".split(), leader_of_place),
    ("what is the gdp of %".split(), gdp_of_place),
    ("what is the currency of %".split(), currency_of_place),
    ("what money do they use in %".split(), currency_of_place),
    ("what is the anthem of %".split(), anthem_of_place),
    ("what is the national anthem of %".split(), anthem_of_place),
    ("what is the calling code for %".split(), calling_code_of_place),
    ("what is the country code for %".split(), calling_code_of_place),
    ("how do i call %".split(), calling_code_of_place),
    ("what is the time zone of %".split(), timezone_of_place),
    ("what time zone is % in".split(), timezone_of_place),
    ("what is the religion of %".split(), religion_of_subject),
    ("what religion is %".split(), religion_of_subject),
    ("what religion do they practice in %".split(), religion_of_subject),
    ("when did % gain independence".split(), independence_of_place),
    ("what is the independence date of %".split(), independence_of_place),
    ("when was % founded".split(), independence_of_place),
    ("what are the coordinates of %".split(), coordinates_of_place),
    ("where is % located".split(), coordinates_of_place),
    ("what is the latitude and longitude of %".split(), coordinates_of_place),
    ("when was the first constitution of %".split(), first_constitution_of_place),
    ("what is the date of the first constitution of %".split(), first_constitution_of_place),
    ("when did % get its first constitution".split(), first_constitution_of_place),



    (["bye"], bye_action),
]


def search_pa_list(src: List[str]) -> List[str]:
    """Takes source, finds matching pattern and calls corresponding action. If it finds
    a match but has no answers it returns ["No answers"]. If it finds no match it
    returns ["I don't understand"].

    Args:
        source - a phrase represented as a list of words (strings)

    Returns:
        a list of answers. Will be ["I don't understand"] if it finds no matches and
        ["No answers"] if it finds a match but no answers
    """
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            answer = act(mat)
            return answer if answer else ["No answers"]

    return ["I don't understand"]


def query_loop() -> None:
    """The simple query loop. The try/except structure is to catch Ctrl-C or Ctrl-D
    characters and exit gracefully"""
    print("Welcome to the wikipedia chatbot!\n")
    while True:
        try:
            print()
            query = input("Your query? ").replace("?", "").lower().split()
            answers = search_pa_list(query)
            for ans in answers:
                print(ans)

        except (KeyboardInterrupt, EOFError):
            break

    print("\nSo long!\n")


# uncomment the next line once you've implemented everything are ready to try it out
query_loop()
