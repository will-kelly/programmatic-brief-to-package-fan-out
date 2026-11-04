"""Read an answer the way a brand tracker would: who's mentioned, in what
order, who gets recommended, and whose URLs get cited."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from .common import load_toml

URL_RE = re.compile(r"https?://[^\s)\]>\"'`]+")


PLACEHOLDER_HOST = re.compile(
    r"^(localhost|127\.|0\.0\.0\.0|10\.|192\.168\.)|example\.(com|org|net)$|\.(internal|local|test|example)$"
    r"|[<>{}]|^your-|^my-|googleapis\.com$|amazonaws\.com$")


def is_placeholder(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return not host or "." not in host or bool(PLACEHOLDER_HOST.search(host))


class Brands:
    def __init__(self, cfg: dict | None = None):
        cfg = cfg or load_toml("brands.toml")
        self.us = cfg["us"]["name"]
        self.entries = [cfg["us"]] + cfg.get("competitor", [])
        self._pats = []
        for e in self.entries:
            alias = "|".join(re.escape(a) for a in sorted(e["aliases"], key=len, reverse=True))
            # Brand names are proper nouns: require the capital for short
            # dictionary words like Render, Fly, Modal, Neon.
            pat = re.compile(rf"(?<![\w.-])(?:{alias})(?![\w-])")
            excl = [re.compile(x, re.I) for x in e.get("exclude", [])]
            self._pats.append((e["name"], pat, excl, e.get("domains", [])))

    def mentions(self, text: str) -> list[dict]:
        """Brands in order of first mention, verb senses excluded."""
        found = []
        masked = text
        for name, pat, excl, _ in self._pats:
            for x in excl:
                masked = x.sub(lambda m: " " * len(m.group(0)), masked)
        for name, pat, _, _ in self._pats:
            m = pat.search(masked)
            if m:
                found.append({"brand": name, "pos": m.start(),
                              "count": len(pat.findall(masked))})
        # A URL on a brand's domain is a mention even when the alias is
        # glued to a subdomain (myapp.onrender.com).
        named = {f["brand"] for f in found}
        for m in URL_RE.finditer(text):
            o = self.owner(m.group(0))
            if not o.startswith("third-party:") and o not in named:
                found.append({"brand": o, "pos": m.start(), "count": 1}); named.add(o)
        found.sort(key=lambda d: d["pos"])
        for i, f in enumerate(found, 1):
            f["rank"] = i
        return found

    def owner(self, url: str) -> str:
        host = (urlparse(url).hostname or "").lower()
        for name, _, _, domains in self._pats:
            if any(host == d or host.endswith("." + d) for d in domains):
                return name
        return "third-party:" + host.removeprefix("www.")

    def citations(self, text: str, extra_urls=()) -> list[dict]:
        """URLs offered as sources. Code samples are full of URLs that
        aren't sources (localhost, example.com, internal hostnames, API
        endpoints, template placeholders), so code is stripped first and
        those hosts are dropped."""
        prose = re.sub(r"```.*?```", " ", text, flags=re.S)
        prose = re.sub(r"`[^`\n]*`", " ", prose)
        urls = [u.rstrip(".,;:") for u in URL_RE.findall(prose)] + list(extra_urls)
        out = []
        for u in dict.fromkeys(urls):
            if is_placeholder(u):
                continue
            out.append({"url": u, "owner": self.owner(u)})
        return out

    def first_recommendation(self, text: str) -> str | None:
        """The brand named first in the answer's recommendation, if there is
        one. Heuristic: the first brand mentioned in a line that reads as a
        pick ('use', 'go with', 'I'd pick', 'best', 'default', 'recommend')."""
        pick = re.compile(r"\b(use|go with|i'?d (pick|choose|use|go)|best|default|recommend|top pick|easiest|winner)\b", re.I)
        for line in text.splitlines():
            if pick.search(line):
                ms = self.mentions(line)
                if ms:
                    return ms[0]["brand"]
        ms = self.mentions(text)
        return ms[0]["brand"] if ms else None
