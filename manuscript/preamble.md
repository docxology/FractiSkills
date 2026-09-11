# LaTeX Preamble

This file contains LaTeX packages and commands that are automatically injected into the document compilation process.

```latex
% Core mathematics
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{mathtools}

% Compact page geometry
\usepackage{geometry}
\geometry{margin=0.7in, top=0.75in, bottom=0.75in}
\usepackage{float}
\usepackage{graphicx}

% Tables
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}

% Typography and formatting
\usepackage{microtype}
\usepackage{xcolor}

% Cross-references, citations, and hyperlinks: all hyperlink ink is red
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=red,
    urlcolor=red,
    citecolor=red,
    filecolor=red,
}
\usepackage[capitalise,noabbrev]{cleveref}
\usepackage{natbib}

% Tighter list spacing for structured section outlines
\usepackage{enumitem}
\setlist{nosep, leftmargin=1.4em}
```
