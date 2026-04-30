import re
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


class RaceAnalyzer:
    """Analyze race URLs to extract course information for personalized training."""

    COMMON_RACES = {
        "utmb": {
            "name": "UTMB",
            "url_patterns": ["utmbmontblanc.com", "utmb.co"],
            "default_distance_km": 171,
            "elevation_gain_m": 10000,
            "difficulty": "extreme",
        },
        "western states": {
            "name": "Western States 100",
            "url_patterns": ["ws100.com", "westernstates.org"],
            "default_distance_km": 161,
            "elevation_gain_m": 5500,
            "difficulty": "hard",
        },
        "hardrock": {
            "name": "Hardrock 100",
            "url_patterns": ["hardrock100.com"],
            "default_distance_km": 161,
            "elevation_gain_m": 10000,
            "difficulty": "extreme",
        },
        "leadville": {
            "name": "Leadville 100",
            "url_patterns": ["leadvilletr100.com"],
            "default_distance_km": 161,
            "elevation_gain_m": 3000,
            "difficulty": "hard",
        },
        "boston": {
            "name": "Boston Marathon",
            "url_patterns": ["baa.org", "bostonmarathon"],
            "default_distance_km": 42.2,
            "elevation_gain_m": 300,
            "difficulty": "medium",
        },
        "new york": {
            "name": "NYC Marathon",
            "url_patterns": ["nycmarathon.org", "nyrr.org"],
            "default_distance_km": 42.2,
            "elevation_gain_m": 150,
            "difficulty": "medium",
        },
        "chicago": {
            "name": "Chicago Marathon",
            "url_patterns": ["chicagomarathon.com"],
            "default_distance_km": 42.2,
            "elevation_gain_m": 0,
            "difficulty": "easy",
        },
    }

    async def analyze_url(self, url: str) -> dict:
        """Fetch and analyze a race webpage."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                return self._parse_html(response.text, url)
        except Exception as e:
            return self._extract_from_url_path(url)

    def _parse_html(self, html: str, url: str) -> dict:
        """Parse HTML to extract race information."""
        soup = BeautifulSoup(html, "html.parser")

        result = {
            "race_name": "",
            "race_date": None,
            "distance_km": None,
            "elevation_gain_m": None,
            "location": "",
            "difficulty": "medium",
            "course_type": "point-to-point",
            "source_url": url,
        }

        title = soup.find("title")
        if title:
            result["race_name"] = title.text.strip()

        meta_tags = soup.find_all("meta")
        for tag in meta_tags:
            name = tag.get("name", "")
            content = tag.get("content", "")

            if "description" in name.lower():
                result["race_name"] = content[:100]

        h1_tags = soup.find_all("h1")
        for h1 in h1_tags:
            text = h1.text.strip()
            if len(text) > 3 and len(text) < 100:
                result["race_name"] = text
                break

        page_text = soup.get_text()

        date_patterns = [
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
            r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
            r"\d{4}-\d{2}-\d{2}",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                try:
                    result["race_date"] = self._parse_date(match.group())
                except:
                    pass

        distance_patterns = [
            r"(\d+)\s*(?:km|kilometers?)",
            r"(\d+(?:\.\d+)?)\s*miles*",
            r"(100|50|50K|100K|50M|100M)\s*miles*",
        ]

        for pattern in distance_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                distance = match.group(1)
                if "mile" in match.group(0).lower():
                    miles = float(distance.replace("M", ""))
                    result["distance_km"] = round(miles * 1.60934, 1)
                elif distance.isdigit():
                    if int(distance) >= 100:
                        result["distance_km"] = int(distance)
                    else:
                        result["distance_km"] = float(distance)
                break

        elevation_patterns = [
            r"(\d+(?:,\d{3})*)\s*(?:ft|feet)\s*(?:elevation|climb|gain)",
            r"(\d+(?:,\d{3})*)\s*(?:m|meters?)\s*(?:elevation|climb|gain)",
            r"elevation\s*(?:gain|change)?\s*:?\s*(\d+(?:,\d{3})*)",
        ]

        for pattern in elevation_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                elev = match.group(1).replace(",", "")
                result["elevation_gain_m"] = int(elev)
                break

        parsed_url = urlparse(url)
        url_lower = (parsed_url.netloc + parsed_url.path).lower()

        for race_key, race_info in self.COMMON_RACES.items():
            if any(p in url_lower for p in race_info["url_patterns"]):
                result["race_name"] = race_info["name"]
                if not result["distance_km"]:
                    result["distance_km"] = race_info["default_distance_km"]
                if not result["elevation_gain_m"]:
                    result["elevation_gain_m"] = race_info["elevation_gain_m"]
                result["difficulty"] = race_info["difficulty"]
                break

        return result

    def _extract_from_url_path(self, url: str) -> dict:
        """Extract race info from URL when HTML parsing fails."""
        parsed_url = urlparse(url)
        url_lower = (parsed_url.netloc + parsed_url.path).lower()

        result = {
            "race_name": "",
            "race_date": None,
            "distance_km": 50,
            "elevation_gain_m": None,
            "location": "",
            "difficulty": "medium",
            "course_type": "unknown",
            "source_url": url,
        }

        for race_key, race_info in self.COMMON_RACES.items():
            if any(p in url_lower for p in race_info["url_patterns"]):
                result["race_name"] = race_info["name"]
                result["distance_km"] = race_info["default_distance_km"]
                result["elevation_gain_m"] = race_info["elevation_gain_m"]
                result["difficulty"] = race_info["difficulty"]
                break

        path_parts = parsed_url.path.split("/")
        for part in path_parts:
            if "50k" in part.lower() or "50k" in part.lower():
                result["distance_km"] = 50
            elif "100k" in part.lower():
                result["distance_km"] = 100
            elif "100" in part.lower() and "mile" in part.lower():
                result["distance_km"] = 161
            elif "marathon" in part.lower():
                result["distance_km"] = 42.2
            elif "half" in part.lower():
                result["distance_km"] = 21.1

        return result

    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats."""
        date_str = date_str.strip()

        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        for month_name, month_num in months.items():
            if month_name in date_str.lower():
                parts = re.findall(r"\d+", date_str)
                if len(parts) >= 2:
                    day = int(parts[0])
                    year = int(parts[1])
                    return datetime(year, month_num, day)
                elif len(parts) == 1:
                    year = int(parts[0])
                    return datetime(year, month_num, 1)

        try:
            return datetime.fromisoformat(date_str[:10])
        except:
            pass

        return datetime(2026, 6, 1)

    def get_training_advice(self, race_info: dict) -> dict:
        """Generate training advice based on race characteristics."""
        distance = race_info.get("distance_km", 50)
        elevation = race_info.get("elevation_gain_m", 0)
        difficulty = race_info.get("difficulty", "medium")

        advice = {
            "weekly_long_run_max_km": 35,
            "weekly_volume_cap_km": 100,
            "back_to_back_weeks": 2,
            "taper_weeks": 2,
            "key_workouts": [],
        }

        if distance >= 100:
            advice["weekly_long_run_max_km"] = 45
            advice["weekly_volume_cap_km"] = 140
            advice["back_to_back_weeks"] = 3
            advice["taper_weeks"] = 3
            advice["key_workouts"] = [
                "Long run with elevation (4-6 hours)",
                "Back-to-back long runs",
                "Hill repeats",
                "Night runs (for headlamp training)",
            ]
        elif distance >= 50:
            advice["weekly_long_run_max_km"] = 32
            advice["weekly_volume_cap_km"] = 100
            advice["key_workouts"] = [
                "Long run (3-4 hours)",
                "Tempo runs",
                "Hill repeats",
                "Recovery runs",
            ]
        else:
            advice["weekly_long_run_max_km"] = 25
            advice["weekly_volume_cap_km"] = 70
            advice["key_workouts"] = [
                "Long run (2-3 hours)",
                "Tempo run",
                "Interval training",
                "Easy recovery runs",
            ]

        if elevation > 5000:
            advice["key_workouts"].append("Vertical training/hill repeats")
            advice["weekly_volume_cap_km"] *= 0.8

        if difficulty == "extreme":
            advice["weekly_volume_cap_km"] *= 0.75
            advice["key_workouts"].append("Mental resilience training")

        return advice
