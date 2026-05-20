import re

with open('scratch/acn_nis.html', 'r') as f:
    html = f.read()

nav_matches = list(re.finditer(r'<nav[^>]*aria-label="(Menu principale|Collegamenti Veloci)"[^>]*>.*?</nav>', html, re.DOTALL | re.IGNORECASE))
print(f"Trovati {len(nav_matches)} nav")
for m in nav_matches:
    print("Match length:", len(m.group(0)))
    print("Contains Relazioni Internazionali:", "Relazioni Internazionali" in m.group(0))
