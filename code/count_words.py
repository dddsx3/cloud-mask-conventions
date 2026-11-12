"""Word counts for the P8 manuscript.

Definitions (stated once, used everywhere):
  abstract  = text between \begin{abstract} and \end{abstract}
  body      = \section ... \section{Conclusions} end  (i.e. Sections 1-5),
              including table/figure captions, excluding the abstract,
              keywords, and everything from \section{Conclusions} onward.
  Numbers inside math ($...$) count as one token each.
"""
import re
import sys

TEX = r"<WORKROOT>\papers\p8_cloud_mask\manuscript.tex"
RAW = open(TEX, encoding="utf-8-sig").read()


def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)


def clean(s):
    s = strip_comments(s)
    s = re.sub(r"\\begin\{(table|table\*|figure|figure\*)\}.*?\\end\{\1\}", " ", s,
               flags=re.S)          # captions re-added separately below
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", s)
    s = s.replace("~", " ").replace("{", " ").replace("}", " ")
    s = s.replace("\\", " ")
    s = re.sub(r"\$[^$]*\$", " NUM ", s)
    return s


def words(s):
    return [w for w in re.split(r"\s+", clean(s)) if re.search(r"[A-Za-z0-9]", w)]


def captions(s):
    out = []
    for m in re.finditer(r"\\caption\{(.+?)\}\s*\n", s, flags=re.S):
        out.append(m.group(1))
    return " ".join(out)


abs_m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", RAW, flags=re.S)
abstract = words(abs_m.group(1))

i0 = RAW.find(r"\section{Introduction}")
i1 = RAW.find(r"\section{Conclusions}")
body_tex = RAW[i0:i1]
body = words(body_tex + " " + captions(body_tex))

# title
t_m = re.search(r"\\title\{(.*?)\}\s*\n\s*\n", RAW, flags=re.S)
title = words(t_m.group(1)) if t_m else []

print("abstract_words      ", len(abstract))
print("body_words_S1_S5    ", len(body))
print("title_words         ", len(title))
print("abstract_chars      ", len(re.sub(r"\s+", " ", clean(abs_m.group(1))).strip()))
sys.exit(0)
