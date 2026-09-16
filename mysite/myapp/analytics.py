import ipaddress
import json
import logging
import urllib.error
import urllib.request
from django.core.cache import cache
from .models import AnalyticsEvent

logger = logging.getLogger(__name__)

# ISO 3166-1 alpha-2 country codes mapped to standard English country names
ISO_COUNTRY_MAP = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AD": "Andorra", "AO": "Angola",
    "AG": "Antigua and Barbuda", "AR": "Argentina", "AM": "Armenia", "AU": "Australia", "AT": "Austria",
    "AZ": "Azerbaijan", "BS": "Bahamas", "BH": "Bahrain", "BD": "Bangladesh", "BB": "Barbados",
    "BY": "Belarus", "BE": "Belgium", "BZ": "Belize", "BJ": "Benin", "BT": "Bhutan",
    "BO": "Bolivia", "BA": "Bosnia and Herzegovina", "BW": "Botswana", "BR": "Brazil", "BN": "Brunei",
    "BG": "Bulgaria", "BF": "Burkina Faso", "BI": "Burundi", "CV": "Cabo Verde", "KH": "Cambodia",
    "CM": "Cameroon", "CA": "Canada", "CF": "Central African Republic", "TD": "Chad", "CL": "Chile",
    "CN": "China", "CO": "Colombia", "KM": "Comoros", "CG": "Congo", "CD": "Congo (DRC)",
    "CR": "Costa Rica", "CI": "Cote d'Ivoire", "HR": "Croatia", "CU": "Cuba", "CY": "Cyprus",
    "CZ": "Czech Republic", "DK": "Denmark", "DJ": "Djibouti", "DM": "Dominica", "DO": "Dominican Republic",
    "EC": "Ecuador", "EG": "Egypt", "SV": "El Salvador", "GQ": "Equatorial Guinea", "ER": "Eritrea",
    "EE": "Estonia", "SZ": "Eswatini", "ET": "Ethiopia", "FJ": "Fiji", "FI": "Finland",
    "FR": "France", "GA": "Gabon", "GM": "Gambia", "GE": "Georgia", "DE": "Germany",
    "GH": "Ghana", "GR": "Greece", "GD": "Grenada", "GT": "Guatemala", "GN": "Guinea",
    "GW": "Guinea-Bissau", "GY": "Guyana", "HT": "Haiti", "HN": "Honduras", "HU": "Hungary",
    "IS": "Iceland", "IN": "India", "ID": "Indonesia", "IR": "Iran", "IQ": "Iraq",
    "IE": "Ireland", "IL": "Israel", "IT": "Italy", "JM": "Jamaica", "JP": "Japan",
    "JO": "Jordan", "KZ": "Kazakhstan", "KE": "Kenya", "KI": "Kiribati", "KR": "South Korea",
    "KP": "North Korea", "KW": "Kuwait", "KG": "Kyrgyzstan", "LA": "Laos", "LV": "Latvia",
    "LB": "Lebanon", "LS": "Lesotho", "LR": "Liberia", "LY": "Libya", "LI": "Liechtenstein",
    "LT": "Lithuania", "LU": "Luxembourg", "MG": "Madagascar", "MW": "Malawi", "MY": "Malaysia",
    "MV": "Maldives", "ML": "Mali", "MT": "Malta", "MH": "Marshall Islands", "MR": "Mauritania",
    "MU": "Mauritius", "MX": "Mexico", "FM": "Micronesia", "MD": "Moldova", "MC": "Monaco",
    "MN": "Mongolia", "ME": "Montenegro", "MA": "Morocco", "MZ": "Mozambique", "MM": "Myanmar",
    "NA": "Namibia", "NR": "Nauru", "NP": "Nepal", "NL": "Netherlands", "NZ": "New Zealand",
    "NI": "Nicaragua", "NE": "Niger", "NG": "Nigeria", "MK": "North Macedonia", "NO": "Norway",
    "OM": "Oman", "PK": "Pakistan", "PW": "Palau", "PA": "Panama", "PG": "Papua New Guinea",
    "PY": "Paraguay", "PE": "Peru", "PH": "Philippines", "PL": "Poland", "PT": "Portugal",
    "QA": "Qatar", "RO": "Romania", "RU": "Russia", "RW": "Rwanda", "KN": "Saint Kitts and Nevis",
    "LC": "Saint Lucia", "VC": "Saint Vincent and the Grenadines", "WS": "Samoa", "SM": "San Marino",
    "ST": "Sao Tome and Principe", "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia",
    "SC": "Seychelles", "SL": "Sierra Leone", "SG": "Singapore", "SK": "Slovakia", "SI": "Slovenia",
    "SB": "Solomon Islands", "SO": "Somalia", "ZA": "South Africa", "SS": "South Sudan",
    "ES": "Spain", "LK": "Sri Lanka", "SD": "Sudan", "SR": "Suriname", "SE": "Sweden",
    "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan", "TJ": "Tajikistan", "TZ": "Tanzania",
    "TH": "Thailand", "TL": "Timor-Leste", "TG": "Togo", "TO": "Tonga", "TT": "Trinidad and Tobago",
    "TN": "Tunisia", "TR": "Turkey", "TM": "Turkmenistan", "TV": "Tuvalu", "UG": "Uganda",
    "UA": "Ukraine", "AE": "United Arab Emirates", "GB": "United Kingdom", "US": "United States",
    "UY": "Uruguay", "UZ": "Uzbekistan", "VU": "Vanuatu", "VA": "Vatican City", "VE": "Venezuela",
    "VN": "Vietnam", "YE": "Yemen", "ZM": "Zambia", "ZW": "Zimbabwe",
    "HK": "Hong Kong", "PR": "Puerto Rico", "PS": "Palestine"
}


def get_client_ip(request):
    """
    Extracts the client's real IP address from request headers or REMOTE_ADDR.
    Handles proxies such as Cloudflare, Render, and Nginx.
    """
    # Cloudflare
    cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
    if cf_ip:
        return cf_ip.strip()

    # Standard proxy forwarded header: "client_ip, proxy1, proxy2"
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    # Nginx / other reverse proxies
    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        return x_real_ip.strip()

    return request.META.get("REMOTE_ADDR", "").strip()


def is_private_ip(ip_str):
    """Checks if an IP string is private, loopback, or invalid."""
    if not ip_str:
        return True
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except ValueError:
        return True


def get_country_from_ip(ip):
    """
    Performs IP-to-Country geolocation with caching.
    Uses free, fast APIs with short timeouts to avoid blocking request pipelines.
    """
    if not ip or is_private_ip(ip):
        return ""

    cache_key = f"geo_country_{ip}"
    cached_country = cache.get(cache_key)
    if cached_country is not None:
        return cached_country

    country_name = ""

    # Primary: ip-api.com (free, high speed, returns country name & code)
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode"
        req = urllib.request.Request(url, headers={"User-Agent": "ScholarHub/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "success":
                    country_name = data.get("country") or ISO_COUNTRY_MAP.get(data.get("countryCode", "").upper(), "")
    except Exception as e:
        logger.debug("ip-api lookup failed for %s: %s", ip, e)

    # Secondary fallback: api.country.is
    if not country_name:
        try:
            url = f"https://api.country.is/{ip}"
            req = urllib.request.Request(url, headers={"User-Agent": "ScholarHub/1.0"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    code = data.get("country", "").upper()
                    country_name = ISO_COUNTRY_MAP.get(code, code)
        except Exception as e:
            logger.debug("api.country.is lookup failed for %s: %s", ip, e)

    timeout = 60 * 60 * 24 * 7 if country_name else 60 * 60
    cache.set(cache_key, country_name, timeout=timeout)
    return country_name


def get_visitor_country(request):
    """
    Determines the visitor's country using:
    1. Session cache (0 ms on subsequent hits within the same session)
    2. Test/Override header (HTTP_X_TEST_COUNTRY)
    3. Cloudflare/Proxy Country header (HTTP_CF_IPCOUNTRY, HTTP_X_COUNTRY_CODE)
    4. Client IP Geolocation via cached lookup
    5. Fallback for Local/Development vs Unknown
    """
    # 1. Check session cache
    if request.session.get("visitor_country"):
        return request.session["visitor_country"]

    # 2. Test / Dev override header
    test_country = request.META.get("HTTP_X_TEST_COUNTRY")
    if test_country:
        country = test_country.strip()
        request.session["visitor_country"] = country
        return country

    # 3. Cloudflare / Proxy Country header (e.g. "NG", "US", "GB")
    cf_country = request.META.get("HTTP_CF_IPCOUNTRY") or request.META.get("HTTP_X_COUNTRY_CODE") or request.META.get("HTTP_X_COUNTRY")
    if cf_country:
        cf_code = cf_country.strip().upper()
        if cf_code not in ("XX", "T1", ""):
            country = ISO_COUNTRY_MAP.get(cf_code, cf_code)
            request.session["visitor_country"] = country
            return country

    # 4. IP Geolocation
    client_ip = get_client_ip(request)
    country = get_country_from_ip(client_ip)

    if not country:
        if is_private_ip(client_ip):
            country = "Local / Development"
        else:
            country = "Unknown"

    request.session["visitor_country"] = country
    return country


def log_event(request, event_type, scholarship=None, page_path="", search_summary="", result_count=None):
    """
    Records one AnalyticsEvent row. Called from views right where the tracked
    action happens (a page load, a scholarship view, a click, a filter/search).

    Uses the visitor's session key (not their IP address) as a stand-in for
    "one visitor" and resolves country for geographic traffic insights.
    """
    if not request.session.session_key:
        # A brand-new visitor with no session yet -- force Django to create
        # one now so we have something to count them by.
        request.session.save()

    country = get_visitor_country(request)

    AnalyticsEvent.objects.create(
        event_type=event_type,
        scholarship=scholarship,
        page_path=page_path[:255],
        search_summary=search_summary[:255],
        result_count=result_count,
        utm_source=request.GET.get("utm_source", "")[:100],
        referrer=request.META.get("HTTP_REFERER", "")[:300],
        session_key=request.session.session_key or "",
        country=country[:100],
    )
