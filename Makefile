#!/usr/bin/make -f

adocs = $(wildcard doc/*.adoc)
htmls = $(adocs:.adoc=.html)
pdfs  = $(adocs:.adoc=.pdf)
pys   = $(shell find kolaborator -name '*.py')

all: doc
doc: html

html: ${htmls}
pdf: ${pdfs}

pep:
	@pep8 --show-source --ignore=E221,E712 ${pys}

clean:
	rm -f doc/*.html doc/*.png doc/*.cache

%.html: %.adoc
	asciidoctor -r asciidoctor-diagram -b html5 -o $@ $<

%.pdf: %.adoc
	asciidoctor-pdf -r asciidoctor-diagram -o $@ $<


# EOF
