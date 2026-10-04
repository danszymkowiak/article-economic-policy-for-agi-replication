You are extracting evidence from encyclopedia article text. Read ONLY the file(s) listed below; do not read or search any other file or directory.

Task: copy out, word for word, every passage that reports empirical evidence about the policy the article describes. Evidence means: results of studies, pilots, experiments and trials; measured effects; programme outcomes; statistics and figures; and criticisms that cite data or observed outcomes.

Do not copy: definitions, history and origins, philosophy or ethical argument, proposals and advocacy, theory with no data, opinions with no cited evidence, or navigation text.

Rules:
- Each passage must be an exact, contiguous copy from the article text: no rewording, no shortening, no ellipses, no merging of separate passages, no changes to spacing or punctuation.
- A passage is one or more whole sentences. Keep each passage self-contained enough to be read alone, but do not add words.
- Record, for each passage, the section heading it falls under (copied exactly from the article text; use the article title for the opening section).
- Include every qualifying passage, in article order. Do not judge which evidence is stronger, and do not leave out evidence that points in either direction.
- If there is no qualifying text, return an empty list.

Output: write a JSON file to the path given below, containing exactly {"spans": [{"heading": "...", "text": "..."}, ...]}. Then reply with only the number of spans written.
