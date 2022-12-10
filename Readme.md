This repository provides code to 

- retrieve named entities (provided as a JSON) from structured text (provided as JSON)
- retrieve the number of times they were mentioned 
   - overall
   - related to the artificial intelligence act
   - related to artificial intelligence
 - retrieve the most common terms in paragraphs not mentioning either the AI act or AI
 - visualize the results (statically and interactively)


Entity retrieval is completed using `python`'s `spaCy` library; visualization using `R`'s `ggplot2`.
